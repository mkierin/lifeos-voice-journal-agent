import openai
from openai import OpenAI
from .config import DEEPSEEK_API_KEY, OPENAI_API_KEY, get_setting

class LLMClient:
    def __init__(self):
        self.provider = get_setting("llm_provider")
        
        if self.provider == "deepseek":
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            self.model = "deepseek-chat"
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = "gpt-4o-mini"
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from LLM"""
        # Refresh provider from settings
        self.provider = get_setting("llm_provider")
        if self.provider == "deepseek":
            self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            self.model = "deepseek-chat"
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = "gpt-4o-mini"

        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": get_setting("system_prompt")})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=get_setting("temperature"),
                max_tokens=get_setting("max_tokens")
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def classify_categories(self, text: str, categories: dict) -> list:
        """Use LLM to classify text into categories"""
        category_list = ", ".join(categories.keys())
        
        prompt = f"""Classify the following text into one or more of these categories: {category_list}

Text: "{text}"

Return only the category names as a comma-separated list. If none fit, return "general"."""
        
        response = self.generate(prompt, system_prompt="You are a classifier that only outputs comma-separated category names.")
        cats = [c.strip().lower() for c in response.split(",")]
        return [c for c in cats if c in categories or c == "general"]
