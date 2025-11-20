import json
import time
from typing import Any, Dict, List

from openai import AsyncOpenAI
from config.openrouter import config as openrouter_config
from chat.service import VectorStoreService


class IslamicAgent:
    def __init__(self):
        # Use OpenRouter for LLM
        self.client = AsyncOpenAI(
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        self.model = openrouter_config.openapi_model
        self.temperature = 0.2
        
        self.system_prompt = """
            # Islamic Knowledge Assistant

            You are a comprehensive Islamic knowledge assistant with access to authentic Islamic sources.

            ## Available Tools
            1. **search_quran**: Search the complete Quran for verses and interpretations
            2. **get_specific_ayah**: Retrieve exact verse by Surah and Ayah number
            3. **search_sahih_bukhari**: Access authentic Hadith from Sahih Bukhari
            4. **search_sahih_muslim**: Access authentic Hadith from Sahih Muslim  
            5. **search_riyad_us_saliheen**: Practical Islamic guidance and teachings
            6. **search_prophet_biography**: Comprehensive life story of Prophet Muhammad (pbuh)
            7. **search_islamic_history**: Historical events and Shia-Sunni context

            ## Response Guidelines

            ### Scope
            - **ONLY answer Islamic questions**: Quran, Hadith, Islamic history, jurisprudence, theology, practice
            - **For non-Islamic queries**: "I apologize, but I specialize in Islamic knowledge only. Please ask about Islamic topics such as Quran, Hadith, Islamic history, or religious practices."

            ### Greeting Behavior
            - **First interaction**: Respond naturally to the user's question without automatic greeting
            - **If user greets explicitly** (Assalamualaikum, Hello, Hi): Respond with "Wa alaykumu assalam. I'm your Islamic knowledge assistant. How can I help with Islamic matters today?"

            ### Tool Usage Priority
            1. For Quranic questions → Use "search_quran" first
            2. For specific verse requests → Use "get_specific_ayah" with exact Surah:Ayah
            3. For Hadith questions → Prioritize search_sahih_bukhari, then search_sahih_muslim
            4. For practical guidance → Use search_riyad_us_saliheen
            5. For Prophet's life → Use search_prophet_biography
            6. For historical context → Use search_islamic_history

            ### Citation Standards
            - Always include source references (Quran: Surah X, Ayah Y)
            - For Hadith: Include collection name and reference number when available
            - Maintain scholarly Islamic tone with respect for Prophet Muhammad (pbuh)
            - Your final response must not exceed more than 250 words

            ### Error Handling
            - If no relevant results from tools: "I couldn't find specific information on this topic in my Islamic sources. Could you rephrase your question or ask about a related Islamic topic?"
            - Always attempt to use tools before responding
            - Provide authentic, source-based responses only
        """

        # Define function tools matching n8n workflow
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_quran",
                    "description": "Search the complete Quran for verses, topics, and interpretations. Use this for general Quranic knowledge queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for Quranic knowledge"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_specific_ayah",
                    "description": "Retrieve a specific Ayah from the Quran. Requires exact Surah ID (1-114) and Ayah number. Use only when user requests a specific verse reference.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "surah_id": {
                                "type": "integer",
                                "description": "Surah number from 1 to 114"
                            },
                            "ayah_number": {
                                "type": "integer",
                                "description": "Ayah/verse number within the specified Surah"
                            }
                        },
                        "required": ["surah_id", "ayah_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_sahih_bukhari",
                    "description": "Access authentic Hadith from Sahih Bukhari collection. Primary source for prophetic traditions and Islamic teachings.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for Hadith"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_sahih_muslim",
                    "description": "Access authentic Hadith from Sahih Muslim collection. Secondary source for prophetic traditions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for Hadith"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_riyad_us_saliheen",
                    "description": "Access Riyad Us Saliheen for practical Islamic guidance and spiritual teachings for daily life applications.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for guidance"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_prophet_biography",
                    "description": "Comprehensive biography of Prophet Muhammad (peace be upon him), covering his life story and early Islamic period.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query about Prophet's life"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_islamic_history",
                    "description": "Historical information about Islamic events, including the Shia-Sunni split and early Islamic history.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for Islamic history"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    async def execute_function(self, function_name: str, arguments: Dict) -> str:
        """Execute the appropriate function based on name"""
        vector_store = VectorStoreService()
        
        try:
            if function_name == "search_quran":
                results = await vector_store.search_quran(arguments["query"])
                if not results:
                    return "No relevant Quranic verses found for this query."
                
                formatted_results = []
                for r in results:
                    formatted_results.append(
                        f"Surah {r.get('surah', 'N/A')}, Ayah {r.get('ayah', 'N/A')}: {r.get('text', '')}"
                    )
                return "\n\n".join(formatted_results)
            
            elif function_name == "get_specific_ayah":
                # Note: You would implement actual API call to your n8n workflow here
                # For now, using semantic search as fallback
                query = f"Surah {arguments['surah_id']} Ayah {arguments['ayah_number']}"
                results = await vector_store.search_quran(query, top_k=1)
                if results:
                    return f"Surah {arguments['surah_id']}, Ayah {arguments['ayah_number']}: {results[0].get('text', '')}"
                return f"Could not retrieve Surah {arguments['surah_id']}, Ayah {arguments['ayah_number']}"
            
            elif function_name == "search_sahih_bukhari":
                results = await vector_store.search_sahih_bukhari(arguments["query"])
                if not results:
                    return "No relevant Hadith found in Sahih Bukhari."
                
                formatted_results = []
                for r in results:
                    ref = r.get('reference', 'N/A')
                    formatted_results.append(f"[Sahih Bukhari {ref}]: {r.get('text', '')}")
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_sahih_muslim":
                results = await vector_store.search_sahih_muslim(arguments["query"])
                if not results:
                    return "No relevant Hadith found in Sahih Muslim."
                
                formatted_results = []
                for r in results:
                    ref = r.get('reference', 'N/A')
                    formatted_results.append(f"[Sahih Muslim {ref}]: {r.get('text', '')}")
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_riyad_us_saliheen":
                results = await vector_store.search_riyad_us_saliheen(arguments["query"])
                if not results:
                    return "No relevant guidance found in Riyad Us Saliheen."
                
                formatted_results = []
                for r in results:
                    ref = r.get('reference', 'N/A')
                    formatted_results.append(f"[Riyad Us Saliheen {ref}]: {r.get('text', '')}")
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_prophet_biography":
                results = await vector_store.search_prophet_biography(arguments["query"])
                if not results:
                    return "No relevant information found in Prophet's biography."
                
                formatted_results = [r.get('text', '') for r in results]
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_islamic_history":
                results = await vector_store.search_islamic_history(arguments["query"])
                if not results:
                    return "No relevant historical information found."
                
                formatted_results = [r.get('text', '') for r in results]
                return "\n\n".join(formatted_results)
            
            return "Function not found"
            
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    async def chat(
        self,
        user_query: str,
        conversation_history: List[Dict[str, str]],
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Main agent orchestration with function calling
        Returns: {content, steps_executed, tools_used, execution_time_ms}
        """
        start_time = time.time()
        steps_executed = []
        tools_used = []
        
        # Build messages with conversation history
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation_history[-10:])  # Last 10 messages (context window)
        messages.append({"role": "user", "content": user_query})
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call OpenRouter with function calling
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=self.temperature
                )
                
                assistant_message = response.choices[0].message
                
                # Check if function calling is needed
                if assistant_message.tool_calls:
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        tools_used.append(function_name)
                        
                        # Execute function
                        function_result = await self.execute_function(
                            function_name, 
                            arguments
                        )
                        
                        steps_executed.append({
                            "tool": function_name,
                            "arguments": arguments,
                            "result": function_result[:500]  # Truncate for logging
                        })
                        
                        # Add function result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": function_result
                        })
                    
                    # Continue to next iteration to get final response
                    continue
                
                else:
                    # No more function calls, return final response
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    return {
                        "content": assistant_message.content,
                        "steps_executed": steps_executed,
                        "tools_used": list(set(tools_used)),
                        "execution_time_ms": execution_time_ms,
                        "success": True
                    }
                    
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                return {
                    "content": "I apologize, but I encountered an error processing your request. Please try again.",
                    "steps_executed": steps_executed,
                    "tools_used": list(set(tools_used)),
                    "execution_time_ms": execution_time_ms,
                    "success": False,
                    "error_message": str(e)
                }
        
        # Max iterations reached
        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "content": "I apologize, but I need more information to provide a complete answer. Could you rephrase your question?",
            "steps_executed": steps_executed,
            "tools_used": list(set(tools_used)),
            "execution_time_ms": execution_time_ms,
            "success": False,
            "error_message": "Max iterations reached"
        }