## Project Summary
A personal voice journal assistant integrated with Telegram. It allows users to send voice messages which are transcribed using OpenAI Whisper, categorized, and stored in a Qdrant vector database. Users can then query their journal using natural language, and the system provides context-aware responses using DeepSeek or OpenAI APIs.

## Tech Stack
- Python 3.11
- Telegram Bot API (python-telegram-bot)
- OpenAI Whisper (local transcription)
- Qdrant (vector database)
- DeepSeek / OpenAI (LLM for categorization and responses)
- Docker & Docker Compose

## Architecture
- `bot/main.py`: Entry point for the Telegram bot.
- `bot/config.py`: Configuration and environment variable management.
- `bot/handlers.py`: Telegram message and command handlers.
- `bot/llm_client.py`: Wrapper for LLM interactions (DeepSeek/OpenAI).
- `bot/vector_store.py`: Interface for Qdrant vector database operations.
- `data/`: Local storage for transient audio files.
- `qdrant_storage/`: Persistent storage for the vector database.

## User Preferences
- Prefers low-cost solutions.
- Use DeepSeek by default as it's cheaper.
- Support switching between DeepSeek and OpenAI.
- Containerized deployment using Docker.

## Project Guidelines
- Keep responses concise and actionable.
- Support auto-categorization of journal entries.
- Ensure easy deployment on Hetzner VPS.

## Common Patterns
- Semantic search for retrieving context from previous entries.
- Metadata filtering for category-specific queries.
