# 🚀 Built an Enterprise AI Agent at Microsoft HQ OpenHack! 🍕🤖

I recently attended the **Microsoft AI Foundry Workshop OpenHack** and built **Contoso PizzaBot**—a fully functional, domain-specific AI assistant that leverages state-of-the-art agentic architectures! 

Here is a summary of the tech stack and architecture I implemented:

### 🛠️ The Tech Stack & Architecture:
- **Orchestration**: Built using the new **Azure AI Foundry Client SDK** and stateful **Agent Service** runs.
- **Base Model**: Powered by **GPT-4o** for advanced natural language understanding and reasoning.
- **Retrieval-Augmented Generation (RAG)**: Grounded the agent with localized store branch details (Boston, Amsterdam, San Francisco) by dynamically querying search indexes in an **Azure AI Search Vector Store**.
- **Deterministic Action Tools**: Configured strict local Python **Function Tools** to handle precise quantity calculations (estimating order sizes based on group sizes) without relying on LLM math.
- **Model Context Protocol (MCP)**: Integrated the agent with live ordering systems over **Server-Sent Events (SSE)** Container Apps using the new open-standard MCP. The agent dynamically discovers tools to pull menus, toppings, and manage order placements!

---

### 💡 Key Skills & Takeaways:
1. **Agentic Personas & Safety**: Mastered designing detailed system prompts to enforce strict domain guardrails, handle personality quirks (like playful pineapple-on-pizza snark 🍍), and implement Human-in-the-Loop order confirmations.
2. **Unified Abstractions (MCP)**: Experienced firsthand how MCP solves the API integration problem. Instead of writing custom endpoints for every database or dashboard, you hook into an MCP server and tools are dynamically resolved by the agent.
3. **State Management**: Orchestrated stateful conversational threads, runs, and local tool call execution interception using the Azure AI SDK.

*Special thanks to the Microsoft team for hosting such a high-impact, hands-on hackathon!*

👉 Check out the source code in the repository: `agent.py`

#AzureAIFoundry #Azure #OpenAI #AIAgents #ModelContextProtocol #RAG #MachineLearning #Python #CloudComputing #MicrosoftOpenHack
