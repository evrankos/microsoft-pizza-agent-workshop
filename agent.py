import json
import os
import glob
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FileSearchTool, FunctionTool, MCPTool, Tool
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam

load_dotenv()

project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

vector_store_id = "vs_5kJq7AmPC6Zoa9fVGwPTQPnO"

## -- FILE SEARCH -- ##
vector_store = openai_client.vector_stores.retrieve(vector_store_id)
print(f"Using existing vector store (id: {vector_store.id})")
## -- FILE SEARCH -- ##

## -- Function Calling Tool -- ##
func_tool = FunctionTool(
    name="calculate_pizza_order",  # <-- FIXED: Matched name with system instructions
    parameters={
        "type": "object",
        "properties": {
            "people": {
                "type": "integer",
                "description": "The number of people to order pizza for",
            },
        },
        "required": ["people"],
        "additionalProperties": False,
    },
    description="Get the quantity of pizza to order based on the number of people.",
    strict=True,
)

def calculate_pizza_order(people: int) -> str:  # <-- FIXED: Function name updated
    """Calculate the number of pizzas to order based on the number of people.
        Assumes each pizza can feed 2 people.
    Args:
        people (int): The number of people to order pizza for.
    Returns:
        str: A message indicating the number of pizzas to order.
    """
    print(f"[FUNCTION CALL:calculate_pizza_order] Calculating pizza quantity for {people} people.")
    return f"For {people} you need to order {people // 2 + people % 2} pizzas."
## -- Function Calling Tool -- ##

## -- MCP -- ##
mcpTool = MCPTool(
    server_label="contoso-pizza-mcp",
    server_url=os.environ.get(
        "MCP_SERVER_URL", 
        "https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/sse"
    ),
    require_approval="never"
)
## -- MCP -- ##

# ============================================================================
# System Instructions
# ============================================================================
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

## Define the toolset for the agent
toolset: list[Tool] = []
toolset.append(FileSearchTool(vector_store_ids=[vector_store.id]))
toolset.append(func_tool)
toolset.append(mcpTool)

agent = project_client.agents.create_version(
    agent_name="evrankos-pizza-guy",
    definition=PromptAgentDefinition(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        instructions=CONTOSO_AGENT_INSTRUCTIONS,
        tools=toolset,
    ),
)

conversation = openai_client.conversations.create()
print(f"Created conversation (id: {conversation.id})")

while True:
    # Get the user input
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the chat.")
        break

    # Get the agent response
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=user_input,
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )

    # Handle function calls in the response
    input_list: ResponseInputParam = []
    for item in response.output:
        if item.type == "function_call":
            if item.name == "calculate_pizza_order":  # <-- FIXED: Handled correct function name
                # Execute the function logic for calculate_pizza_order
                pizza_quantity = calculate_pizza_order(**json.loads(item.arguments))
                # Provide function call results to the model
                input_list.append(
                    FunctionCallOutput(
                        type="function_call_output",
                        call_id=item.call_id,
                        output=json.dumps({"pizza_quantity": pizza_quantity}),
                    )
                )

    if input_list:
        response = openai_client.responses.create(
            previous_response_id=response.id,
            input=input_list,
            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
        )    

    # Print the agent response
    print(f"Assistant: {response.output_text}")