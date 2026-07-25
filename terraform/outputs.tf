# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

# Azure OpenAI Service
output "openai_service_name" {
  description = "Name of the Azure OpenAI Service"
  value       = local.openai_service_name
}

output "openai_endpoint" {
  description = "Endpoint of the Azure OpenAI Service"
  value       = "https://${local.openai_service_name}.openai.azure.com/"
}

output "openai_api_key" {
  description = "API key for the Azure OpenAI Service (stored in Key Vault)"
  value       = azurerm_key_vault_secret.openai_api_key_id
  sensitive   = true
}

# Azure Cognitive Search
output "search_service_name" {
  description = "Name of the Azure Cognitive Search Service"
  value       = local.search_service_name
}

output "search_endpoint" {
  description = "Endpoint of the Azure Cognitive Search Service"
  value       = "https://${local.search_service_name}.search.windows.net"
}

output "search_admin_key" {
  description = "Admin key for the Azure Cognitive Search Service (stored in Key Vault)"
  value       = azurerm_key_vault_secret.search_admin_key_id
  sensitive   = true
}

# Azure Storage Account
output "storage_account_name" {
  description = "Name of the Azure Storage Account"
  value       = local.storage_account_name
}

output "storage_account_primary_connection_string" {
  description = "Primary connection string for the Storage Account (stored in Key Vault)"
  value       = azurerm_key_vault_secret.storage_connection_string_id
  sensitive   = true
}

output "storage_container_name" {
  description = "Name of the blob storage container"
  value       = "documents"
}

# Azure Key Vault
output "key_vault_name" {
  description = "Name of the Azure Key Vault"
  value       = local.key_vault_name
}

output "key_vault_uri" {
  description = "URI of the Azure Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# Azure Container Apps
output "container_apps_environment_name" {
  description = "Name of the Azure Container Apps Environment"
  value       = local.container_apps_environment
}

output "container_app_default_domain" {
  description = "Default domain for the Container Apps Environment"
  value       = azurerm_container_app_environment.main.default_domain
}

output "container_app_url" {
  description = "URL of the deployed container app"
  value       = "https://${azurerm_container_app.main.name}.${azurerm_container_app_environment.main.default_domain}"
}

# Azure Monitor
output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics Workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics Workspace"
  value       = local.log_analytics_workspace_name
}

output "application_insights_id" {
  description = "ID of the Application Insights"
  value       = azurerm_application_insights.main.id
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights (stored in Key Vault)"
  value       = azurerm_key_vault_secret.app_insights_key_id
  sensitive   = true
}

# Application Gateway
output "application_gateway_name" {
  description = "Name of the Application Gateway"
  value       = local.application_gateway_name
}

output "application_gateway_public_ip" {
  description = "Public IP address of the Application Gateway"
  value       = azurerm_public_ip.application_gateway.ip_address
}

output "application_gateway_dns_name" {
  description = "DNS name of the Application Gateway"
  value       = azurerm_public_ip.application_gateway.dns_name
}

# Managed Identity
output "user_assigned_identity_id" {
  description = "ID of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.main.id
}

output "user_assigned_identity_client_id" {
  description = "Client ID of the user-assigned managed identity (stored in Key Vault)"
  value       = azurerm_key_vault_secret.managed_identity_client_id_id
  sensitive   = true
}

# Environment variables for application
output "environment_variables" {
  description = "Environment variables for the application"
  value = {
    AZURE_OPENAI_RESOURCE           = local.openai_service_name
    AZURE_OPENAI_ENDPOINT           = "https://${local.openai_service_name}.openai.azure.com/"
    AZURE_OPENAI_API_VERSION        = "2024-02-15-preview"
    AZURE_OPENAI_CHAT_DEPLOYMENT    = var.openai_deployment_name
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
    AZURE_SEARCH_SERVICE            = local.search_service_name
    AZURE_SEARCH_INDEX              = "ai-knowledge-base"
    AZURE_STORAGE_ACCOUNT           = local.storage_account_name
    AZURE_STORAGE_CONTAINER         = "documents"
    AZURE_KEY_VAULT_NAME            = local.key_vault_name
    AZURE_APP_INSIGHTS_NAME         = local.app_insights_name
    LOG_LEVEL                       = "INFO"
    APP_NAME                        = var.project_name
    APP_VERSION                     = "1.0.0"
    APP_ENVIRONMENT                = var.environment
  }
}

# Connection strings
output "connection_strings" {
  description = "Connection strings for Azure services"
  value = {
    OPENAI_ENDPOINT       = "https://${local.openai_service_name}.openai.azure.com/"
    SEARCH_ENDPOINT       = "https://${local.search_service_name}.search.windows.net"
    KEY_VAULT_URI         = azurerm_key_vault.main.vault_uri
    LOG_ANALYTICS_WORKSPACE_ID = azurerm_log_analytics_workspace.main.workspace_id
  }
  sensitive = true
}

# Important notes
output "setup_instructions" {
  description = "Setup instructions for the application"
  value = <<EOT
1. Update your .env file with the connection strings above
2. Set AZURE_OPENAI_API_KEY in your environment or Key Vault
3. Set AZURE_SEARCH_ADMIN_KEY in your environment or Key Vault
4. Run: python -m pip install -r requirements.txt
5. Run: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
6. Access API documentation at: http://localhost:8000/docs
EOT
}