# main.py
import asyncio
import sys
import os

# Ensure current directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agents import run_agents

async def main():
    topic = "Artificial Intelligence in 2025"
    target_score = 9

    try:
        results = await run_agents(topic, target_score)
        # Cleanly print all sections
        for key, value in results.items():
            if isinstance(value, list):
                value = "\n".join(value)
            print(f"\n=== {key.capitalize()} ===\n{value}")
    except Exception as e:
        print("❌ Error running agents:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
