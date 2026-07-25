variable "storage_account_name" {
  description = "Name of the storage account"
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

variable "account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.account_tier)
    error_message = "Storage account tier must be Standard or Premium."
  }
}

variable "account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.account_replication_type)
    error_message = "Replication type must be LRS, GRS, RAGRS, ZRS, GZRS, or RAGZRS."
  }
}

variable "access_tier" {
  description = "Storage access tier"
  type        = string
  default     = "Hot"
  validation {
    condition     = contains(["Hot", "Cool", "Archive"], var.access_tier)
    error_message = "Access tier must be Hot, Cool, or Archive."
  }
}

variable "enable_hierarchical_namespace" {
  description = "Enable hierarchical namespace (ADLS Gen2)"
  type        = bool
  default     = true
}

variable "allow_shared_key_access" {
  description = "Allow shared key access"
  type        = bool
  default     = true
}

variable "public_network_access_enabled" {
  description = "Enable public network access"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "network_rules_enabled" {
  description = "Enable network rules"
  type        = bool
  default     = false
}

variable "default_network_action" {
  description = "Default network action"
  type        = string
  default     = "Allow"
}

variable "bypass" {
  description = "Bypass for network rules"
  type        = string
  default     = "AzureServices"
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

variable "cors_rules" {
  description = "CORS rules for blob storage"
  type = object({
    allowed_headers    = list(string)
    allowed_methods    = list(string)
    allowed_origins    = list(string)
    exposed_headers    = list(string)
    max_age_in_seconds = number
  })
  default = null
}

variable "delete_retention_days" {
  description = "Blob delete retention days"
  type        = number
  default     = 30
}

variable "container_delete_retention_days" {
  description = "Container delete retention days"
  type        = number
  default     = 7
}

variable "enable_static_website" {
  description = "Enable static website hosting"
  type        = bool
  default     = false
}

variable "index_document" {
  description = "Index document for static website"
  type        = string
  default     = "index.html"
}

variable "error_404_document" {
  description = "Error 404 document for static website"
  type        = string
  default     = "404.html"
}

variable "customer_managed_key" {
  description = "Customer-managed encryption key configuration"
  type = object({
    key_vault_key_id          = string
    user_assigned_identity_id = string
  })
  default = null
}

variable "key_vault_id" {
  description = "ID of the Key Vault to store connection string"
  type        = string
}

variable "blob_delete_after_days" {
  description = "Days after which blobs are automatically deleted"
  type        = number
  default     = 90
}

variable "snapshot_delete_after_days" {
  description = "Days after which snapshots are automatically deleted"
  type        = number
  default     = 7
}

output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.main.id
}

output "storage_primary_endpoint" {
  description = "Primary endpoint of the storage account"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "storage_connection_string_id" {
  description = "ID of the Key Vault secret containing the connection string"
  value       = azurerm_key_vault_secret.storage_connection_string.id
}