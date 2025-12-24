# app.py
import asyncio
import streamlit as st
from agents import run_agents  # async function
from helpers import with_retries  # optional, if used in agents.py

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
# Page config
# -----------------------------
st.set_page_config(page_title="🚀 SEO AI Generator", layout="wide")
st.markdown("<h1 style='color:#ff6f61;'>🚀 SEO AI Content Generator</h1>", unsafe_allow_html=True)

# -----------------------------
# Sidebar Inputs
# -----------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#61dafb;'>Settings</h2>", unsafe_allow_html=True)

    topic = st.text_input("Topic", placeholder="Enter your topic here")
    target_score = st.slider("Target SEO Score", 1, 10, 10)

    # Agent checkboxes
    st.markdown("### Select Agents to View")
    agents_to_view = []
    for agent in ["ResearchAgent", "WriterAgent", "VerificationAgent", "RefinementAgent", "SEOAgent"]:
        if st.checkbox(agent, value=True):
            agents_to_view.append(agent)

    generate_btn = st.button("✨ Generate SEO Content")

    # Safety & Correctness displayed once
    st.markdown("### 🔒 Safety & Correctness Checks")
    for check in SAFETY_CHECKS:
        st.markdown(f"**{check['Risk']}**: {check['How we avoided it']}")

# -----------------------------
# Main Panel: Generate content
# -----------------------------
if generate_btn and topic:
    with st.spinner("🤖 Agents collaborating..."):
        results, scores, final_score = asyncio.run(run_agents(topic, target_score))

    # Display content for selected agents
    for agent_name in agents_to_view:
        st.markdown(f"### 📝 {agent_name} Output")
        st.markdown(
            f"<div style='padding:1rem; border-radius:12px; background:#1e1e2f; color:#f0f0f0'>{results.get(agent_name, '')}</div>",
            unsafe_allow_html=True
        )

    # -----------------------------
    # Scoreboard
    # -----------------------------
    st.markdown("### 🏆 Scores")
    for agent, score in scores.items():
        st.markdown(f"**{agent}**: {score}/10")

    # -----------------------------
    # Final Score
    # -----------------------------
    st.markdown(f"### 🎯 Final Score: {final_score}/10")
