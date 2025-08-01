# n8n REST API Connection Requirements

## Information Needed to Connect to Your Self-Hosted n8n

To connect to your self-hosted n8n instance via REST API, I need the following information:

### 1. API Base URL
The base URL for your n8n instance. Common formats:
- **Local**: `http://localhost:5678/api/v1`
- **Docker**: `http://n8n:5678/api/v1` 
- **External**: `https://your-domain.com/api/v1`
- **Hostinger**: `https://n8n.srv928466.hstgr.cloud/api/v1` (based on your setup)

### 2. API Key
You need to create an API key in your n8n instance:
1. Log in to your n8n instance
2. Go to **Settings > n8n API**
3. Click **Create an API key**
4. Give it a label (e.g., "Claude Integration")
5. Set expiration (or leave blank for no expiration)
6. Copy the generated API key

### 3. Authentication Header
The API key must be sent as a header:
- Header name: `X-N8N-API-KEY`
- Header value: Your API key

## Available API Endpoints

Once connected, I can help you with:

### Workflow Management
- **GET** `/workflows` - List all workflows
- **GET** `/workflows/{id}` - Get specific workflow
- **POST** `/workflows` - Create new workflow
- **PUT** `/workflows/{id}` - Update workflow
- **DELETE** `/workflows/{id}` - Delete workflow
- **POST** `/workflows/{id}/activate` - Activate workflow
- **POST** `/workflows/{id}/deactivate` - Deactivate workflow

### Execution Management
- **GET** `/executions` - List executions
- **GET** `/executions/{id}` - Get execution details
- **POST** `/workflows/{id}/run` - Execute workflow
- **DELETE** `/executions/{id}` - Delete execution

### Credentials Management
- **GET** `/credentials` - List credentials
- **POST** `/credentials` - Create credentials
- **GET** `/credentials/{id}` - Get credential details
- **DELETE** `/credentials/{id}` - Delete credentials

### Node Information
- **GET** `/node-types` - Get available node types
- **GET** `/credentials/schema/{credentialType}` - Get credential schema

## Example API Request Format

```bash
curl -X GET \
  'https://your-n8n-instance.com/api/v1/workflows' \
  -H 'X-N8N-API-KEY: your-api-key-here' \
  -H 'Content-Type: application/json'
```

## What I Can Do Once Connected

1. **Create and manage workflows programmatically**
   - Build complete workflows from JSON definitions
   - Update existing workflows
   - Activate/deactivate workflows

2. **Execute workflows**
   - Trigger workflow executions
   - Pass data to workflow executions
   - Monitor execution status

3. **Manage credentials**
   - List available credentials
   - Create new credentials (with limitations)

4. **Query workflow data**
   - Get execution history
   - Analyze workflow performance
   - Debug failed executions

5. **Build complex automations**
   - Create Graph RAG workflows for SpyroSolutions
   - Set up data ingestion pipelines
   - Configure monitoring workflows

## Security Considerations

1. **API Key Security**
   - Store the API key securely
   - Don't share it in public repositories
   - Consider using environment variables

2. **Access Scope**
   - Non-enterprise API keys have full access
   - Enterprise instances can limit scopes

3. **Network Security**
   - Use HTTPS for external connections
   - Consider IP whitelisting if available

## Next Steps

Please provide:
1. Your n8n instance URL (e.g., `https://n8n.srv928466.hstgr.cloud`)
2. An API key created from your n8n settings
3. Any specific workflows or operations you'd like me to help with

With this information, I can directly interact with your n8n instance to create and manage workflows for the SpyroSolutions Graph RAG implementation.