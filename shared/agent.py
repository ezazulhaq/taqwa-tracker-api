import json
import logging
import os
import math
import requests
import re
import html
import asyncio

from typing import Any, Dict, List
from datetime import datetime

from dotenv import load_dotenv
from config import openrouter, pinecone, gemini
from chat.model import AgentStep, AgentTool
from geopy.geocoders import Nominatim
from hijri_converter import Hijri, Gregorian

load_dotenv()


class AgentService:
    def __init__(self):
        self.tools = {}
        self.conversation_context = []
        self.agent_steps = []
        self.register_tools()
    
    def register_tools(self):
        """Register all available tools"""
        
        # Direct Response Tool for greetings and casual conversation
        self.tools["direct_response"] = AgentTool(
            name="direct_response",
            description="Handle greetings, casual conversation, and general responses",
            parameters={
                "message": {"type": "string", "description": "User's message to respond to"}
            },
            function=self.direct_response
        )
        
        # Restrict Query Tool for non-Islamic queries
        self.tools["restrict_query"] = AgentTool(
            name="restrict_query",
            description="Restrict non-Islamic queries with appropriate message",
            parameters={
                "message": {"type": "string", "description": "User's message that was restricted"}
            },
            function=self.restrict_query
        )
        
        # Islamic Knowledge Search Tool
        self.tools["search_islamic_knowledge"] = AgentTool(
            name="search_islamic_knowledge",
            description="Search for Islamic knowledge, verses, hadith, and scholarly opinions",
            parameters={
                "query": {"type": "string", "description": "Search query for Islamic content"},
                "source_type": {"type": "string", "enum": ["quran", "hadith", "scholarly", "all"], "default": "all"}
            },
            function=self.search_islamic_knowledge
        )
        
        # Prayer Times Tool
        self.tools["get_prayer_times"] = AgentTool(
            name="get_prayer_times",
            description="Get prayer times for a specific location and date",
            parameters={
                "location": {"type": "string", "description": "City name or coordinates"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format, default is today"},
                "method": {"type": "integer", "description": "Calculation method (1-12), default is 2"}
            },
            function=self.get_prayer_times
        )
        
        # Qibla Direction Tool
        self.tools["get_qibla_direction"] = AgentTool(
            name="get_qibla_direction",
            description="Calculate Qibla direction from any location",
            parameters={
                "location": {"type": "string", "description": "City name or coordinates"}
            },
            function=self.get_qibla_direction
        )
        
        # Islamic Calendar Tool
        self.tools["convert_islamic_date"] = AgentTool(
            name="convert_islamic_date",
            description="Convert between Gregorian and Islamic (Hijri) dates",
            parameters={
                "date": {"type": "string", "description": "Date to convert"},
                "from_calendar": {"type": "string", "enum": ["gregorian", "hijri"]},
                "to_calendar": {"type": "string", "enum": ["gregorian", "hijri"]}
            },
            function=self.convert_islamic_date
        )
        
        # Halal Places Finder Tool
        self.tools["find_halal_places"] = AgentTool(
            name="find_halal_places",
            description="Find halal restaurants, mosques, or Islamic centers",
            parameters={
                "location": {"type": "string", "description": "City or area to search"},
                "place_type": {"type": "string", "enum": ["restaurant", "mosque", "islamic_center", "all"]},
                "radius": {"type": "integer", "description": "Search radius in km", "default": 10}
            },
            function=self.find_halal_places
        )
        
        # Islamic Guidance Tool
        self.tools["get_islamic_guidance"] = AgentTool(
            name="get_islamic_guidance",
            description="Get specific Islamic guidance on religious matters, ethics, and practices",
            parameters={
                "topic": {"type": "string", "description": "Topic for guidance (prayer, fasting, marriage, business, etc.)"},
                "situation": {"type": "string", "description": "Specific situation or context"},
                "madhab": {"type": "string", "description": "Islamic school of thought preference", "default": "general"}
            },
            function=self.get_islamic_guidance
        )
    
    async def plan_and_execute(self, user_message: str, context: List[Dict]) -> Dict:
        """Main agent reasoning and planning function"""
        self.conversation_context = context
        self.agent_steps = []
        
        # Step 1: Analyze user intent and create execution plan
        plan = await self.analyze_intent_and_plan(user_message)
        
        # Step 2: Execute the plan step by step
        results = []
        for step_num, step in enumerate(plan["steps"], 1):
            try:
                result = await self.execute_step(step_num, step)
                results.append(result)
                self.agent_steps.append(
                    AgentStep(
                        step=step_num,
                        action=step["action"],
                        tool_used=step["tool"],
                        result=str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
                        reasoning=step["reasoning"]
                    )
                )
            except Exception as e:
                logging.error(f"Error executing step {step_num}: {e}", exc_info=True)
                continue
        
        # Step 3: Synthesize final response
        final_response = await self.synthesize_response(user_message, results, plan)
        
        return {
            "response": final_response,
            "agent_steps": self.agent_steps,
            "tools_used": list(set([step["tool"] for step in plan["steps"]]))
        }
    
    def validate_islamic_query(self, user_message: str) -> bool:
        """Validate if the query is Islamic-related"""
        islamic_keywords = [
            "islam", "islamic", "quran", "quranic", "hadith", "sunnah", "prophet", "muhammad", 
            "allah", "prayer", "salah", "dua", "mosque", "masjid", "halal", "haram", 
            "ramadan", "hajj", "umrah", "zakat", "shahada", "iman", "tawhid", "fiqh",
            "salam", "assalam", "assalamu alaikum", "bismillah", "alhamdulillah", "inshallah",
            "surah", "ayah", "verse", "qibla", "wudu", "ghusl", "tahajjud", "fajr", "dhuhr",
            "asr", "maghrib", "isha", "jummah", "friday", "eid", "mecca", "medina", "kaaba"
        ]
        
        greetings = ["hi", "hello", "hey", "salam", "assalam", "assalamu alaikum", "how are you", "good morning", "good evening"]
        
        message_lower = user_message.lower()
        
        # Allow greetings
        if any(greeting in message_lower for greeting in greetings):
            return True
            
        # Check for Islamic keywords
        return any(keyword in message_lower for keyword in islamic_keywords)

    async def analyze_intent_and_plan(self, user_message: str) -> Dict:
        """Analyze user intent and create execution plan"""
        
        # Validate if query is Islamic-related
        if not self.validate_islamic_query(user_message):
            return {
                "intent": "non_islamic_query",
                "complexity": "simple",
                "steps": [{
                    "action": "Restrict non-Islamic query",
                    "tool": "restrict_query",
                    "reasoning": "Query is not related to Islamic topics",
                    "parameters": {"message": user_message}
                }]
            }
        
        # Check for simple greetings/casual messages first
        casual_patterns = ["hi", "hello", "hey", "salam", "assalam", "good morning", "good evening", "how are you"]
        if any(pattern in user_message.lower() for pattern in casual_patterns):
            return {
                "intent": "Greeting/casual conversation",
                "complexity": "simple",
                "steps": [{
                    "action": "Respond to greeting",
                    "tool": "direct_response",
                    "reasoning": "User is greeting or making casual conversation",
                    "parameters": {"message": user_message}
                }]
            }
        
        # Create planning prompt
        tools_description = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])
        
        planning_prompt = f"""
            You are an Islamic AI agent that helps Muslims with religious guidance and practical needs. 
        
            Available tools:
            {tools_description}

            User message: "{user_message}"

            Analyze the user's intent and create a step-by-step execution plan. Consider:
            1. What information does the user need?
            2. What tools should be used and in what order?
            3. Are there multiple aspects to address?
            4. Does this require location-based information?
            5. Is this a complex multi-step query?
            6. If this is just a greeting or casual conversation, respond with "direct_response" tool

            Respond with a JSON plan in this format:
            {{
                "intent": "brief description of what user wants",
                "complexity": "simple|moderate|complex",
                "steps": [
                    {{
                        "action": "description of what to do",
                        "tool": "tool_name_to_use",
                        "reasoning": "why this step is needed",
                        "parameters": {{tool_parameters}}
                    }}
                ]
            }}

            For simple questions, use 1-2 steps. For complex requests, break into logical steps.
        """

        try:
            response = openrouter.openrouter_client.chat.completions.create(
                model=os.getenv("OPENROUTER_MODEL_OPENAI"),
                messages=[
                    {
                        "role": "user", 
                        "content": planning_prompt
                    }
                ],
                max_tokens=800,
                temperature=0.3,
                timeout=30
            )
            
            plan_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            else:
                # Better fallback - check if it's Islamic-related
                islamic_keywords = ["islam", "quran", "hadith", "prayer", "salah", "dua", "allah", "prophet", "muhammad", "mosque", "halal", "haram"]
                if any(keyword in user_message.lower() for keyword in islamic_keywords):
                    return {
                        "intent": "Islamic knowledge inquiry",
                        "complexity": "simple",
                        "steps": [{
                            "action": "Search for Islamic knowledge",
                            "tool": "search_islamic_knowledge",
                            "reasoning": "User needs Islamic information",
                            "parameters": {"query": user_message}
                        }]
                    }
                else:
                    return {
                        "intent": "General conversation",
                        "complexity": "simple",
                        "steps": [{
                            "action": "Provide general response",
                            "tool": "direct_response",
                            "reasoning": "General inquiry not requiring specific tools",
                            "parameters": {"message": user_message}
                        }]
                    }
                
        except Exception as e:
            logging.error(f"Error in planning: {e}", exc_info=True)
            return self._get_fallback_plan(user_message)
    
    def _get_fallback_plan(self, user_message: str) -> Dict:
        """Generate fallback plan when AI planning fails"""
        islamic_keywords = ["islam", "quran", "hadith", "prayer", "salah", "dua", "allah", "prophet", "muhammad", "mosque", "halal", "haram"]
        if any(keyword in user_message.lower() for keyword in islamic_keywords):
            return {
                "intent": "Islamic inquiry",
                "complexity": "simple",
                "steps": [{
                    "action": "Search Islamic knowledge",
                    "tool": "search_islamic_knowledge",
                    "reasoning": "Islamic-related query",
                    "parameters": {"query": user_message}
                }]
            }
        else:
            return {
                "intent": "Non-Islamic query",
                "complexity": "simple",
                "steps": [{
                    "action": "Restrict non-Islamic query",
                    "tool": "restrict_query",
                    "reasoning": "Query is not related to Islamic topics",
                    "parameters": {"message": user_message}
                }]
            }
    
    async def execute_step(self, step_num: int, step: Dict) -> Any:
        """Execute a single step in the plan"""
        if not isinstance(step, dict) or "tool" not in step:
            logging.error(f"Invalid step format at step {step_num}: {step}")
            return "Invalid step configuration"
            
        tool_name = step["tool"]
        parameters = step.get("parameters", {})
        
        if tool_name not in self.tools:
            logging.error(f"Tool {tool_name} not found at step {step_num}")
            return f"Tool {tool_name} not available"
            
        try:
            tool = self.tools[tool_name]
            result = await tool.function(**parameters)
            return result
        except Exception as e:
            logging.error(f"Error executing step {step_num} with tool {tool_name}: {e}", exc_info=True)
            return f"Error executing {tool_name}: {str(e)}"
    
    async def synthesize_response(self, user_message: str, results: List, plan: Dict) -> str:
        """Synthesize final response from all step results"""
        
        # Combine all results
        combined_results = "\n\n".join([
            f"Step {i+1} Result: {result}" 
            for i, result in enumerate(results) if result
        ])
        
        synthesis_prompt = f"""
            You are an Islamic AI agent providing a final response to a Muslim user.

            User's original question: "{user_message}"

            Execution results from various tools:
            {combined_results}

            Please synthesize a comprehensive, helpful, and authentic Islamic response that:
            1. Directly addresses the user's question
            2. Incorporates relevant information from the tool results
            3. Provides Islamic sources/references where appropriate
            4. Is compassionate and respectful
            5. Offers practical guidance when applicable
            6. Maintains authentic Islamic perspective
            7. Strictly limit the response content to not more than 150 words

            Keep the response conversational and helpful while being thorough.
        """

        try:
            response = openrouter.openrouter_client.chat.completions.create(
                model=os.getenv("OPENROUTER_MODEL_OPENAI"),
                messages=[
                    {
                        "role": "user", 
                        "content": synthesis_prompt
                    }
                ],
                max_tokens=4096,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in synthesis: {e}", exc_info=True)
            return "I apologize, but I encountered an issue generating a response. Please try again."
    
    # Tool implementation methods
    async def restrict_query(self, message: str) -> str:
        """Restrict non-Islamic queries"""
        return ("I'm an Islamic AI assistant designed to help with religious guidance, Quranic knowledge, "
                "prayer times, and Islamic practices. I can only assist with Islamic-related queries. "
                "Please ask me about Islamic topics, and I'll be happy to help!")
    
    async def direct_response(self, message: str) -> str:
        """Handle direct responses for greetings and casual conversation"""
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in ["salam", "assalam", "assalamu alaikum"]):
            return "Wa alaikum assalam wa rahmatullahi wa barakatuh! How can I assist you with your Islamic needs today?"
        elif any(greeting in message_lower for greeting in ["hi", "hello", "hey"]):
            return "Hello! I'm your Islamic AI assistant. I can help you with prayer times, Quranic guidance, Islamic knowledge, and more. How can I assist you today?"
        elif "how are you" in message_lower:
            return "Alhamdulillah, I'm here and ready to help you with any Islamic guidance or information you need. How can I assist you?"
        else:
            return "I'm here to help you with Islamic guidance, prayer times, Quranic knowledge, and more. What would you like to know?"
    
    async def search_islamic_knowledge(self, query: str, source_name: str = "all") -> str:
        """Search Islamic knowledge in Pinecone"""
        if not query or not query.strip():
            return "Search query is required"
            
        try:
            # Check index status first
            try:
                stats = await asyncio.wait_for(
                    asyncio.to_thread(pinecone.index.describe_index_stats), 
                    timeout=10
                )
            except asyncio.TimeoutError:
                logging.error(f"Failed to check index stats: {e}")
                return "Knowledge base is temporarily unavailable"
            
            query_embedding = self.generate_embedding(query.strip())
            if not query_embedding:
                return "Failed to process search query"
            
            search_results = pinecone.index.query(
                vector=query_embedding,
                top_k=3,  # Reduced for better performance
                include_metadata=True,
                namespace="sahih_bukhari"
            )
            
            if not search_results.matches:
                return "No relevant Islamic knowledge found for your query"
            
            # Process results more efficiently
            formatted_results = []
            for match in search_results.matches:
                content = match.metadata.get("text", "")
                source = match.metadata.get(source_name, "Unknown")
                # Truncate long content for better readability
                if len(content) > 300:
                    content = content[:300] + "..."
                formatted_results.append(f"Source: {source}\nContent: {content}")
            
            return f"Found {len(formatted_results)} results:\n\n" + "\n\n".join(formatted_results)
                
        except Exception as e:
            logging.error(f"Error searching Islamic knowledge: {e}", exc_info=True)
            return "Unable to search knowledge base at this time"
    
    async def get_prayer_times(self, location: str, date: str = None, method: int = 2) -> str:
        """Get prayer times using Aladhan API"""
        if not location or not location.strip():
            return "Location is required for prayer times"
            
        try:
            safe_location = html.escape(location.strip())
            
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Get coordinates for location
            geolocator = Nominatim(user_agent="islamic-agent")
            location_data = geolocator.geocode(location)
            
            if not location_data:
                return f"Could not find location: {safe_location}"
            
            lat, lng = location_data.latitude, location_data.longitude
            
            # Call Aladhan API
            url = f"http://api.aladhan.com/v1/timings/{date}"
            params = {
                "latitude": lat,
                "longitude": lng,
                "method": method
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" not in data or "timings" not in data["data"]:
                    return "Invalid response from prayer times service"
                    
                timings = data["data"]["timings"]
                prayer_times = f"Prayer times for {safe_location} on {date}:\n"
                prayer_times += f"Fajr: {timings['Fajr']}\n"
                prayer_times += f"Dhuhr: {timings['Dhuhr']}\n"
                prayer_times += f"Asr: {timings['Asr']}\n"
                prayer_times += f"Maghrib: {timings['Maghrib']}\n"
                prayer_times += f"Isha: {timings['Isha']}\n"
                
                return prayer_times
            else:
                return "Unable to fetch prayer times at this time"
                
        except requests.RequestException as e:
            logging.error(f"Network error getting prayer times: {e}")
            return "Unable to fetch prayer times due to network issues"
        except Exception as e:
            logging.error(f"Error getting prayer times: {e}", exc_info=True)
            return "Unable to fetch prayer times at this time"
    
    async def get_qibla_direction(self, location: str) -> str:
        """Calculate Qibla direction"""
        if not location or not location.strip():
            return "Location is required for Qibla calculation"
            
        try:
            safe_location = html.escape(location.strip())
            
            geolocator = Nominatim(user_agent="islamic-agent")
            location_data = geolocator.geocode(location)
            
            if not location_data:
                return f"Could not find location: {safe_location}"
            
            lat, lng = location_data.latitude, location_data.longitude
            
            # Kaaba coordinates
            kaaba_lat = 21.4225
            kaaba_lng = 39.8262
            
            # Calculate bearing to Kaaba
            lat1 = math.radians(lat)
            lat2 = math.radians(kaaba_lat)
            lng_diff = math.radians(kaaba_lng - lng)
            
            y = math.sin(lng_diff) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lng_diff)
            
            bearing = math.atan2(y, x)
            bearing = math.degrees(bearing)
            bearing = (bearing + 360) % 360
            
            return f"Qibla direction from {safe_location}: {bearing:.1f}° from North"
            
        except Exception as e:
            return f"Error calculating Qibla direction: {str(e)}"
    
    async def convert_islamic_date(self, date: str, from_calendar: str, to_calendar: str) -> str:
        """Convert between Gregorian and Islamic dates"""
        if not date or not from_calendar or not to_calendar:
            return "Date and calendar types are required"
            
        try:
            safe_date = html.escape(date.strip())
            
            if from_calendar == "gregorian" and to_calendar == "hijri":
                # Parse Gregorian date
                date_parts = date.split("-")
                if len(date_parts) != 3:
                    return "Invalid date format. Use YYYY-MM-DD"
                year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                
                # Convert to Hijri
                hijri_date = Gregorian(year, month, day).to_hijri()
                return f"Gregorian date {safe_date} corresponds to Hijri date: {hijri_date.day}/{hijri_date.month}/{hijri_date.year}"
                
            elif from_calendar == "hijri" and to_calendar == "gregorian":
                # Parse Hijri date
                date_parts = date.split("-") if "-" in date else date.split("/")
                if len(date_parts) != 3:
                    return "Invalid date format. Use YYYY-MM-DD or YYYY/MM/DD"
                year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                
                # Convert to Gregorian
                gregorian_date = Hijri(year, month, day).to_gregorian()
                return f"Hijri date {safe_date} corresponds to Gregorian date: {gregorian_date.day}/{gregorian_date.month}/{gregorian_date.year}"
            else:
                return "Invalid calendar conversion requested"
                
        except Exception as e:
            return f"Error converting date: {str(e)}"
    
    async def find_halal_places(self, location: str, place_type: str = "all", radius: int = 10) -> str:
        """Find halal places using mock data (implement with real API)"""
        if not location or not location.strip():
            return "Location is required to find halal places"
            
        try:
            safe_location = html.escape(location.strip())
            
            # This is a mock implementation - in production, integrate with:
            # - Zomato API for halal restaurants
            # - Google Places API for mosques
            # - Foursquare API for Islamic centers
            
            results = {
                "restaurant": [
                    f"Halal Restaurant 1 in {safe_location}",
                    f"Halal Restaurant 2 in {safe_location}",
                ],
                "mosque": [
                    f"Central Mosque of {safe_location}",
                    f"Community Islamic Center in {safe_location}",
                ],
                "islamic_center": [
                    f"Islamic Cultural Center in {safe_location}",
                    f"Muslim Community Center in {safe_location}",
                ]
            }
            
            if place_type == "all":
                all_places = []
                for places in results.values():
                    all_places.extend(places)
                return f"Found halal places near {safe_location}:\n" + "\n".join(all_places)
            else:
                places = results.get(place_type, [])
                return f"Found {place_type}s near {safe_location}:\n" + "\n".join(places)
                
        except Exception as e:
            return f"Error finding halal places: {str(e)}"
    
    async def get_islamic_guidance(self, topic: str, situation: str, madhab: str = "general") -> str:
        """Get specific Islamic guidance"""
        if not topic or not situation:
            return "Topic and situation are required for Islamic guidance"
            
        try:
            safe_topic = html.escape(topic.strip())
            safe_situation = html.escape(situation.strip())
            safe_madhab = html.escape(madhab.strip())
            
            # Search for relevant guidance in knowledge base
            guidance_query = f"{safe_topic} {safe_situation} Islamic ruling guidance {safe_madhab}"
            knowledge_result = await self.search_islamic_knowledge(guidance_query)
            
            # Generate contextual guidance
            guidance_prompt = f"""
                Provide Islamic guidance on the following:

                Topic: {safe_topic}
                Situation: {safe_situation}
                Madhab preference: {safe_madhab}

                Relevant Islamic sources found:
                {knowledge_result}

                Please provide clear, authentic Islamic guidance that:
                1. Addresses the specific situation
                2. Cites relevant Quran verses or authentic hadith
                3. Considers different scholarly opinions if applicable
                4. Provides practical advice
                5. Maintains compassionate tone

                Keep response concise but comprehensive.
            """

            response = openrouter.openrouter_client.chat.completions.create(
                model=os.getenv("OPENROUTER_MODEL_OPENAI"),
                messages=[{"role": "user", "content": guidance_prompt}],
                max_tokens=500,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting Islamic guidance: {str(e)}"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini"""
        if not text or not text.strip():
            logging.warning("Empty text provided for embedding generation")
            return []
            
        try:            
            result = gemini.genai_client.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            if 'embedding' not in result:
                logging.error("No embedding returned from Gemini API")
                return []
            return result['embedding']
        except Exception as e:
            logging.error(f"Error generating embedding for text: {e}", exc_info=True)
            return []
