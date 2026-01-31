from pydantic_ai import Agent
import os
from dotenv import load_dotenv

load_dotenv()

def test_simple():
    print("Testing simple Pydantic AI agent...")
    try:
        # Use a model that doesn't require API key for setup, or use the key from env
        model = "openai:gpt-4o-mini"
        agent = Agent(model)
        print(f"Agent created with model: {model}")
        # result = agent.run_sync("Say hello") # Don't run this yet as it might hang
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple()
