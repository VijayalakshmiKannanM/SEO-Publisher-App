import asyncio
import logging
import streamlit as st
from pathlib import Path
import re
import difflib
import os

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import Swarm

# -------------------------------
# Logging
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# OpenAI API Key (update your valid key here)
# -------------------------------

import os
from dotenv import load_dotenv

load_dotenv()  # This loads variables from .env into os.environ

api_key = os.getenv("OPENAI_API_KEY")
print(api_key)



# -------------------------------
# Optional Tavily
# -------------------------------
TAVILY_AVAILABLE = False  # Set True if TavilySearch is installed and available

# -------------------------------
# Minimal test to check API
# -------------------------------
from openai import OpenAI
client = OpenAI()
try:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("✅ OpenAI key valid, test message OK")
except Exception as e:
    print(f"❌ OpenAI test failed: {e}")

# -------------------------------
# Async agent pipeline
# -------------------------------
async def run_agents_until_target(topic: str, model_name: str, keywords: list, target_score: int = 10,
                                  use_tavily: bool = False, max_turns: int = 2, max_iterations: int = 5):
    model = OpenAIChatCompletionClient(model=model_name)
    tools_list = []

    # Only add Tavily if available
    if use_tavily and TAVILY_AVAILABLE:
        from autogen_ext.tools.tavily import TavilySearch
        from autogen_agentchat.tools.langchain import LangChainToolAdapter
        tavily = LangChainToolAdapter(TavilySearch(max_results=5))
        tools_list.append(tavily)

    keyword_text = ", ".join(keywords) if keywords else "no specific keywords"

    # Agents definition
    agents = {
        "ResearchAgent": AssistantAgent(
            "ResearchAgent",
            model_client=model,
            tools=tools_list,
            system_message=(f"Provide comprehensive research on '{topic}' including statistics, examples, and references. "
                            f"Include keywords naturally: {keyword_text}.")
        ),
        "WriterAgent": AssistantAgent(
            "WriterAgent",
            model_client=model,
            system_message=(f"Write SEO-optimized content for '{topic}' using the research. "
                            f"Include H1/H2, bullet points, numbered lists, natural keyword placement: {keyword_text}.")
        ),
        "VerificationAgent": AssistantAgent(
            "VerificationAgent",
            model_client=model,
            system_message="Check all facts, URLs, references. Suggest fixes."
        ),
        "RefinementAgent": AssistantAgent(
            "RefinementAgent",
            model_client=model,
            system_message=(f"Refine content for clarity, SEO, readability, engagement, and keyword usage: {keyword_text}. "
                            f"Ensure facts and references are correct.")
        ),
        "ReviewerAgent": AssistantAgent(
            "ReviewerAgent",
            model_client=model,
            system_message=(f"Score content 0–10 on headings, structure, readability, keywords, references, search intent. "
                            f"Output only numeric score. Target: {target_score}.")
        ),
        "ScoreVerifierAgent": AssistantAgent(
            "ScoreVerifierAgent",
            model_client=model,
            system_message=(f"Verify the SEO content and provide a confirmed score 0–10, considering all SEO best practices. "
                            f"Output only numeric score. Target: {target_score}.")
        ),
        "FinalSummaryAgent": AssistantAgent(
            "FinalSummaryAgent",
            model_client=model,
            system_message="Write a concise summary and conclusion based on the final content."
        ),
    }

    results = {}
    prev_writer = ""
    prev_refinement = ""
    score = 0
    verified_score = 0
    loop_count = 0

    while score < target_score and loop_count < max_iterations:
        loop_count += 1
        team = Swarm(list(agents.values()), max_turns=max_turns)

        refinement_instruction = ""
        if verified_score < target_score:
            refinement_instruction = f" Improve content to reach SEO score {target_score}/10 using keywords: {keyword_text}."
        task_text = f"Generate SEO content for: {topic} (loop {loop_count}){refinement_instruction}"

        # Run swarm
        async for msg in team.run_stream(task=task_text):
            if hasattr(msg, "content"):
                results[msg.source] = (
                    " ".join(msg.content) if isinstance(msg.content, list) else str(msg.content)
                )

        # Extract scores
        review_text = results.get("ReviewerAgent", "")
        score = int(re.search(r'(\d{1,2})', review_text).group(1)) if review_text else 0
        verified_score_text = results.get("ScoreVerifierAgent", "")
        verified_score = int(re.search(r'(\d{1,2})', verified_score_text).group(1)) if verified_score_text else score

        logger.info(f"Loop {loop_count}: SEO score = {score}, Verified score = {verified_score}")

        # Highlight WriterAgent changes
        writer_content = results.get("WriterAgent", "")
        if loop_count > 1 and prev_writer:
            diff = difflib.ndiff(prev_writer.splitlines(), writer_content.splitlines())
            highlighted = "".join(
                f"<span style='background-color:#d4fcbc'>{line[2:]}</span><br>" if line.startswith("+ ") else
                f"{line[2:]}<br>" if not line.startswith("- ") else ""
                for line in diff
            )
            results["WriterAgent"] = highlighted
        prev_writer = writer_content

        # Highlight RefinementAgent changes
        refinement_content = results.get("RefinementAgent", "")
        if loop_count > 1 and prev_refinement:
            diff = difflib.ndiff(prev_refinement.splitlines(), refinement_content.splitlines())
            highlighted_ref = "".join(
                f"<span style='background-color:#fce0d4'>{line[2:]}</span><br>" if line.startswith("+ ") else
                f"{line[2:]}<br>" if not line.startswith("- ") else ""
                for line in diff
            )
            results["RefinementAgent"] = highlighted_ref
        prev_refinement = refinement_content

        yield results, verified_score, loop_count

        # Stop early if content unchanged
        if writer_content.strip() == prev_writer.strip() and refinement_content.strip() == prev_refinement.strip():
            logger.info("Content unchanged, stopping early.")
            break

    # Fallback defaults
    defaults = {
        "ResearchAgent": "No research results.",
        "WriterAgent": f"Sample SEO content for {topic}.",
        "VerificationAgent": "Content verified.",
        "RefinementAgent": "Content refined.",
        "ReviewerAgent": f"SEO score: {score}/{target_score}",
        "ScoreVerifierAgent": f"Verified SEO score: {verified_score}/{target_score}",
        "FinalSummaryAgent": f"Summary and conclusion for {topic}.",
    }
    for key, value in defaults.items():
        if key not in results or not results[key]:
            results[key] = value

    yield results, verified_score, loop_count
