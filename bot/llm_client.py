from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import asyncio
from functools import partial
from openai import OpenAI
from .config import DEEPSEEK_API_KEY, OPENAI_API_KEY, get_setting, CATEGORIES
from .vector_store import VectorStore

@dataclass
class JournalDeps:
    vector_store: VectorStore
    user_id: int
    current_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %A"))

class ClassificationOutput(BaseModel):
    categories: List[str] = Field(description="List of categories that apply to the text")
    reasoning: str = Field(description="Brief explanation of why these categories were chosen")

class LLMClient:
    def __init__(self):
        self._agent: Optional[Agent] = None
        self._classifier: Optional[Agent] = None
        self._last_provider: Optional[str] = None
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    def _get_model(self):
        """Get the appropriate model based on provider setting"""
        provider = get_setting("llm_provider")

        if provider == "deepseek":
            # DeepSeek uses OpenAI-compatible API
            return OpenAIModel(
                "deepseek-chat",
                base_url="https://api.deepseek.com",
                api_key=DEEPSEEK_API_KEY
            )
        else:
            # OpenAI
            return "openai:gpt-4o-mini"

    def _get_agent(self) -> Agent:
        provider = get_setting("llm_provider")
        if self._agent is None or provider != self._last_provider:
            self._last_provider = provider
            model = self._get_model()

            self._agent = Agent(
                model,
                deps_type=JournalDeps,
                system_prompt=get_setting("system_prompt"),
                retries=2
            )
            self._register_tools(self._agent)
        return self._agent

    def _get_classifier(self) -> Agent:
        provider = get_setting("llm_provider")
        if self._classifier is None or provider != self._last_provider:
            model = self._get_model()
            self._classifier = Agent(
                model,
                output_type=ClassificationOutput,
                system_prompt="You are an expert classifier. Categorize the journal entry accurately.",
                retries=2
            )
        return self._classifier

    @property
    def agent(self) -> Agent:
        return self._get_agent()

    def _register_tools(self, agent: Agent):
        @agent.tool
        async def manage_task(
            ctx: RunContext[JournalDeps],
            description: str,
            task_id: Optional[str] = None,
            status: Literal["open", "completed", "archived"] = "open",
            goal_id: Optional[str] = None,
            due_date: Optional[str] = None
        ) -> str:
            """Create or update an actionable task."""
            tid = task_id or str(uuid.uuid4())
            ctx.deps.vector_store.upsert_task(
                user_id=ctx.deps.user_id,
                task_id=tid,
                description=description,
                status=status,
                goal_id=goal_id,
                due_date=due_date
            )
            return f"Task '{description}' { 'updated' if task_id else 'created' }."

        @agent.tool
        def get_open_tasks(ctx: RunContext[JournalDeps], goal_id: Optional[str] = None) -> str:
            """Retrieve all currently open tasks for the user."""
            tasks = ctx.deps.vector_store.get_tasks(ctx.deps.user_id, status="open", goal_id=goal_id)
            if not tasks:
                return "No open tasks found."
            
            output = "Current Open Tasks:\n"
            for t in tasks:
                p = t.payload
                due = f" [Due: {p['due_date']}]" if p.get('due_date') else ""
                goal = f" (Goal: {p['goal_id']})" if p.get('goal_id') else ""
                output += f"- {p['description']}{due}{goal}\n"
            return output

        @agent.tool
        async def set_reminder(ctx: RunContext[JournalDeps], reminder_text: str, when: str = "tomorrow") -> str:
            """Set a reminder for the user. 'when' supports dates AND times:
            - With time: 'today at 3pm', 'tomorrow at 12', 'Tuesday at 18:30'
            - Relative: 'in 2 hours', 'in 30 minutes', 'in 3 days'
            - Date only: 'tomorrow', 'Tuesday', 'next week'
            """
            from .reminder_scheduler import parse_natural_date

            try:
                target_date = parse_natural_date(when)
                due_date = target_date.isoformat()

                tid = str(uuid.uuid4())
                ctx.deps.vector_store.upsert_task(
                    user_id=ctx.deps.user_id,
                    task_id=tid,
                    description=f"{reminder_text}",
                    status="open",
                    due_date=due_date,
                    metadata={"type": "reminder"}
                )

                date_str = target_date.strftime("%A, %B %d")
                return f"Reminder set: '{reminder_text}' on {date_str}"
            except Exception as e:
                return f"Could not set reminder: {str(e)}"

        @agent.system_prompt
        def get_system_prompt(ctx: RunContext[JournalDeps]) -> str:
            base_prompt = get_setting("system_prompt")
            date_info = f"\nToday is {ctx.deps.current_date}."
            instructions = """
You are a down-to-earth coach, mentor, and friend. Talk like you're texting a friend. 
Be chill, personal, and supportive. Use "I" and "you" naturally.

### STRICT RULES:
1. NO Markdown bolding (**). NO italics (*). NO complex formatting.
2. NO technical jargon. NO task IDs or internal references in messages.
3. Be EXTREMELY concise. One or two short sentences max.
4. If retrieving info from the journal, condense it to the absolute essentials.
5. Distinguish between high-level GOALS (outcomes) and actionable TASKS (steps).

Keep it real. Don't sound like an AI.
"""
            return f"{base_prompt}{date_info}{instructions}"

        @agent.tool
        def search_journal(ctx: RunContext[JournalDeps], query: str, limit: int = 5) -> str:
            """Search the user's journal for relevant entries based on a query."""
            results = ctx.deps.vector_store.search(query, ctx.deps.user_id, limit=limit)
            if not results:
                return "No relevant entries found."
            return "\n".join([f"- [{r.payload.get('type', 'general')}] {r.payload['text']} ({r.payload['timestamp'][:10]})" for r in results])

        @agent.tool
        def get_recent_entries(ctx: RunContext[JournalDeps], limit: int = 5) -> str:
            """Retrieve the most recent entries from the user's journal."""
            results = ctx.deps.vector_store.get_recent_entries(ctx.deps.user_id, limit=limit)
            if not results:
                return "No entries found yet."
            return "\n".join([f"- [{r.payload.get('type', 'general')}] {r.payload['text']} ({r.payload['timestamp'][:10]})" for r in results])

        @agent.tool
        async def add_journal_entry(
            ctx: RunContext[JournalDeps], 
            text: str, 
            entry_type: Literal["general", "goal", "idea", "fitness", "project"] = "general",
            status: Optional[Literal["pending", "in_progress", "completed", "abandoned"]] = None,
            metadata: Optional[dict] = None
        ) -> str:
            """Add a new entry to the journal."""
            final_metadata = metadata or {}
            final_metadata["type"] = entry_type
            if status:
                final_metadata["status"] = status
            
            categories = [entry_type] if entry_type != "general" else ["general"]
            
            ctx.deps.vector_store.add_entry(
                text=text,
                categories=categories,
                user_id=ctx.deps.user_id,
                metadata=final_metadata
            )
            return f"Successfully saved {entry_type} to your journal."

        @agent.tool
        async def update_goal_status(
            ctx: RunContext[JournalDeps], 
            goal_description: str, 
            new_status: Literal["pending", "in_progress", "completed", "abandoned"]
        ) -> str:
            """Update the status of an existing goal."""
            text = f"Updated status for goal '{goal_description}' to {new_status}."
            ctx.deps.vector_store.add_entry(
                text=text,
                categories=["goal", "update"],
                user_id=ctx.deps.user_id,
                metadata={"type": "goal", "status": new_status, "goal_ref": goal_description}
            )
            return f"Goal status updated to {new_status}."

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured for transcription")
        
        def _call_openai():
            with open(audio_file_path, "rb") as audio_file:
                return self.openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
        
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(None, _call_openai)
        return transcript.text
