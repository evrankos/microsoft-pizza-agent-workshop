# 2. Environment & Azure Setup

Before writing any agent code, you must configure your development environment, provision resources in Azure, and deploy the base model. This section details how to get everything up and running.

---

## 1. Developer Environment Configuration

We use a consistent, pre-configured development environment. You can set this up locally or run it via **GitHub Codespaces**.

### Environment Prerequisites
- **Python**: Version `3.10` or higher (we recommend using the latest stable release; refer to the package requirements defined in [`requirements.txt`](./requirements.txt)).
- **Azure CLI**: Installed and available in your terminal path.
- **Core Dependencies**: Installed via your package manager or pip using the provided dependencies manifest:
  ```bash
  pip install -r requirements.txt
  ```

---

## 2. Microsoft Azure Provisioning

To run AI agents, you need an active Azure subscription with access to the **Microsoft AI Foundry Portal**.

### Step-by-Step Resource Setup:
1. **Sign in to Azure**: Log in to the [Azure Portal](https://portal.azure.com).
2. **Navigate to AI Foundry**: Search for **Microsoft Foundry** or Azure AI Studio in the top search bar and navigate to the hub service.
3. **Create a Hub Resource**:
   - Click **Create a resource** in the top action bar.
   - Enter your resource details:
     - **Subscription**: Select the subscription provided/used for the workshop.
     - **Resource Group**: Create a new group (e.g., `pizza-workshop-RG`).
     - **Resource Name**: Give it a unique identifier (e.g., `pizza-foundry-resource-7yud`).
     - **Region**: Choose **East US** or **Sweden Central** (where model deployments are fully available).
     - **Project Name**: Enter `Pizza-Workshop`.
   - Click **Next** through default networking/security tabs and hit **Create**. Deployment takes about 1–3 minutes.

4. **Access the Project Hub**:
   - Navigate to [ai.azure.com](https://ai.azure.com) (Microsoft AI Foundry portal).
   - Locate and click your newly created `Pizza-Workshop` project.
   - Ensure the new modern AI Foundry interface is toggled ON.

> [!NOTE]
> Cloud management dashboards are updated frequently by Microsoft. If the layout of the AI Foundry Portal or the Azure Portal does not match these instructions exactly, refer to the official [Azure AI Agent Service documentation](https://learn.microsoft.com/azure/ai-studio/how-to/develop-templates) for the latest user interface path maps.

---

## 3. Deploying the GPT-4o Model

AI Agent Service leverages deployed LLM endpoints within your project context.

1. **Deploy Model**: In the left sidebar of the AI Foundry portal under your project, go to **Build** > **Models** and click **Deploy a base model**.
2. **Choose Model**: Select the **gpt-4o** model from the catalog list and click **Deploy**.
3. **Deployment Settings**: Keep the default deployment configurations, naming the deployment `gpt-4o` (or match your preferred environment variable definition).
4. **Test in Playground**: Go to the **Model Playground** once deployment is active, type "Hello world", and verify that you receive a structured response from the model.

> [!TIP]
> Model catalog lists evolve over time. If `gpt-4o` is not available in your deployed subscription region, choose any other compatible GPT model (like `gpt-4o-mini`) and match the deployment name inside your local `.env` variables.

---

## 4. Local Environment Configuration

To allow your Python code to securely authenticate and connect to your Azure resources:

### Step 1: Create a `.env` File
Create a `.env` file in the root of your project directory (the same folder containing your python scripts) and add these variables:

```env
PROJECT_ENDPOINT="https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project-name>"
MODEL_DEPLOYMENT_NAME="gpt-4o"

# Optional: Override the live Contoso Pizza MCP server URL if redeployed
MCP_SERVER_URL="https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/sse"
```

> [!NOTE]
> Make sure there are no trailing spaces or spaces around the `=` character in the `.env` file. Replace the project endpoint URL with the actual value from your Azure AI Foundry project dashboard overview.

### Step 2: Authenticate via Azure CLI
The Azure Identity SDK uses `DefaultAzureCredential` to fetch local authentication tokens. Authenticate your terminal session by executing:

```bash
az login --use-device-code
```

Follow the interactive device login flow in your browser. Once complete, your Python scripts will automatically detect your Azure identity and authenticate requests to the AI Project Client.