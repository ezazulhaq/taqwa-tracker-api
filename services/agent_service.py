import json
import os
import math
import requests

from typing import Any, Dict, List
from datetime import datetime

from dotenv import load_dotenv
from config import openrouter, pinecone, gemini
from entity.user import UserProfile
from model.agent import AgentTool
from model.chat import AgentStep
from geopy.geocoders import Nominatim
from hijri_converter import Hijri, Gregorian

load_dotenv()


class AgentService:
    def __init__(self):
        self.tools = {}
        self.user_profile = UserProfile()
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
                print(f"Error executing step {step_num}: {e}")
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
                temperature=0.3
            )
            
            plan_text = response.choices[0].message.content
            
            # Extract JSON from response
            import re
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
            print(f"Error in planning: {e}")
            # Better fallback logic
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
        tool_name = step["tool"]
        parameters = step.get("parameters", {})
        
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return await tool.function(**parameters)
        else:
            return f"Tool {tool_name} not found"
    
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
            print(f"Error in synthesis: {e}")
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
        try:
            stats = pinecone.index.describe_index_stats()
            if stats.total_vector_count == 0:
                return "Index is empty"
            
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return "Embedding failed"
            
            search_results = pinecone.index.query(
                vector=query_embedding,
                top_k=5,
                include_metadata=True,
                namespace="sahih_bukhari"
            )
            
            if not search_results.matches:
                return "No matches found"
            
            results = []
            for match in search_results.matches:
                results.append({
                    "content": match.metadata.get("text", ""),
                    "source": match.metadata.get("source_name", ""),
                    "hadith_no": match.metadata.get("hadith_no", ""),
                    "score": match.score
                })
            
            formatted_results = []
            for r in results:
                formatted_results.append(f"Score: {r['score']:.3f}\nSource: {r['source']}\nContent: {r['content']}")
            
            return f"Found {len(results)} results:\n" + "\n\n".join(formatted_results)
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def get_prayer_times(self, location: str, date: str = None, method: int = 2) -> str:
        """Get prayer times using Aladhan API"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Get coordinates for location
            geolocator = Nominatim(user_agent="islamic-agent")
            location_data = geolocator.geocode(location)
            
            if not location_data:
                return f"Could not find location: {location}"
            
            lat, lng = location_data.latitude, location_data.longitude
            
            # Call Aladhan API
            url = f"http://api.aladhan.com/v1/timings/{date}"
            params = {
                "latitude": lat,
                "longitude": lng,
                "method": method
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                timings = data["data"]["timings"]
                
                # Sanitize location input to prevent XSS
                safe_location = location.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
                prayer_times = f"Prayer times for {safe_location} on {date}:\n"
                prayer_times += f"Fajr: {timings['Fajr']}\n"
                prayer_times += f"Dhuhr: {timings['Dhuhr']}\n"
                prayer_times += f"Asr: {timings['Asr']}\n"
                prayer_times += f"Maghrib: {timings['Maghrib']}\n"
                prayer_times += f"Isha: {timings['Isha']}\n"
                
                return prayer_times
            else:
                return "Unable to fetch prayer times at this time"
                
        except Exception as e:
            return f"Error getting prayer times: {str(e)}"
    
    async def get_qibla_direction(self, location: str) -> str:
        """Calculate Qibla direction"""
        try:
            geolocator = Nominatim(user_agent="islamic-agent")
            location_data = geolocator.geocode(location)
            
            if not location_data:
                return f"Could not find location: {location}"
            
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
            
            return f"Qibla direction from {location}: {bearing:.1f}° from North"
            
        except Exception as e:
            return f"Error calculating Qibla direction: {str(e)}"
    
    async def convert_islamic_date(self, date: str, from_calendar: str, to_calendar: str) -> str:
        """Convert between Gregorian and Islamic dates"""
        try:
            if from_calendar == "gregorian" and to_calendar == "hijri":
                # Parse Gregorian date
                date_parts = date.split("-")
                year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                
                # Convert to Hijri
                hijri_date = Gregorian(year, month, day).to_hijri()
                return f"Gregorian date {date} corresponds to Hijri date: {hijri_date.day}/{hijri_date.month}/{hijri_date.year}"
                
            elif from_calendar == "hijri" and to_calendar == "gregorian":
                # Parse Hijri date
                date_parts = date.split("-") if "-" in date else date.split("/")
                year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                
                # Convert to Gregorian
                gregorian_date = Hijri(year, month, day).to_gregorian()
                return f"Hijri date {date} corresponds to Gregorian date: {gregorian_date.day}/{gregorian_date.month}/{gregorian_date.year}"
            else:
                return "Invalid calendar conversion requested"
                
        except Exception as e:
            return f"Error converting date: {str(e)}"
    
    async def find_halal_places(self, location: str, place_type: str = "all", radius: int = 10) -> str:
        """Find halal places using mock data (implement with real API)"""
        try:
            # This is a mock implementation - in production, integrate with:
            # - Zomato API for halal restaurants
            # - Google Places API for mosques
            # - Foursquare API for Islamic centers
            
            results = {
                "restaurant": [
                    f"Halal Restaurant 1 in {location}",
                    f"Halal Restaurant 2 in {location}",
                ],
                "mosque": [
                    f"Central Mosque of {location}",
                    f"Community Islamic Center in {location}",
                ],
                "islamic_center": [
                    f"Islamic Cultural Center in {location}",
                    f"Muslim Community Center in {location}",
                ]
            }
            
            if place_type == "all":
                all_places = []
                for places in results.values():
                    all_places.extend(places)
                return f"Found halal places near {location}:\n" + "\n".join(all_places)
            else:
                places = results.get(place_type, [])
                return f"Found {place_type}s near {location}:\n" + "\n".join(places)
                
        except Exception as e:
            return f"Error finding halal places: {str(e)}"
    
    async def get_islamic_guidance(self, topic: str, situation: str, madhab: str = "general") -> str:
        """Get specific Islamic guidance"""
        try:
            # Search for relevant guidance in knowledge base
            guidance_query = f"{topic} {situation} Islamic ruling guidance {madhab}"
            knowledge_result = await self.search_islamic_knowledge(guidance_query)
            
            # Generate contextual guidance
            guidance_prompt = f"""
                Provide Islamic guidance on the following:

                Topic: {topic}
                Situation: {situation}
                Madhab preference: {madhab}

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
        try:            
            result = gemini.genai_client.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
