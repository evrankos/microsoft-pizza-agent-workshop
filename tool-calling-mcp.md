# 4. Tools & MCP Integration

In this final chapter, we extend **Contoso PizzaBot**'s reasoning capabilities by enabling it to perform deterministic actions. We accomplish this through two methods:
1. **Custom Function Tools**: Executing local Python functions (for pizza quantity estimations).
2. **Model Context Protocol (MCP) Tools**: Connecting the agent over Server-Sent Events (SSE) to a live backend ordering system.

---

## 1. Custom Function Tools

While LLMs excel at language comprehension, they are not reliable for exact calculations. We offload order sizing math to a local Python function wrapped in a structured schema.

### Defining the Tool Schema
In [`agent.py`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L25-L41), we define a strict parameters schema for the pizza calculator tool:

```python
func_tool = FunctionTool(
    name="calculate_pizza_order",
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
```

### Implementing the Local Function
The underlying logic is a deterministic Python function. It calculates the required pizzas assuming each pizza feeds 2 people (rounding up):

```python
def calculate_pizza_order(people: int) -> str:
    """Calculate the number of pizzas to order based on the number of people.
        Assumes each pizza can feed 2 people.
    Args:
        people (int): The number of people to order pizza for.
    Returns:
        str: A message indicating the number of pizzas to order.
    """
    print(f"[FUNCTION CALL:calculate_pizza_order] Calculating pizza quantity for {people} people.")
    return f"For {people} you need to order {people // 2 + people % 2} pizzas."
```

---

## 2. Model Context Protocol (MCP) Integration

The **Model Context Protocol (MCP)** is an open standard that enables models to connect to external systems seamlessly. Rather than writing custom SDK connectors for every database or API, you connect to an MCP server, which dynamically registers its available tools to the agent.

We connect to the Contoso Pizza backend MCP server deployed on Azure Container Apps, using an environment variable override if available:

```python
mcpTool = MCPTool(
    server_label="contoso-pizza-mcp",
    server_url=os.environ.get(
        "MCP_SERVER_URL", 
        "https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/sse"
    ),
    require_approval="never"
)
```

By appending `mcpTool` to the agent's toolset, the agent automatically discovers tools to:
- Retrieve pizza menu items and pricing details (`get_menu`).
- Query available toppings (`get_toppings`).
- Manage client orders (`create_order`, `get_order`, `cancel_order`).

---

## 3. Registering the Complete Toolset

The agent's toolset combines our RAG vector store, local function tool, and the live MCP connection:

```python
# Assemble all tools
toolset: list[Tool] = []
toolset.append(FileSearchTool(vector_store_ids=[vector_store.id]))  # RAG
toolset.append(func_tool)                                          # Function Calling
toolset.append(mcpTool)                                            # MCP Integration

# Create the agent version with the combined toolset
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

## 4. Handling Tool Execution in the Conversation Loop

When the agent decides to invoke a function tool, it returns a `function_call` payload. Our client application must intercept this payload, run the local function, and return the execution results back to the thread.

Here is the tool-handling logic inside our main chat loop:

```python
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # 1. Send the user's message to the conversation thread
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=user_input,
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )

    # 2. Intercept and handle local function tool calls
    input_list: ResponseInputParam = []
    for item in response.output:
        if item.type == "function_call":
            if item.name == "calculate_pizza_order":
                # Execute local python calculation
                pizza_quantity = calculate_pizza_order(**json.loads(item.arguments))
                
                # Format execution result into function call output response
                input_list.append(
                    FunctionCallOutput(
                        type="function_call_output",
                        call_id=item.call_id,
                        output=json.dumps({"pizza_quantity": pizza_quantity}),
                    )
                )

    # 3. If a tool was executed, submit the result back to continue the run
    if input_list:
        response = openai_client.responses.create(
            previous_response_id=response.id,
            input=input_list,
            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
        )    

    # 4. Output the final generated response text
    print(f"Assistant: {response.output_text}")
```

---

## 5. Live Testing & Dashboards

To place real pizza orders, follow these integration steps:

1. **Register a User Account**: Visit [Nice Dune Customer Registration Portal](https://nice-dune-07e53ec0f.2.azurestaticapps.net/) to register a customer account and generate a unique User ID GUID.
2. **Set User Details**: Add your details to your system prompt instructions or pass them directly in chat:
   ```txt
   Name: <YOUR NAME>
   UserId: <YOUR USER GUID>
   ```
3. **Monitor Orders**: Open the [Ambitious Stone Pizza Dashboard](https://ambitious-stone-0f6b9760f.2.azurestaticapps.net/) to watch your orders propagate through the system in real-time as your agent calls the MCP tools!