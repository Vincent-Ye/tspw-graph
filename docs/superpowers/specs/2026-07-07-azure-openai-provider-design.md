# Azure OpenAI Provider Design

## Goal

Add Azure OpenAI as a first-class online extraction provider without changing the build workspace flow. Users should be able to select an Azure deployment through `MODEL_PROFILES_JSON`, upload a TXT file, and run the existing extraction pipeline.

## Design

Add a separate provider kind, `azure-openai`, rather than overloading `openai-compatible`.

Azure OpenAI uses a different REST shape from OpenAI-compatible endpoints:

- URL: `{base_url}/openai/deployments/{deployment}/chat/completions?api-version={api_version}`
- Authentication header: `api-key: <secret>`
- Deployment name: stored in the existing `model` field
- API version: stored in a new optional `api_version` profile field, defaulting to `2024-06-01`

The request body remains aligned with the existing extraction contract: chat messages plus JSON Schema structured output. Response parsing and error mapping should match the OpenAI-compatible provider so the pipeline and worker do not need special cases.

## Configuration

Example profile:

```json
{
  "id": "azure:gpt-4o-mini",
  "provider": "azure-openai",
  "base_url": "https://YOUR_RESOURCE.openai.azure.com",
  "model": "YOUR_DEPLOYMENT_NAME",
  "api_key_env": "AZURE_OPENAI_API_KEY",
  "api_version": "2024-06-01",
  "timeout_seconds": 60
}
```

## Testing

- Contract test verifies Azure URL, `api-version`, `api-key` header, deployment path, and JSON Schema request body.
- Registry test verifies `ProviderRegistry` creates `AzureOpenAIProvider`.
- Existing provider tests must continue to pass.
- Documentation and `.env.example` include Azure configuration.
