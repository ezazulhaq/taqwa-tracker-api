import json
import time
import asyncio
from typing import Any, Dict, List
from functools import lru_cache

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
        
        # Cache for vector store service (singleton pattern)
        self._vector_store = None
        
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

            ### CRITICAL: Use ONLY ONE tool per query unless absolutely necessary
            - Most queries can be answered with a single tool call
            - Only use multiple tools if the query explicitly requires different sources
            - Prefer broader searches over multiple narrow ones

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
    
    @property
    def vector_store(self):
        """Lazy load and cache vector store service"""
        if self._vector_store is None:
            self._vector_store = VectorStoreService()
        return self._vector_store
    
    async def execute_function(self, function_name: str, arguments: Dict) -> str:
        """Execute the appropriate function based on name"""
        try:
            if function_name == "search_quran":
                results = await self.vector_store.search_quran(arguments["query"], top_k=3)
                if not results:
                    return "No relevant Quranic verses found for this query."
                
                formatted_results = []
                for r in results:
                    formatted_results.append(
                        f"Surah {r.get('surah', 'N/A')}, Ayah {r.get('ayah', 'N/A')}: {r.get('text', '')}"
                    )
                return "\n\n".join(formatted_results)
            
            elif function_name == "get_specific_ayah":
                query = f"Surah {arguments['surah_id']} Ayah {arguments['ayah_number']}"
                results = await self.vector_store.search_quran(query, top_k=1)
                if results:
                    return f"Surah {arguments['surah_id']}, Ayah {arguments['ayah_number']}: {results[0].get('text', '')}"
                return f"Could not retrieve Surah {arguments['surah_id']}, Ayah {arguments['ayah_number']}"
            
            elif function_name == "search_sahih_bukhari":
                results = await self.vector_store.search_sahih_bukhari(arguments["query"], top_k=3)
                if not results:
                    return "No relevant Hadith found in Sahih Bukhari."
                
                formatted_results = []
                for r in results:
                    ref = r.get('reference', 'N/A')
                    formatted_results.append(f"[Sahih Bukhari {ref}]: {r.get('text', '')}")
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_sahih_muslim":
                results = await self.vector_store.search_sahih_muslim(arguments["query"], top_k=3)
                if not results:
                    return "No relevant Hadith found in Sahih Muslim."
                
                formatted_results = []
                for r in results:
                    ref = r.get('reference', 'N/A')
                    formatted_results.append(f"[Sahih Muslim {ref}]: {r.get('text', '')}")
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_riyad_us_saliheen":
                results = await self.vector_store.search_riyad_us_saliheen(arguments["query"], top_k=3)
                if not results:
                    return "No relevant guidance found in Riyad Us Saliheen."
                
                formatted_results = []
                for r in results:
                    ref = r.get('reference', 'N/A')
                    formatted_results.append(f"[Riyad Us Saliheen {ref}]: {r.get('text', '')}")
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_prophet_biography":
                results = await self.vector_store.search_prophet_biography(arguments["query"], top_k=3)
                if not results:
                    return "No relevant information found in Prophet's biography."
                
                formatted_results = [r.get('text', '') for r in results]
                return "\n\n".join(formatted_results)
            
            elif function_name == "search_islamic_history":
                results = await self.vector_store.search_islamic_history(arguments["query"], top_k=3)
                if not results:
                    return "No relevant historical information found."
                
                formatted_results = [r.get('text', '') for r in results]
                return "\n\n".join(formatted_results)
            
            return "Function not found"
            
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    async def execute_functions_parallel(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute multiple function calls in parallel"""
        tasks = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            task = self.execute_function(function_name, arguments)
            tasks.append({
                "task": task,
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "arguments": arguments
            })
        
        # Execute all functions in parallel
        results = await asyncio.gather(*[t["task"] for t in tasks], return_exceptions=True)
        
        # Combine results with metadata
        function_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                result_text = f"Error: {str(result)}"
            else:
                result_text = result
            
            function_results.append({
                "tool_call_id": tasks[i]["tool_call_id"],
                "function_name": tasks[i]["function_name"],
                "arguments": tasks[i]["arguments"],
                "result": result_text
            })
        
        return function_results
    
    async def chat(
        self,
        user_query: str,
        conversation_history: List[Dict[str, str]],
        max_iterations: int = 3  # Reduced from 5 to 3
    ) -> Dict[str, Any]:
        """
        Main agent orchestration with function calling
        Returns: {content, steps_executed, tools_used, execution_time_ms}
        """
        start_time = time.time()
        steps_executed = []
        tools_used = []
        
        # Build messages with conversation history (reduced to last 5 for performance)
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation_history[-5:])  # Reduced from 10 to 5
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
                    temperature=self.temperature,
                    #max_tokens=1000  # Limit response tokens for faster processing
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
                    
                    # Execute all tool calls in parallel
                    function_results = await self.execute_functions_parallel(assistant_message.tool_calls)
                    
                    # Add results to steps and tools_used
                    for fr in function_results:
                        tools_used.append(fr["function_name"])
                        steps_executed.append({
                            "tool": fr["function_name"],
                            "arguments": fr["arguments"],
                            "result": fr["result"][:500]  # Truncate for logging
                        })
                        
                        # Add function result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": fr["tool_call_id"],
                            "name": fr["function_name"],
                            "content": fr["result"]
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