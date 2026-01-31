from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from openai import OpenAI
from .config import DEEPSEEK_API_KEY, OPENAI_API_KEY, get_setting, CATEGORIES
from .vector_store import VectorStore

@dataclass
class JournalDeps:
    vector_store: VectorStore
    user_id: int

class ClassificationOutput(BaseModel):
    categories: List[str] = Field(description="List of categories that apply to the text")
    reasoning: str = Field(description="Brief explanation of why these categories were chosen")

class LLMClient:
    def __init__(self):
        self._setup_agents()
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    def _setup_agents(self):
        provider = get_setting("llm_provider")
        if provider == "deepseek":
            model_name = "deepseek:deepseek-chat"
        else:
            model_name = "openai:gpt-4o-mini"

        # Base agent for general responses
        self.agent = Agent(
            model_name,
            deps_type=JournalDeps,
            system_prompt=get_setting("system_prompt"),
            retries=2
        )

        @self.agent.tool
        def search_journal(ctx: RunContext[JournalDeps], query: str, limit: int = 5) -> str:
            """Search the user's journal for relevant entries based on a query."""
            results = ctx.deps.vector_store.search(query, ctx.deps.user_id, limit=limit)
            if not results:
                return "No relevant entries found."
            return "\n".join([f"- {r.payload['text']} ({r.payload['timestamp'][:10]})" for r in results])

        @self.agent.tool
        def get_recent_entries(ctx: RunContext[JournalDeps], limit: int = 5) -> str:
            """Retrieve the most recent entries from the user's journal."""
            results = ctx.deps.vector_store.get_recent_entries(ctx.deps.user_id, limit=limit)
            if not results:
                return "No entries found yet."
            return "\n".join([f"- {r.payload['text']} ({r.payload['timestamp'][:10]})" for r in results])

        @self.agent.tool
        async def add_journal_entry(ctx: RunContext[JournalDeps], text: str) -> str:
            """
            Add a new entry to the journal. 
            Use this when the user provides information they want to save in their journal.
            """
            # We use the classifier to get categories
            # Note: we need to handle the fact that we are inside a tool
            # It's better to just call the vector store directly with a default category if needed,
            # or use the classifier if we can.
            # For simplicity in the tool, we'll just add it.
            ctx.deps.vector_store.add_entry(
                text=text,
                categories=["general"],
                user_id=ctx.deps.user_id
            )
            return "Entry saved successfully to your journal."

        # Classifier agent for structured output
        self.classifier = Agent(
            model_name,
            output_type=ClassificationOutput,
            system_prompt="You are an expert classifier. Categorize the journal entry accurately.",
            retries=2
        )

    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from LLM using pydantic-ai"""
        self._setup_agents() # Refresh settings
        
        if system_prompt:
            # Create a temporary agent with the custom system prompt
            temp_agent = Agent(self.agent.model, system_prompt=system_prompt)
            result = await temp_agent.run(prompt)
        else:
            result = await self.agent.run(prompt)
            
        return result.output

    async def classify_categories(self, text: str) -> List[str]:
        """Use pydantic-ai for structured classification"""
        self._setup_agents()
        
        category_list = ", ".join(CATEGORIES.keys())
        prompt = f"Classify this journal entry into one or more of these categories: {category_list}\n\nEntry: \"{text}\""
        
        try:
            result = await self.classifier.run(prompt)
            cats = [c.strip().lower() for c in result.output.categories]
            valid_cats = [c for c in cats if c in CATEGORIES]
            return valid_cats if valid_cats else ["general"]
        except Exception as e:
            print(f"Classification error: {e}")
            return ["general"]

    @property
    def provider(self):
        return get_setting("llm_provider")

    def switch_provider(self, provider: str):
        # This is handled by get_setting dynamically in _setup_agents
        pass

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured for transcription")
        
        # Use run_in_executor to avoid blocking the event loop with file I/O and sync API call
        import asyncio
        from functools import partial
        
        def _call_openai():
            with open(audio_file_path, "rb") as audio_file:
                return self.openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
        
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(None, _call_openai)
        return transcript.text
