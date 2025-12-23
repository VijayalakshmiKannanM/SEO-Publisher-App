# ERP Hot Topics Agent Quick Start

This project demonstrates how three agents interact to research ERP hot topics in a fact-grounded manner using web search.

## Agents

- **TopicSelectorAgent**: Searches the web for "ERP hot topics" and lists top current trends.
- **TopicResearchAgent**: For a chosen topic, runs web searches to gather supporting information and summarizes key authoritative content.
- **SEOIntentAgent**: Checks the summarized content against real search signals via web search, scores relevance/intent match, and ensures no hallucination by using search results only.

All agents use Autogen's AssistantAgent with a Tavily web search tool for verified, fact-grounded output.

## Setup

1. Create a virtual environment:
   ```
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

3. Install dependencies:
   ```
   pip install python-dotenv autogen-agentchat autogen-ext openai langchain-community google-search-results streamlit
   ```

4. Get API keys:
   - **OPENAI_API_KEY**: From [OpenAI](https://platform.openai.com/account/api-keys).
   - **SERPAPI_KEY**: From [SerpAPI](https://serpapi.com/) (sign up for a free plan).

5. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_key_here
   SERPAPI_KEY=your_serpapi_key_here
   ```

## Running the App

Activate the virtual environment:
```
.\.venv\Scripts\Activate.ps1
```

Run the Streamlit app:
```
streamlit run quick_start.py
```

Open the provided URL in your browser to access the modern dashboard. Click "Start ERP Research" to run the AI agents and view the latest ERP trends, research summary, and relevance scoreboard.

## Notes

- The free Tavily plan provides 1,000 API credits/month.
- Ensure your OpenAI key has access to GPT-4o or adjust the model in the code.
- The code uses asyncio for asynchronous execution.