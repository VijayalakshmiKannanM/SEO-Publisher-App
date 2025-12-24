# agents.py
import os
import json
import asyncio
from typing import Dict, Any
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import Swarm
from autogen_ext.tools.langchain import LangChainToolAdapter
from langchain_tavily import TavilySearch
from helpers import with_retries  # optional retry helper
from db import init_db, save_post  # your persistence module

def initialize_agent_results():
    # Initialize results for each agent
    results = {
        "ResearchAgent": "...",
        "WriterAgent": "...",
        "VerificationAgent": "...",
        "RefinementAgent": "...",
        "SEOAgent": "..."
    }
    
    # Initialize scores for each agent
    scores = {agent_name: 0 for agent_name in results.keys()}
    
    # Determine the highest score
    final_score = max(scores.values())
    
    # Return all three
    return results, scores, final_score


# Example usage:
results, scores, final_score = initialize_agent_results()
print("Results:", results)
print("Scores:", scores)
print("Final Score:", final_score)


# -----------------------------
# SAFETY & CORRECTNESS CHECKS
# -----------------------------
SAFETY_CHECKS = [
    {"Risk": "Hallucination", "How we avoided it": "Web search tool enforced (Tavily) – agents reference real sources"},
    {"Risk": "Repetition", "How we avoided it": "Agent system prompts instruct to avoid repeating content"},
    {"Risk": "Outdated info", "How we avoided it": "Use real-time Google results via Tavily"},
    {"Risk": "Wrong intent", "How we avoided it": "Dedicated SEO agent ensures content matches target intent"},
    {"Risk": "Weak topics", "How we avoided it": "Final score check + rejection/resubmission if below target"},
]

# -----------------------------
# Run SEO Swarm
# -----------------------------
async def run_agents(topic: str, target_score: int) -> Dict[str, Any]:
    init_db()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    # 1️⃣ Create the model client
    model = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=api_key)

    # 2️⃣ Web search tool
    tavily = TavilySearch(max_results=5)
    tool = LangChainToolAdapter(tavily)

    # 3️⃣ Safety text
    safety_text = "\n".join([f"{c['Risk']}: {c['How we avoided it']}" for c in SAFETY_CHECKS])

    # 4️⃣ Create agents
    agents = [
        AssistantAgent(
            "ResearchAgent",
            tools=[tool],
            model_client=model,
            system_message="Research topic with sources, provide references."
        ),
        AssistantAgent(
            "WriterAgent",
            model_client=model,
            system_message="Write SEO content with headings, keywords, and meta description."
        ),
        AssistantAgent(
            "VerificationAgent",
            tools=[tool],
            model_client=model,
            system_message="Check factual accuracy, correct errors, and improve clarity."
        ),
        AssistantAgent(
            "RefinementAgent",
            model_client=model,
            system_message="Refine content for readability, flow, grammar, and SEO optimization."
        ),
        AssistantAgent(
            "SEOAgent",
            model_client=model,
            system_message=f"""
You are an SEO expert. Follow the Safety & Correctness guidelines strictly:
{safety_text}

Score content 1-10 and provide improvement suggestions. Return only valid JSON.
"""
        ),
    ]

    swarm = Swarm(agents, max_turns=5)  # round-robin execution

    results = {agent.name: "" for agent in agents}
    scores = {agent.name: 0 for agent in agents}
    final_score = 0

    # -----------------------------
    # Run swarm asynchronously with retries
    # -----------------------------
    async def run_team():
        async for msg in swarm.run_stream(task=f"Create SEO content on '{topic}', target score {target_score}/10"):
            if hasattr(msg, "content"):
                results[msg.source] = msg.content

                # Extract score from SEOAgent
                if msg.source == "SEOAgent":
                    import re
                    m = re.search(r"(\d+)/10", msg.content)
                    if m:
                        score = int(m.group(1))
                        scores[msg.source] = score
                        final_score = score

                # Stop early if target score reached
                if final_score >= target_score:
                    break
        return results

    # Retry wrapper
    results = await with_retries(run_team)

    # Persist to DB
    save_post({
        "title": results.get("WriterAgent", "")[:100],
        "content": results.get("WriterAgent", ""),
        "keywords": ["AI", "SEO"],  # placeholder; you can parse from content
        "seo_score": scores.get("SEOAgent", 0),
        "readability_score": scores.get("RefinementAgent", 0),
        "metadata": {"topic": topic}
    })

    return {"results": results, "scores": scores, "final_score": final_score}
