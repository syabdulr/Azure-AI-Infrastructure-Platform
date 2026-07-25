# Azure Provider Configuration
variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
  sensitive   = true
}

variable "client_id" {
  description = "Azure client ID (service principal)"
  type        = string
  sensitive   = true
}

variable "client_secret" {
  description = "Azure client secret (service principal)"
  type        = string
  sensitive   = true
}

# Resource Configuration
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "ai-infra-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "azure-ai-infra"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Creator  = "Abdul Syed"
    Role     = "AI Platform Engineer"
    Purpose  = "Azure AI Infrastructure Platform"
    CostCenter = "AI-Platform-001"
  }
}

# Azure OpenAI Configuration
variable "openai_sku_name" {
  description = "Azure OpenAI SKU name"
  type        = string
  default     = "S0"
}

variable "openai_deployment_name" {
  description = "Azure OpenAI deployment name"
  type        = string
  default     = "gpt-4"
}

variable "openai_model_name" {
  description = "Azure OpenAI model name"
  type        = string
  default     = "gpt-4"
}

variable "openai_model_version" {
  description = "Azure OpenAI model version"
  type        = string
  default     = "0613"
}

# Azure Cognitive Search Configuration
variable "search_sku" {
  description = "Azure Cognitive Search SKU"
  type        = string
  default     = "standard"
  validation {
    condition     = contains(["free", "basic", "standard", "standard2", "standard3", "storage_optimized_l1", "storage_optimized_l2"], var.search_sku)
    error_message = "Search SKU must be free, basic, standard, standard2, standard3, storage_optimized_l1, or storage_optimized_l2."
  }
}

variable "search_replica_count" {
  description = "Azure Cognitive Search replica count"
  type        = number
  default     = 1
  validation {
    condition     = var.search_replica_count >= 1 && var.search_replica_count <= 12
    error_message = "Replica count must be between 1 and 12."
  }
}

variable "search_partition_count" {
  description = "Azure Cognitive Search partition count"
  type        = number
  default     = 1
  validation {
    condition     = var.search_partition_count >= 1 && var.search_partition_count <= 12
    error_message = "Partition count must be between 1 and 12."
  }
}

# Azure Storage Configuration
variable "storage_account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.storage_account_tier)
    error_message = "Storage account tier must be Standard or Premium."
  }
}

variable "storage_account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.storage_account_replication_type)
    error_message = "Replication type must be LRS, GRS, RAGRS, ZRS, GZRS, or RAGZRS."
  }
}

# Azure Container Apps Configuration
variable "container_apps_min_replicas" {
  description = "Minimum number of replicas for container apps"
  type        = number
  default     = 0
}

variable "container_apps_max_replicas" {
  description = "Maximum number of replicas for container apps"
  type        = number
  default     = 10
}

variable "container_app_cpu" {
  description = "CPU cores for container app"
  type        = number
  default     = 0.5
}

variable "container_app_memory" {
  description = "Memory for container app in GB"
  type        = number
  default     = 1.0
}

# Azure Key Vault Configuration
variable "key_vault_sku" {
  description = "Azure Key Vault SKU"
  type        = string
  default     = "standard"
  validation {
    condition     = contains(["standard", "premium"], var.key_vault_sku)
    error_message = "Key Vault SKU must be standard or premium."
  }
}

variable "key_vault_soft_delete_retention_days" {
  description = "Key Vault soft delete retention days"
  type        = number
  default     = 90
}

# Azure Monitor Configuration
variable "log_analytics_retention_days" {
  description = "Log Analytics retention days"
  type        = number
  default     = 30
}

variable "enable_app_insights" {
  description = "Enable Application Insights"
  type        = bool
  default     = true
}

# Application Gateway Configuration
variable "application_gateway_sku" {
  description = "Application Gateway SKU"
  type        = string
  default     = "Standard_v2"
}

variable "application_gateway_capacity" {
  description = "Application Gateway capacity"
  type        = number
  default     = 2
}

# Network Configuration
variable "enable_virtual_network" {
  description = "Enable virtual network integration"
  type        = bool
  default     = true
}

variable "vnet_address_space" {
  description = "Virtual network address space"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnet_address_prefixes" {
  description = "Subnet address prefixes"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}