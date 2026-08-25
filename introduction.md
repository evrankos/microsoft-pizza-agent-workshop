# 1. Workshop Introduction & Overview

Welcome to the **Contoso PizzaBot** AI agent workshop documentation! This guide documents the step-by-step implementation of an enterprise-grade, domain-specific AI assistant using the **Microsoft Azure AI Foundry Agent Service** and the **Model Context Protocol (MCP)**.

Built during the Microsoft HQ OpenHack workshop, this showcase demonstrates how to bridge LLMs with real-world private data and external service systems securely and efficiently.

---

## What We Are Building: Contoso PizzaBot 🍕🤖

The goal of this project is to create **Contoso PizzaBot**, a conversational agent that acts as a friendly, Gen Alpha-styled ordering assistant. Unlike a generic chatbot, PizzaBot is integrated into Contoso Pizza’s backend systems to answer store queries, recommend order sizes, and place real orders.

```mermaid
graph TD
    User([User Chat Interface]) <--> Loop[Agent Conversation Loop]
    Loop <--> Client[Azure AI Project Client]
    Client <--> AgentService[Azure AI Agent Service]
    
    subgraph Azure AI Foundry Tools
        AgentService <--> RAG[File Search RAG Vector Store]
        AgentService <--> LocalFunc[Local Function Tool: calculate_pizza_order]
        AgentService <--> MCP[MCP Tool: contoso-pizza-mcp SSE]
    end

    RAG --> Stores[(Store Markdown Grounding Docs)]
    MCP --> ContainerApp[Azure Container Apps Pizza API]
```

### Core Capabilities:
1. **Dynamic Persona & Guardrails**: Configured with strict rules to keep discussions focused on pizzas, handle Pineapple-on-pizza snark playfully, and require user confirmations before processing transactions.
2. **Retrieval-Augmented Generation (RAG)**: Connects to an Azure Vector Store containing localized markdown files for branches (Boston, Amsterdam, Sao Paulo, San Francisco, etc.) to query hours, addresses, and physical store menus.
3. **Deterministic Function Tools**: Calls local Python code to calculate pizza order quantities based on group sizes.
4. **Model Context Protocol (MCP)**: Integrates over Server-Sent Events (SSE) to a live Container Apps service to query real-time toppings, place new orders, track status, or execute cancellations.

---

## Key Skills & Concepts Covered

Through this project, you will learn and apply:
- **Azure AI Foundry Client SDK**: Initializing [`AIProjectClient`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L12) and orchestrating assistants and runs.
- **RAG & Semantic Indexing**: Setting up, uploading documents to, and querying vector stores using [`FileSearchTool`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L7).
- **Strict Schema Tooling**: Exposing Python helper functions to the model with strict JSON validations using [`FunctionTool`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L7).
- **MCP Integration**: Using the new industry-standard Model Context Protocol via [`MCPTool`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L7) to avoid custom API boilerplate.
- **Agent Loop Execution**: Managing stateful multi-turn runs, handling function call intermediate executions, and handling thread states.

---

## Document Site Roadmap

1. **[1. Introduction & Overview](./introduction.md)** (This page)
2. **[2. Environment & Azure Setup](./setup-environment.md)**: Authenticating, setting up the Azure Resource Group, deploying models, and loading variables.
3. **[3. Building Your First Agent](./building-agent.md)**: Creating the agent, setting system instructions, and enabling File Search (RAG) using your local store docs in `docs/contoso-stores/`.
4. **[4. Tools & MCP Integration](./tool-calling-mcp.md)**: Activating function tools, hooking into SSE MCP server endpoints, handling conversational loops, and testing live pizza ordering.