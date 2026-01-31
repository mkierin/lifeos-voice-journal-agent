from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
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
        async def manage_task(
            ctx: RunContext[JournalDeps],
            description: str,
            task_id: Optional[str] = None,
            status: Literal["open", "completed", "archived"] = "open",
            goal_id: Optional[str] = None,
            due_date: Optional[str] = None
        ) -> str:
            """
            Create or update an actionable task.
            - description: What needs to be done.
            - task_id: If updating, provide the existing ID. If None, a new one is created.
            - status: 'open' or 'completed'.
            - goal_id: Optional link to a higher-level goal.
            - due_date: Optional ISO date for reminders.
            """
            tid = task_id or str(uuid.uuid4())
            ctx.deps.vector_store.upsert_task(
                user_id=ctx.deps.user_id,
                task_id=tid,
                description=description,
                status=status,
                goal_id=goal_id,
                due_date=due_date
            )
            return f"Task '{description}' (ID: {tid}) has been { 'updated' if task_id else 'created' } with status: {status}."

        @self.agent.tool
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
                output += f"- {p['description']} (ID: {t.id}){due}{goal}\n"
            return output

        @self.agent.tool
        async def set_reminder(ctx: RunContext[JournalDeps], reminder_text: str, in_days: int) -> str:
            """Set a reminder for the user in a certain number of days."""
            due_date = (datetime.now() + timedelta(days=in_days)).isoformat()
            tid = str(uuid.uuid4())
            ctx.deps.vector_store.upsert_task(
                user_id=ctx.deps.user_id,
                task_id=tid,
                description=f"REMINDER: {reminder_text}",
                status="open",
                due_date=due_date,
                metadata={"type": "reminder"}
            )
            return f"Reminder set for {reminder_text} in {in_days} days (Due: {due_date[:10]})."

        @self.agent.system_prompt
        def get_system_prompt(ctx: RunContext[JournalDeps]) -> str:
            base_prompt = get_setting("system_prompt")
            date_info = f"\nToday is {ctx.deps.current_date}."
            instructions = """
You are a personal journal assistant. You act as a coach and friend.

### Output Style:
- NO Markdown bolding (**). Use plain text.
- Be extremely concise.
- Use a friendly, casual tone (down-to-earth).
- Condense retrieved info to essentials.

### Goal Tracking & Task Extrapolation:
When a user mentions a long-term goal:
1. **Break it down**: Create actionable tasks with `manage_task`.
2. **Check Progress**: Mark tasks 'completed' when the user mentions progress.
3. **Adaptive**: Update tasks dynamically.
4. **Reminders**: Use `set_reminder` or `manage_task` with a `due_date`.

### Task Management:
- Use `get_open_tasks` to see pending items.
- Refer to tasks naturally, avoid technical IDs unless necessary.
"""
            return f"{base_prompt}{date_info}{instructions}"

        @self.agent.tool
        def search_journal(ctx: RunContext[JournalDeps], query: str, limit: int = 5) -> str:
            """Search the user's journal for relevant entries based on a query."""
            results = ctx.deps.vector_store.search(query, ctx.deps.user_id, limit=limit)
            if not results:
                return "No relevant entries found."
            return "\n".join([f"- [{r.payload.get('type', 'general')}] {r.payload['text']} ({r.payload['timestamp'][:10]})" for r in results])

        @self.agent.tool
        def get_recent_entries(ctx: RunContext[JournalDeps], limit: int = 5) -> str:
            """Retrieve the most recent entries from the user's journal."""
            results = ctx.deps.vector_store.get_recent_entries(ctx.deps.user_id, limit=limit)
            if not results:
                return "No entries found yet."
            return "\n".join([f"- [{r.payload.get('type', 'general')}] {r.payload['text']} ({r.payload['timestamp'][:10]})" for r in results])

        @self.agent.tool
        async def add_journal_entry(
            ctx: RunContext[JournalDeps], 
            text: str, 
            entry_type: Literal["general", "goal", "idea", "fitness", "project"] = "general",
            status: Optional[Literal["pending", "in_progress", "completed", "abandoned"]] = None,
            metadata: Optional[dict] = None
        ) -> str:
            """
            Add a new entry to the journal with specific type and status.
            - entry_type: category of the entry (goal, idea, fitness, etc.)
            - status: relevant for goals (pending, in_progress, completed)
            - metadata: any extra key-value pairs to store
            """
            final_metadata = metadata or {}
            final_metadata["type"] = entry_type
            if status:
                final_metadata["status"] = status
            
            # Use the classifier to get categories if it's general, otherwise use the type
            categories = [entry_type] if entry_type != "general" else ["general"]
            
            ctx.deps.vector_store.add_entry(
                text=text,
                categories=categories,
                user_id=ctx.deps.user_id,
                metadata=final_metadata
            )
            return f"Successfully saved {entry_type} to your journal."

        @self.agent.tool
        async def update_goal_status(
            ctx: RunContext[JournalDeps], 
            goal_description: str, 
            new_status: Literal["pending", "in_progress", "completed", "abandoned"]
        ) -> str:
            """
            Update the status of an existing goal. 
            Search for the goal first, then save a new entry reflecting the status update.
            """
            # We don't "update" in-place in vector DB easily without ID, 
            # so we add a new entry marking the progress.
            text = f"Updated status for goal '{goal_description}' to {new_status}."
            ctx.deps.vector_store.add_entry(
                text=text,
                categories=["goal", "update"],
                user_id=ctx.deps.user_id,
                metadata={"type": "goal", "status": new_status, "goal_ref": goal_description}
            )
            return f"Goal status updated to {new_status}."

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
