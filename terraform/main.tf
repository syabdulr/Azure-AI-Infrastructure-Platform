terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "terraformstateacc"
    container_name       = "tfstate"
    key                  = "azure-ai-infra-platform.tfstate"
  }
}

provider "azurerm" {
  features {}
  
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

provider "random" {
}

# Random suffix for unique resource names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  
  tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })
}

# Local variables for naming consistency
locals {
  prefix = "${var.project_name}-${var.environment}"
  
  # Resource names with random suffix
  openai_service_name         = "${local.prefix}-openai-${random_string.suffix.result}"
  search_service_name          = "${local.prefix}-search-${random_string.suffix.result}"
  storage_account_name         = "${lower(replace(local.prefix, "-", ""))}${random_string.suffix.result}"
  key_vault_name              = "${local.prefix}-kv-${random_string.suffix.result}"
  container_apps_environment  = "${local.prefix}-cae"
  application_gateway_name     = "${local.prefix}-agw"
  log_analytics_workspace_name = "${local.prefix}-logs"
  app_insights_name           = "${local.prefix}-appinsights"
  
  # Common tags
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
  })
}