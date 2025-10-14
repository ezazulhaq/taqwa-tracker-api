# Taqwa Tracker API

A comprehensive FastAPI microservice for Islamic guidance and Quranic data access, featuring an intelligent AI agent for Islamic knowledge, prayer times, and religious guidance.

## Features

- **AI-Powered Islamic Agent**: Intelligent conversational agent for Islamic guidance
- **Quranic Data Access**: RESTful API for Surahs, Ayahs, and translations
- **Prayer Times & Qibla**: Location-based prayer times and Qibla direction
- **Islamic Knowledge Search**: Vector-based search through hadith and Islamic texts
- **Multi-Modal Chat**: Conversation management with context and history
- **User Profiles**: Location, timezone, and preference management
- **PostgreSQL Integration**: Robust database with SQLModel ORM
- **Vector Search**: Pinecone integration for semantic Islamic knowledge search
- **Multi-LLM Support**: OpenRouter and Google Gemini integration

## Project Structure

```
taqwa-tracker-api/
├── config/
│   ├── database.py          # Database configuration
│   ├── gemini.py           # Google Gemini AI configuration
│   ├── openrouter.py       # OpenRouter LLM configuration
│   └── pinecone.py         # Pinecone vector DB configuration
├── entity/
│   ├── agent.py            # Agent execution entities
│   ├── chat.py             # Chat and conversation entities
│   ├── surah.py            # Quranic data entities
│   └── user.py             # User profile entities
├── model/
│   ├── agent.py            # Agent response models
│   ├── chat.py             # Chat request/response models
│   ├── surah.py            # Surah response models
│   └── user.py             # User profile models
├── services/
│   ├── agent_service.py    # AI agent business logic
│   ├── chat_service.py     # Chat management service
│   ├── surah_service.py    # Quranic data service
│   └── user_service.py     # User management service
├── main.py                 # FastAPI application
├── requirements.txt        # Dependencies
├── pyproject.toml          # Project configuration
├── vercel.json            # Vercel deployment config
└── README.md              # Documentation
```

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL database (Supabase recommended)
- Pinecone account for vector search
- OpenRouter API key for LLM access
- Google Gemini API key for embeddings

### Installation

1. Clone the repository
2. Install dependencies using uv (recommended) or pip:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

3. Set environment variables (create `.env` file):
```bash
# PostgreSQL Configuration
TAQWA_TRACKER_DB_HOSTNAME=your-db-host
TAQWA_TRACKER_DB_NAME=your-db-name
TAQWA_TRACKER_DB_USERNAME=your-username
TAQWA_TRACKER_DB_PASSWORD=your-password
TAQWA_TRACKER_DB_PORT=5432

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=your-index-name

# OpenRouter Configuration
OPENROUTER_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL_MISTRAL=mistralai/mistral-nemo
OPENROUTER_MODEL_OPENAI=openai/gpt-4

# Google Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL_EMBED=models/text-embedding-004
```

### Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Checks
- `GET /` - Basic status check
- `GET /health/db` - Database connection test

### Quranic Data
- `GET /surahs/{surah_no}` - Get ayahs for a specific surah (1-114)
  - **Parameters**: `surah_no` (integer, 1-114)
  - **Response**: List of ayah details with Arabic text and translations

### AI Chat Agent
- `POST /chat` - Main conversational AI endpoint
  - **Request Body**:
    ```json
    {
      "message": "Your Islamic question or request",
      "conversation_id": "optional-uuid",
      "location": "optional-city-name",
      "timezone": "optional-timezone"
    }
    ```
  - **Response**:
    ```json
    {
      "response": "AI agent response",
      "conversation_id": "conversation-uuid",
      "message_id": "message-uuid",
      "agent_steps": ["execution steps"],
      "tools_used": ["list of tools"]
    }
    ```

## AI Agent Capabilities

The AI agent provides comprehensive Islamic assistance through various tools:

### 🕌 Islamic Knowledge
- Quranic verse search and interpretation
- Hadith lookup and authentication
- Scholarly opinions and rulings
- Islamic jurisprudence (Fiqh) guidance

### 🕐 Prayer & Worship
- Location-based prayer times
- Qibla direction calculation
- Islamic calendar conversions (Hijri ↔ Gregorian)
- Ramadan and Hajj guidance

### 📍 Location Services
- Halal restaurant finder
- Nearby mosque locator
- Islamic center directory
- Prayer time calculations for any location

### 💬 Conversational AI
- Context-aware conversations
- Multi-turn dialogue support
- Personalized responses based on user profile
- Islamic etiquette and manners guidance

## Database Schema

### Core Tables
- `conversations` - Chat conversation management
- `messages` - Individual chat messages with metadata
- `user_profiles` - User preferences and location data
- `agent_executions` - AI agent execution logs and analytics
- `surahs` - Quranic surah data
- `v_surah_details` - Detailed ayah view with translations

## Deployment

### Vercel (Recommended)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Set environment variables in Vercel dashboard or CLI:
```bash
vercel env add TAQWA_TRACKER_DB_HOSTNAME
vercel env add TAQWA_TRACKER_DB_NAME
# ... add all environment variables
```

3. Deploy:
```bash
vercel --prod
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Dependencies

### Core Framework
- **FastAPI** - Modern web framework for APIs
- **SQLModel** - SQL database ORM with Pydantic integration
- **Uvicorn** - ASGI server for production

### Database & Storage
- **psycopg2-binary** - PostgreSQL adapter
- **pinecone** - Vector database for semantic search

### AI & ML
- **openai** - OpenAI API client (via OpenRouter)
- **google-generativeai** - Google Gemini AI integration

### Utilities
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for external APIs
- **geopy** - Geocoding and location services
- **pytz** - Timezone handling
- **hijri-converter** - Islamic calendar conversions

## Usage Examples

### Basic Islamic Question
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the 5 pillars of Islam?"
  }'
```

### Prayer Times Request
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are today\'s prayer times?",
    "location": "New York, NY",
    "timezone": "America/New_York"
  }'
```

### Quranic Verse Lookup
```bash
curl -X GET "http://localhost:8000/surahs/1"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team

---

*Built with ❤️ for the Muslim community*