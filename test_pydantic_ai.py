
from pydantic_ai import Agent
import asyncio

async def test():
    agent = Agent('openai:gpt-4o-mini')
    result = await agent.run('hello')
    print(f"Attributes: {dir(result)}")
    try:
        print(f"Data: {result.data}")
    except AttributeError:
        print("No .data attribute")
    try:
        print(f"Output: {result.output}")
    except AttributeError:
        print("No .output attribute")

if __name__ == "__main__":
    asyncio.run(test())
