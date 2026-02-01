## Project Summary
A personal voice journal assistant integrated with Telegram. It allows users to send voice messages which are transcribed using OpenAI Whisper, categorized, and stored in a Qdrant vector database. Users can then query their journal using natural language, and the system provides context-aware responses using DeepSeek or OpenAI APIs.

## Tech Stack
- Python 3.11
- Telegram Bot API (python-telegram-bot)
- OpenAI Whisper API (fast, reliable transcription)
- Qdrant (vector database) with FastEmbed
- DeepSeek / OpenAI (LLM for categorization and responses)
- Pydantic AI (modern agent framework)
- Docker & Docker Compose

## Architecture
- `bot/main.py`: Entry point for the Telegram bot.
- `bot/config.py`: Configuration and environment variable management.
- `bot/handlers.py`: Telegram message and command handlers.
- `bot/llm_client.py`: Wrapper for LLM interactions (DeepSeek/OpenAI/Whisper).
- `bot/vector_store.py`: Interface for Qdrant vector database operations.
- `data/`: Local storage for transient audio files.
- `qdrant_data/`: Persistent storage for the vector database (mapped to host).

## User Preferences
- VPS: 2 vCPU, 4GB RAM, 40GB Disk (Confirmed sufficient for this lightweight stack).
- Prefers low-cost solutions (DeepSeek by default).
- Support switching between DeepSeek and OpenAI.
- Personality: Down-to-earth coach, mentor, friend, and personal assistant.
- Communication Style: Extremely concise, casual "texting a friend" style.
- NO Markdown bolding (**). Use plain text.
- Info retrieval should be condensed to essentials unless a full plan is requested.
- Feedback: Wants immediate acknowledgment when sending messages.

## Project Guidelines
- Keep responses concise and actionable.
- Support auto-categorization of journal entries.
- Ensure easy deployment on Hetzner VPS using Docker Compose.
- Persistence is handled via the `./qdrant_data` volume mapping.
- Use `DEPLOYMENT.md` for specific VPS setup instructions.
- ALWAYS use `await agent.run()` and NEVER `run_sync()` in async handlers.
- Handle `AgentRunResult` safely using `get_result_data` helper.

## Common Patterns
- Semantic search for retrieving context from previous entries.
- Metadata filtering for category-specific queries.
