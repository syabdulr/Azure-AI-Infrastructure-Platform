# Azure Provider Configuration
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  
  # Configuration is loaded from environment variables or .tfvars files
  # Variables: AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
  # Can also use managed identity authentication
  
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

# Allow authentication via managed identity when client_id/client_secret are not provided
provider "azurerm" {
  alias = "managed_identity"
  features {}
  
  use_msi = true
  
  # Fallback to service principal authentication if MSI fails
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  
  dynamic "client_id" {
    for_each = var.client_id != "" ? [var.client_id] : []
    content {
      value = client_id.value
    }
  }
  
  dynamic "client_secret" {
    for_each = var.client_secret != "" ? [var.client_secret] : []
    content {
      value = client_secret.value
    }
  }
}