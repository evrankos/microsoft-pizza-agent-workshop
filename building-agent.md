# 3. Building Your First Agent

In this chapter, you will build the core Python script to instantiate the Azure AI Project Client, register the agent definition, provide tailored system instructions, and integrate **Retrieval-Augmented Generation (RAG)** using localized store data.

---

## 1. Project Client Initialization

To connect to Azure AI Foundry Agent Service, we initialize [`AIProjectClient`](./agent.py#L12) using our configured environment endpoints and credentials. We also get the OpenAI compatibility client to run responses.

Here is the initialization setup from [`agent.py`](./agent.py#L1-L17):

```python
import os
import json
import glob
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FileSearchTool, Tool

# Load environment secrets
load_dotenv()

# Initialize connection client
project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# Fetch compatible openai client
openai_client = project_client.get_openai_client()
```

---

## 2. Shaping Behavior with System Instructions

System prompts instruct the LLM on its persona, objectives, reasoning pathways, and formatting limits. For PizzaBot, we configure detailed instructions within [`agent.py`](./agent.py#L63-L100):

- **Role**: Playful Gen Alpha pizza-ordering assistant connected to store data.
- **Rules**: Keep conversations focused only on pizza, ask for customer names/delivery details before ordering, and require explicit customer confirmation before checking out.
- **Snark Guardrail**: Mildly snarky but helpful responses when users try to order pineapple on their pizza.

```python
CONTOSO_AGENT_INSTRUCTIONS = """
# Role and Objective
You are a personable pizza-ordering assistant connected to Contoso Pizza’s real store and ordering systems. Your goal is to make pizza-only conversations feel natural while helping users choose, place, track, and cancel orders...

# Instructions
- Remember and use customers’ names when they provide them.
- Gently deflect questions or requests unrelated to ordering pizzas.
- Before confirming an order, learn where the pizza should be sent.
- Require the customer’s explicit confirmation immediately before placing an order.
- When a customer chooses pineapple, help them complete the order while using only gentle, playful snark.
"""
```

---

## 3. Adding Knowledge with File Search (RAG)

Without specific data, the LLM wouldn't know Contoso Pizza's physical branch locations, hours, or localized menus. We ground the model using a vector store populated with the files under the `docs/contoso-stores/` folder.

Here's how we establish and connect the vector store:

### Reusing or Uploading Grounding Files
To optimize execution speed, we check if the vector store already exists before uploading files. During our setup, we uploaded files matching `docs/contoso-stores/*.md` and registered the store ID [`vs_5kJq7AmPC6Zoa9fVGwPTQPnO`](./agent.py#L18):

```python
vector_store_id = "vs_5kJq7AmPC6Zoa9fVGwPTQPnO"

if vector_store_id:
    # Retrieve the existing store already containing our store MD files
    vector_store = openai_client.vector_stores.retrieve(vector_store_id)
    print(f"Using existing vector store (id: {vector_store.id})")
else:
    # Fallback to create a store and upload contoso-stores files
    vector_store = openai_client.vector_stores.create(name="ContosoPizzaStores")
    for file_path in glob.glob("docs/contoso-stores/*.md"):
        openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=open(file_path, "rb")
        )
```

### Adding the FileSearchTool to the Agent
We bind the vector store to the agent via [`FileSearchTool`](./agent.py#L7):

```python
toolset: list[Tool] = []
# Attach the FileSearch tool mapping to our store ID
toolset.append(FileSearchTool(vector_store_ids=[vector_store.id]))

# Register agent version in cloud service
agent = project_client.agents.create_version(
    agent_name="evrankos-pizza-guy",
    definition=PromptAgentDefinition(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        instructions=CONTOSO_AGENT_INSTRUCTIONS,
        tools=toolset,
    ),
)
```

---

## 4. Stateful Conversations & the Execution Loop

Azure AI Agent Service manages stateful conversations using thread-like structures called **conversations**. We create a stateful conversation thread and start a multi-turn terminal loop:

```python
# Create conversational thread
conversation = openai_client.conversations.create()
print(f"Created conversation (id: {conversation.id})")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # Send input and run the agent version
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=user_input,
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )

    # Print response
    print(f"Assistant: {response.output_text}")
```
This loop sends prompts to the model, triggers vector search retrieval (RAG) when a query references a branch location (e.g. "What are the hours for the Boston store?"), and prints the retrieved answer back to the terminal.