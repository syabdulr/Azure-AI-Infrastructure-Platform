variable "search_service_name" {
  description = "Name of the Azure Cognitive Search service"
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
  description = "Azure Cognitive Search SKU"
  type        = string
  default     = "standard"
  validation {
    condition     = contains(["free", "basic", "standard", "standard2", "standard3", "storage_optimized_l1", "storage_optimized_l2"], var.sku_name)
    error_message = "Search SKU must be free, basic, standard, standard2, standard3, storage_optimized_l1, or storage_optimized_l2."
  }
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 12
    error_message = "Replica count must be between 1 and 12."
  }
}

variable "partition_count" {
  description = "Number of partitions"
  type        = number
  default     = 1
  validation {
    condition     = var.partition_count >= 1 && var.partition_count <= 12
    error_message = "Partition count must be between 1 and 12."
  }
}

variable "index_name" {
  description = "Name of the search index"
  type        = string
  default     = "ai-knowledge-base"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "public_network_access_enabled" {
  description = "Enable public network access"
  type        = bool
  default     = true
}

variable "local_authentication_enabled" {
  description = "Enable local authentication"
  type        = bool
  default     = false
}

variable "key_vault_id" {
  description = "ID of the Key Vault to store keys"
  type        = string
}

variable "enable_blob_indexer" {
  description = "Enable blob storage indexer"
  type        = bool
  default     = false
}

variable "storage_account_name" {
  description = "Name of the storage account for blob indexer"
  type        = string
  default     = ""
}

variable "storage_container_name" {
  description = "Name of the storage container for blob indexer"
  type        = string
  default     = "documents"
}

variable "storage_connection_string" {
  description = "Connection string for storage account"
  type        = string
  sensitive   = true
  default     = ""
}

output "search_endpoint" {
  description = "Endpoint of the Azure Cognitive Search service"
  value       = azurerm_search_service.main.endpoint
}

output "search_service_id" {
  description = "ID of the Azure Cognitive Search service"
  value       = azurerm_search_service.main.id
}

output "search_admin_key_id" {
  description = "ID of the Key Vault secret containing the admin key"
  value       = azurerm_key_vault_secret.search_admin_key.id
}

output "search_query_key_id" {
  description = "ID of the Key Vault secret containing the query key"
  value       = azurerm_key_vault_secret.search_query_key.id
}