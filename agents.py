# agents.py
import asyncio
import os
import openai
import re

# Make sure your OpenAI API key is set in environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

async def run_agents(topic, target_score):
    """
    Run AI agents to generate research, content, verification, refinement, review, and citations.
    Parses model output into structured sections.
    """
    prompt = f"""
You are a content creation assistant. For the topic "{topic}", provide output in the following format:

Research: [Brief research on the topic]
Content: [Draft content on the topic]
Verification: [Confirm facts are correct]
Refinement: [Refined content for clarity and flow]
Review: [Give an SEO score out of 10]
Citations: [Provide at least one credible source link]
"""

    # Call the OpenAI API (wrapped for async)
    response = await asyncio.to_thread(
        lambda: openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
    )

    reply = response.choices[0].message.content.strip()

    # Parse the output into sections using regex
    sections = re.findall(r"(Research|Content|Verification|Refinement|Review|Citations):\s*(.*?)\s*(?=(Research|Content|Verification|Refinement|Review|Citations):|$)", reply, re.DOTALL)

    # Build a dictionary
    result = {}
    for section in sections:
        key = section[0].lower()
        value = section[1].strip()
        # For citations, convert to list if multiple
        if key == "citations":
            value = [link.strip() for link in re.split(r",|\n", value) if link.strip()]
        result[key] = value

    # Ensure all fields exist even if the model didn't return them
    defaults = {
        "research": "No research generated.",
        "content": "No content generated.",
        "verification": "Not verified.",
        "refinement": "No refinement generated.",
        "review": f"SEO score: {target_score}/10",
        "score": target_score,
        "citations": []
    }

    for k, v in defaults.items():
        if k not in result:
            result[k] = v

    return result
