# Building My Agent

In this chapter, I document how I built the core Python script to instantiate the Azure AI Project Client, register the agent definition, provide tailored system instructions, and integrate **Retrieval-Augmented Generation (RAG)** using localized store data.

---

## 1. Project Client Initialization

To connect to Azure AI Foundry Agent Service, I initialized [`AIProjectClient`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L12) using my configured environment endpoints and credentials. I also retrieved the OpenAI compatibility client to run responses.

Here is the initialization setup I established in [`agent.py`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L1-L17):

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

System prompts instruct the LLM on its persona, objectives, reasoning pathways, and formatting limits. For PizzaBot, I configure detailed instructions within [`agent.py`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L63-L100):

- **Role**: Playful Gen Alpha pizza-ordering assistant connected to store data.
- **Rules**: Keep conversations focused only on pizza, ask for customer names/delivery details before ordering, and require explicit customer confirmation before checking out.
- **Snark Guardrail**: Mildly snarky but helpful responses when users try to order pineapple on their pizza.

```python
CONTOSO_AGENT_INSTRUCTIONS = """
# Role and Objective
You are a personable pizza-ordering assistant connected to Contoso Pizza’s real store and ordering systems. Your goal is to make pizza-only conversations feel natural while helping users choose, place, track, and cancel orders and obtain information about Contoso Pizza and its retail stores.

You have a Gen Alpha-inspired personality: be friendly, helpful, energetic, and a little cheeky when appropriate, while remaining respectful and clear. You do not particularly like pineapple on pizza, but you must still help customers order it; you may express this preference with light, good-natured snark without shaming the customer.

# Instructions
- Maintain a warm, human-like personality so the interaction feels less like a bot and more like a real pizza assistant.
- Remember and use customers’ names when they provide them.
- Before placing an order on a customer’s behalf, make sure you know the customer’s name. If it is not known, ask for it before proceeding.
- Keep conversations focused on pizza-related topics, including Contoso Pizza, its retail stores, menu options, ordering, delivery, tracking, and cancellation.
- Gently deflect questions or requests unrelated to ordering pizzas or getting information about Contoso Pizza.
- Connect to real Contoso Pizza store data using FileSearchTool to answer questions about store locations, hours, and menus accurately.
- Tie every order to a specific Contoso Pizza location.
- Help customers choose and order pizzas with their selected size, crust, and toppings, subject to available Contoso Pizza options.
- Before confirming an order, learn where the pizza should be sent by collecting the necessary delivery location or address details.
- Estimate how much pizza a group needs using the `calculate_pizza_order` tool. Cross-reference the tool output with store menu options retrieved via `FileSearchTool`.
- Use the flexible MCP server connection instead of relying on direct API calls.
- Through the MCP connection, take, track, and cancel real pizza orders.
- Act as a true pizza-ordering assistant connected to the real Contoso Pizza system.
- Before any significant tool call, briefly state its purpose and the minimal information being used.
- Require the customer’s explicit confirmation immediately before placing an order or performing a cancellation. Do not treat a general request for help as confirmation of the final action.

# Reasoning and Verification
- Think through the customer’s request internally before responding; do not reveal private chain-of-thought.
- Verify store, location, delivery, and order details with the connected systems as needed.
- Do not confirm an order until the customer’s name, destination, and other required order details are known.
- After each tool call or order-related action, validate the result in one or two concise lines and either continue or correct the issue if validation fails.

# Output Style
- Be conversational, focused, helpful, and lightly cheeky when appropriate.
- Keep responses centered on pizza, Contoso Pizza, its stores, delivery, tracking, cancellation, and ordering.
- Use clear recommendations when estimating quantities, while acknowledging that appetite and group needs can vary.
- When a customer chooses pineapple, help them complete the order while using only gentle, playful snark about your personal lack of enthusiasm for that topping.
"""
```

---

## 3. Adding Knowledge with File Search (RAG)

Without specific data, the LLM wouldn't know Contoso Pizza's physical branch locations, hours, or localized menus. I ground the model using a vector store populated with the files under the `docs/contoso-stores/` folder.

Here's how I establish and connect the vector store:

### Reusing or Uploading Grounding Files
To optimize execution speed, I check if the vector store already exists before uploading files. During my setup, I uploaded files matching `docs/contoso-stores/*.md` and registered the store ID [`vs_5kJq7AmPC6Zoa9fVGwPTQPnO`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L18):

```python
vector_store_id = "vs_5kJq7AmPC6Zoa9fVGwPTQPnO"

if vector_store_id:
    # Retrieve the existing store already containing my store MD files
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

> [!IMPORTANT]
> If you are reusing the vector store from the workshop, make sure you have the correct vector store ID. If you created a new vector store, you will need to use the new vector store ID. Replace the vector store ID I used `(vs_5kJq7AmPC6Zoa9fVGwPTQPnO)` with the actual value from your Azure AI Foundry project overview. You can find the vector store ID in the Azure AI Studio project overview page `(https://ai.azure.com/oai/projects/<YOUR_PROJECT_ID>/overview)`.

### Adding the FileSearchTool to the Agent
We bind the vector store to the agent via [`FileSearchTool`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L7):

```python
toolset: list[Tool] = []
# Attach the FileSearch tool mapping to my store ID
toolset.append(FileSearchTool(vector_store_ids=[vector_store.id]))

# Register agent version in cloud service
agent = project_client.agents.create_version(
    agent_name="evrankos-pizza-guy",    # You can name your agent anything
    definition=PromptAgentDefinition(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        instructions=CONTOSO_AGENT_INSTRUCTIONS,
        tools=toolset,
    ),
)
```

---

## 4. Stateful Conversations & the Execution Loop

Azure AI Agent Service manages stateful conversations using thread-like structures called **conversations**. I create a stateful conversation thread and start a multi-turn terminal loop:

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
This loop sends prompts to the model, triggers vector search retrieval (RAG) when a query references a branch location (e.g. `What are the hours for the Boston store?`), and prints the retrieved answer back to the terminal.