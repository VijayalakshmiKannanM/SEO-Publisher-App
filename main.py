import asyncio
import sys
from typing import Any, Dict
from agents import run_agents

async def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "Artificial Intelligence in 2025"
    target = 9
    results: Dict[str, Any] = await run_agents(topic, target)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
