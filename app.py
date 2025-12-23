import asyncio
import re
import streamlit as st
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import Swarm
from autogen_ext.tools.langchain import LangChainToolAdapter
from tavily import TavilySearch
from langchain_tavily import TavilySearch


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="🚀 SEO AI Generator", layout="wide")
st.markdown("<h1>🚀 SEO AI Content Generator</h1>", unsafe_allow_html=True)

# -----------------------------
# Dark card styling with light text
# -----------------------------
st.markdown("""
<style>
.card {
    padding: 1.2rem;
    border-radius: 16px;
    background: linear-gradient(135deg,#1e1e2f,#2a2a40);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    margin-bottom: 1rem;
    color: #f0f0f0;  /* Light text */
    font-size: 14px;
    line-height: 1.5;
}
.sidebar .stMarkdown {
    color: #f0f0f0;
}
.scoreboard {
    padding: 0.8rem;
    border-radius: 12px;
    background: #0f172a;
    color: #f0f0f0;
    margin-bottom: 1rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# User Input
# -----------------------------
topic = st.text_input("Topic", placeholder="Enter your topic")
target_score = st.slider("Target SEO Score", 1, 10, 10)

# -----------------------------
# Run Swarm with Verification and Refinement
# -----------------------------
async def run_perfect_swarm(topic, target_score):
    model = OpenAIChatCompletionClient(model="gpt-4o-mini")
    tavily = TavilySearch(max_results=5)
    tool = LangChainToolAdapter(tavily)

    # Define agents
    agents = [
        AssistantAgent("ResearchAgent", tools=[tool], model_client=model, system_message="Research topic with sources."),
        AssistantAgent("WriterAgent", model_client=model, system_message="Write SEO content with headings and keywords."),
        AssistantAgent("VerificationAgent", tools=[tool], model_client=model, system_message="Check factual accuracy and correct errors."),
        AssistantAgent("RefinementAgent", model_client=model, system_message="Improve clarity, flow, grammar, and SEO."),
        AssistantAgent("ReviewerAgent", model_client=model, system_message=f"Score SEO out of 10. If < {target_score}, provide detailed improvement suggestions."),
    ]

    swarm = Swarm(agents, max_turns=5)  # multiple turns for perfection

    results = {agent.name: "" for agent in agents}
    scores = {agent.name: 0 for agent in agents}  # track reviewer scores per turn
    final_score = 0

    # Run swarm and update agents dynamically
    async for msg in swarm.run_stream(task=f"Create SEO content on: {topic}. Target score {target_score}/10"):
        if hasattr(msg, "content"):
            results[msg.source] = msg.content

            # If ReviewerAgent responded, extract score
            if msg.source == "ReviewerAgent":
                m = re.search(r"(\d+)/10", msg.content)
                if m:
                    score = int(m.group(1))
                    scores[msg.source] = score
                    final_score = score

            # Optional: real-time sidebar updates
            st.sidebar.markdown(f"### {msg.source}")
            st.sidebar.markdown(f"<div class='card'>{msg.content}</div>", unsafe_allow_html=True)

        # Stop early if target score reached
        if final_score >= target_score:
            break

    return results, scores, final_score

# -----------------------------
# Run button
# -----------------------------
if st.button("✨ Generate Perfect SEO Content"):
    with st.spinner("🤖 AI Agents collaborating for perfection..."):
        results, scores, final_score = asyncio.run(run_perfect_swarm(topic, target_score))

    # -----------------------------
    # Main Content Display
    # -----------------------------
    st.markdown("### 📝 Main Content")
    st.markdown(f"<div class='card'>{results.get('WriterAgent','')}</div>", unsafe_allow_html=True)

    st.markdown("### ✅ Verification / Refinement")
    st.markdown(f"<div class='card'>{results.get('VerificationAgent','')}\n{results.get('RefinementAgent','')}</div>", unsafe_allow_html=True)

    st.markdown("### 📈 SEO Review")
    st.markdown(f"<div class='card'>{results.get('ReviewerAgent','')}</div>", unsafe_allow_html=True)

    st.markdown("### 🔍 Citations / Sources")
    st.markdown(f"<div class='card'>{results.get('ResearchAgent','')}</div>", unsafe_allow_html=True)

    # -----------------------------
    # Scoreboard
    # -----------------------------
    st.markdown("### 🏆 Scoreboard")
    scoreboard_text = "\n".join([f"{agent}: {score}/10" for agent, score in scores.items()])
    st.markdown(f"<div class='scoreboard'>{scoreboard_text}</div>", unsafe_allow_html=True)

    st.markdown(f"### 🎯 Final Score: {final_score}/10")
