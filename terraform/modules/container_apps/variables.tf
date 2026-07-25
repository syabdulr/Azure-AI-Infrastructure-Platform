variable "environment_name" {
  description = "Name of the Container Apps Environment"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "ID of the Log Analytics Workspace"
  type        = string
}

variable "container_app_name" {
  description = "Name of the container app"
  type        = string
}

variable "container_image" {
  description = "Container image (e.g., myregistry.azurecr.io/myapp:latest)"
  type        = string
}

variable "cpu" {
  description = "CPU cores for the container"
  type        = number
  default     = 0.5
}

variable "memory" {
  description = "Memory for the container in GB"
  type        = string
  default     = "1.0Gi"
}

variable "min_replicas" {
  description = "Minimum number of replicas"
  type        = number
  default     = 0
}

variable "max_replicas" {
  description = "Maximum number of replicas"
  type        = number
  default     = 10
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling"
  type        = bool
  default     = true
}

variable "custom_domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "certificate_name" {
  description = "Certificate name for custom domain (optional)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Service connections
variable "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
}

variable "openai_chat_deployment" {
  description = "Azure OpenAI chat deployment name"
  type        = string
  default     = "gpt-4"
}

variable "search_endpoint" {
  description = "Azure Cognitive Search endpoint"
  type        = string
}

variable "storage_account_name" {
  description = "Azure Storage account name"
  type        = string
}

variable "key_vault_name" {
  description = "Azure Key Vault name"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "azure-ai-infra-platform"
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# Secret configuration
variable "openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
}

variable "search_admin_key" {
  description = "Azure Cognitive Search admin key"
  type        = string
  sensitive   = true
}

variable "storage_connection_string" {
  description = "Azure Storage connection string"
  type        = string
  sensitive   = true
}

variable "app_insights_connection_string" {
  description = "Application Insights connection string"
  type        = string
  sensitive   = true
}

# Resource IDs for role assignments
variable "key_vault_id" {
  description = "ID of the Key Vault"
  type        = string
}

variable "search_service_id" {
  description = "ID of the Cognitive Search service"
  type        = string
}

variable "storage_account_id" {
  description = "ID of the Storage account"
  type        = string
}

variable "app_insights_id" {
  description = "ID of the Application Insights"
  type        = string
}

# Secret enablement
variable "enable_openai_secret" {
  description = "Enable OpenAI API key as secret"
  type        = bool
  default     = true
}

variable "enable_search_secret" {
  description = "Enable Search admin key as secret"
  type        = bool
  default     = true
}

variable "enable_storage_secret" {
  description = "Enable Storage connection string as secret"
  type        = bool
  default     = true
}

variable "enable_monitoring_secret" {
  description = "Enable Application Insights connection string as secret"
  type        = bool
  default     = true
}

output "container_app_url" {
  description = "URL of the container app"
  value       = "https://${azurerm_container_app.main.name}.${azurerm_container_app_environment.main.default_domain}"
}

output "managed_identity_client_id" {
  description = "Client ID of the managed identity"
  value       = azurerm_user_assigned_identity.container_app.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity"
  value       = azurerm_user_assigned_identity.container_app.principal_id
}