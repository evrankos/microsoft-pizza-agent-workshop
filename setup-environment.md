# Environment & Azure Setup

Before writing my agent code, I configured my development environment, provisioned my Azure resources, and deployed the base GPT model. This section details my setup process and the resources I configured (which can also be used as a step-by-step guide to reproduce my environment).

---

## 1. My Developer Environment

To run and test my agent, I established a consistent, pre-configured development environment, which can be run locally or via **GitHub Codespaces**.

### My Environment Prerequisites
- **Python**: Version `3.10` or higher (I recommend using the latest stable release; refer to the package requirements defined in [`requirements.txt`](./requirements.txt)).
- **Azure CLI**: Installed and available in my terminal path to handle cloud authentication.
- **Dependencies**: Installed from the root dependency manifest:
  ```bash
  pip install -r requirements.txt
  ```

---

## 2. Azure Resource Provisioning

To support my AI agent runs, I provisioned a Hub and Project resource in the **Microsoft AI Foundry Portal** under my Azure subscription. Here is the configuration I created:

1. **Sign in to Azure**: I logged in to the [Azure Portal](https://portal.azure.com).
2. **Navigate to AI Foundry**: Searched for **Microsoft Foundry** or Azure AI Studio in the top search bar and opened the Hub service.
3. **Hub Resource Setup**:
   - I clicked **Create a resource** in the top action bar.
   - I entered my resource details:
     - **Subscription**: Selected my active subscription.
     - **Resource Group**: Created a new group named `pizza-workshop-RG`.
     - **Resource Name**: Named it uniquely (e.g., `pizza-foundry-resource-7yud`).
     - **Region**: Selected **East US** or **Sweden Central** (where agent models are fully available).
     - **Project Name**: Entered `Pizza-Workshop`.
   - I clicked **Next** through default networking/security tabs and hit **Create**. Deployment completed in about 2 minutes.

4. **Access the Project Hub**:
   - I navigated to [ai.azure.com](https://ai.azure.com) (Microsoft AI Foundry portal).
   - Opened my newly created `Pizza-Workshop` project.
   - Verified that the new modern AI Foundry interface was toggled ON.

> [!NOTE]
> Cloud management dashboards are updated frequently by Microsoft. If the layout of the AI Foundry Portal or the Azure Portal does not match these instructions exactly, refer to the official [Azure AI Agent Service documentation](https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code?tabs=portal) for the latest user interface path maps.

---

## 3. Deploying the GPT-4o Model

The Azure AI Agent Service requires a deployed LLM endpoint within the project context. I deployed the base model as follows:

1. **Deploy Model**: In the left sidebar of the AI Foundry portal under my project, I went to **Build** > **Models** and clicked **Deploy a base model**.
2. **Choose Model**: Selected the **gpt-4o** model from the catalog list and clicked **Deploy**.
3. **Deployment Settings**: Maintained default settings, naming the deployment `gpt-4o` (to match my environment variable configuration).
4. **Test in Playground**: Typed "Hello world" in the Model Playground once active to verify structured responses.

> [!TIP]
> Model catalog lists evolve over time. If `gpt-4o` is not available in your deployed subscription region, choose any other compatible GPT model (like `gpt-4o-mini`) and match the deployment name inside your local `.env` variables.

---

## 4. Local Credentials Setup

To securely connect my local Python scripts to my Azure resources, I configured local environment variables and terminal authentication:

### Step 1: My `.env` Configuration
I created a `.env` file in the root of my project directory with my project endpoint and model configuration:

```env
PROJECT_ENDPOINT="https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project-name>"
MODEL_DEPLOYMENT_NAME="gpt-4o"    # If you have named your model something else, then use it instead of gpt-4o

# Optional: Override the live Contoso Pizza MCP server URL if redeployed
MCP_SERVER_URL="https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/sse"
```

> [!NOTE]
> Make sure there are no trailing spaces or spaces around the `=` character in the `.env` file. Replace the project endpoint URL with the actual value from your Azure AI Foundry project dashboard overview.

### Step 2: Authentication via Azure CLI
The Azure Identity SDK uses `DefaultAzureCredential` to fetch authentication tokens. I logged in using the Azure CLI:

```bash
az login --use-device-code
```

After completing the interactive login in my web browser, my local Python scripts automatically detected my credentials to sign and authenticate all requests to the AI Project Client.