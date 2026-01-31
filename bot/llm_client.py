from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
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

    def _setup_agents(self):
        provider = get_setting("llm_provider")
        if provider == "deepseek":
            model_name = "openai:deepseek-chat"
            base_url = "https://api.deepseek.com"
            api_key = DEEPSEEK_API_KEY
        else:
            model_name = "openai:gpt-4o-mini"
            base_url = None
            api_key = OPENAI_API_KEY

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

        # Classifier agent for structured output
        self.classifier = Agent(
            model_name,
            result_type=ClassificationOutput,
            system_prompt="You are an expert classifier. Categorize the journal entry accurately.",
            retries=2
        )
        
        # Configure model with proper API key and base URL
        from pydantic_ai.models.openai import OpenAIChatModel
        model = OpenAIChatModel(model_name.split(':', 1)[1], base_url=base_url, api_key=api_key)
        self.agent.model = model
        self.classifier.model = model

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from LLM using pydantic-ai"""
        self._setup_agents() # Refresh settings
        
        if system_prompt:
            # Create a temporary agent with the custom system prompt
            temp_agent = Agent(self.agent.model, system_prompt=system_prompt)
            result = temp_agent.run_sync(prompt)
        else:
            result = self.agent.run_sync(prompt)
            
        return result.data

    def classify_categories(self, text: str) -> List[str]:
        """Use pydantic-ai for structured classification"""
        self._setup_agents()
        
        category_list = ", ".join(CATEGORIES.keys())
        prompt = f"Classify this journal entry into one or more of these categories: {category_list}\n\nEntry: \"{text}\""
        
        try:
            result = self.classifier.run_sync(prompt)
            cats = [c.strip().lower() for c in result.data.categories]
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
