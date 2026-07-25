variable "key_vault_name" {
  description = "Name of the Key Vault"
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

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
}

variable "sku_name" {
  description = "Key Vault SKU"
  type        = string
  default     = "standard"
  validation {
    condition     = contains(["standard", "premium"], var.sku_name)
    error_message = "Key Vault SKU must be standard or premium."
  }
}

variable "soft_delete_retention_days" {
  description = "Soft delete retention days"
  type        = number
  default     = 90
}

variable "enable_purge_protection" {
  description = "Enable purge protection"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "admin_object_ids" {
  description = "List of admin object IDs for Key Vault access"
  type        = list(string)
  default     = []
}

variable "managed_identity_principal_ids" {
  description = "Principal ID of managed identity for access"
  type        = string
  default     = null
}

variable "ip_rules" {
  description = "List of IP rules for network ACLs"
  type        = list(string)
  default     = []
}

variable "virtual_network_subnet_ids" {
  description = "List of subnet IDs for network ACLs"
  type        = list(string)
  default     = []
}

variable "enable_rbac_authorization" {
  description = "Enable Azure RBAC for Key Vault authorization"
  type        = bool
  default     = true
}

variable "managed_identity_client_id" {
  description = "Client ID of managed identity to store"
  type        = string
  default     = ""
}

variable "app_insights_instrumentation_key" {
  description = "Application Insights instrumentation key to store"
  type        = string
  default     = ""
}

output "key_vault_id" {
  description = "ID of the Key Vault"
  value       = azurerm_key_vault.main.id
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}