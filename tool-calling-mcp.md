# Tools & MCP Integration

In this final chapter, I document how I extended **Contoso PizzaBot**'s reasoning capabilities by enabling it to perform deterministic actions. I accomplished this through two methods:
1. **Custom Function Tools**: Executing local Python functions (for pizza quantity estimations).
2. **Model Context Protocol (MCP) Tools**: Connecting the agent over Server-Sent Events (SSE) to a live backend ordering system.

---

## 1. Custom Function Tools

While LLMs excel at language comprehension, they are not reliable for exact calculations. I offload order sizing math to a local Python function wrapped in a structured schema.

### Defining the Tool Schema
In [`agent.py`](https://github.com/evrankos/microsoft-pizza-agent-workshop/blob/main/agent.py#L25-L41), I define a strict parameters schema for the pizza calculator tool:

```python
func_tool = FunctionTool(
    name="calculate_pizza_order",
    parameters={
        "type": "object",
        "properties": {
            "adults": {
                "type": "integer",
                "description": "Number of adults eating pizza. Must be 0 or greater.",
            },
            "children": {
                "type": "integer",
                "description": "Number of children eating pizza. Must be 0 or greater.",
            },
            "size": {
                "type": "string",
                "enum": ["Personal", "Small", "Medium", "Large", "X-Large"],
                "description": "The pizza size to order.",
            },
        },
        "required": ["adults", "children", "size"],
        "additionalProperties": False,
    },
    description=(
        "Calculate how many pizzas are needed based on the number of "
        "adults, children, and pizza size."
    ),
    strict=True,
)
```

### Implementing the Local Function
The underlying logic is a deterministic Python function. It calculates the required pizzas assuming each pizza feeds 2 people (rounding up):

```python
SIZE_CAPACITY = {
    "Personal": 1.0,
    "Small": 1.5,
    "Medium": 2.0,
    "Large": 2.5,
    "X-Large": 3.0,
}

def calculate_pizza_order(
    adults: int,
    children: int,
    size: str,
) -> str:
    """Calculate the number of pizzas needed for a group.

    Children are counted as 0.5 adult-equivalents.

    Args:
        adults: Number of adults.
        children: Number of children.
        size: Pizza size: Personal, Small, Medium, Large, or X-Large.

    Returns:
        A message indicating how many pizzas to order.
    """
    if adults < 0 or children < 0:
        raise ValueError("Adults and children cannot be negative.")

    if size not in SIZE_CAPACITY:
        raise ValueError(
            f"Invalid pizza size: {size}. "
            f"Choose from {', '.join(SIZE_CAPACITY)}."
        )

    adult_equivalents = adults + (children * 0.5)
    pizzas = max(1, int(
        -(-adult_equivalents // SIZE_CAPACITY[size])
    ))

    return (
        f"For {adults} adults and {children} children, "
        f"order {pizzas} {size} pizza(s)."
    )
```

---

## 2. Model Context Protocol (MCP) Integration

The **Model Context Protocol (MCP)** is an open standard that enables models to connect to external systems seamlessly. Rather than writing custom SDK connectors for every database or API, you connect to an MCP server, which dynamically registers its available tools to the agent.

I connect to the Contoso Pizza backend MCP server deployed on Azure Container Apps, using an environment variable override if available:

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

The agent's toolset combines my RAG vector store, local function tool, and the live MCP connection:

```python
# Assemble all tools
toolset: list[Tool] = []
toolset.append(FileSearchTool(vector_store_ids=[vector_store.id]))  # RAG
toolset.append(func_tool)                                          # Function Calling
toolset.append(mcpTool)                                            # MCP Integration

# Create the agent version with the combined toolset
agent = project_client.agents.create_version(
    agent_name="evrankos-pizza-guy",    # Change it to your own agent name
    definition=PromptAgentDefinition(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        instructions=CONTOSO_AGENT_INSTRUCTIONS,
        tools=toolset,
    ),
)
```

---

## 4. Handling Tool Execution in the Conversation Loop

When the agent decides to invoke a function tool, it returns a `function_call` payload. My client application must intercept this payload, run the local function, and return the execution results back to the thread.

Here is the tool-handling logic inside my main chat loop:

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

## 5. Live Testing & Integration Results

During the Microsoft OpenHack workshop, the organizers provided dedicated web applications within the virtual machine (VM) sandbox environment to test and display the challenge results:
1. **Customer Registration Portal**: Used to register a mock user profile and generate a unique customer `UserID` GUID.
2. **Real-Time Pizza Dashboard**: Used to monitor the order pipeline, showcasing incoming orders and processing statuses in real time.

Because these portals were hosted inside the isolated workshop VM environment, they are not publicly accessible outside that sandbox. However, by supplying the registered `UserID` and customer credentials to my agent within the VM, I successfully demonstrated full end-to-end execution:
* **Placing Real-Time Orders**: The agent parsed my topping preferences and size guidelines, resolved local quantity estimations, and invoked the `create_order` tool via the MCP server to send the order to the kitchen.
* **Modifying Orders**: I was able to dynamically modify topping requests and quantities mid-conversation through the agent.
* **Cancellations**: The agent validated my customer profile and invoked order cancellation APIs via the MCP backend.

The entire lifecycle—from store discovery and order size planning to checkout and cancellation—was executed **purely by chatting with the AI agent I created**, showcasing the seamless capabilities of a RAG-grounded, tool-enabled assistant!

---

## 6. Real-World Production Use Cases

This combined architecture (RAG + Function Calling + MCP) serves as a production-ready template for several enterprise scenarios:
* **Automated E-Commerce & Retail Checkout**: The combination of system guardrails, local validation functions, and backend MCP tools can be adapted for any retail business (e.g., flower shops, ticket bookings, groceries) to handle inventory, ordering, and user confirmation.
* **Customer Support & Service Desks**: Using RAG to query company policies, product FAQs, or store directories combined with function tools that trigger ticketing or system modifications (e.g., resetting passwords, updating profiles).
* **Unified Microservices Agent Orchestration**: Standardizing tool bindings through the Model Context Protocol (MCP) enables enterprises to build a catalog of shared capabilities (database queries, ERP updates) that any agent can discover and invoke without custom SDK integrations.