variable "openai_service_name" {
  description = "Name of the Azure OpenAI Service"
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

variable "sku_name" {
  description = "Azure OpenAI SKU name (e.g., S0)"
  type        = string
  default     = "S0"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "chat_deployment_name" {
  description = "Name of the chat deployment (e.g., gpt-4)"
  type        = string
  default     = "gpt-4"
}

variable "chat_model_name" {
  description = "Name of the chat model (e.g., gpt-4)"
  type        = string
  default     = "gpt-4"
}

variable "chat_model_version" {
  description = "Version of the chat model"
  type        = string
  default     = "0613"
}

variable "chat_capacity" {
  description = "Capacity for the chat deployment"
  type        = number
  default     = 10
}

variable "embedding_deployment_name" {
  description = "Name of the embedding deployment"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "embedding_model_name" {
  description = "Name of the embedding model"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "embedding_model_version" {
  description = "Version of the embedding model"
  type        = string
  default     = "1"
}

variable "embedding_capacity" {
  description = "Capacity for the embedding deployment"
  type        = number
  default     = 10
}

variable "key_vault_id" {
  description = "ID of the Key Vault to store API key"
  type        = string
}

output "openai_endpoint" {
  description = "Endpoint of the Azure OpenAI Service"
  value       = azurerm_cognitive_account.main.endpoint
}

output "openai_api_key_id" {
  description = "ID of the Key Vault secret containing the API key"
  value       = azurerm_key_vault_secret.openai_api_key.id
}