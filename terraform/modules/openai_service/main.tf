# Azure OpenAI Service
resource "azurerm_cognitive_account" "main" {
  name                = var.openai_service_name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = var.sku_name
  
  tags = var.tags
  
  # Enable custom subdomain
  custom_subdomain_name = "${var.openai_service_name}-custom"
}

# Azure OpenAI Chat Deployment (GPT-4)
resource "azurerm_cognitive_deployment" "chat" {
  name                = var.chat_deployment_name
  cognitive_account_id = azurerm_cognitive_account.main.id
  
  model {
    format  = "OpenAI"
    name    = var.chat_model_name
    version = var.chat_model_version
  }
  
  scale {
    type = "Standard"
    
    capacity = var.chat_capacity
  }
}

# Azure OpenAI Embedding Deployment (text-embedding-ada-002)
resource "azurerm_cognitive_deployment" "embedding" {
  name                = var.embedding_deployment_name
  cognitive_account_id = azurerm_cognitive_account.main.id
  
  model {
    format  = "OpenAI"
    name    = var.embedding_model_name
    version = var.embedding_model_version
  }
  
  scale {
    type = "Standard"
    
    capacity = var.embedding_capacity
  }
}

# Store API key in Key Vault
resource "azurerm_key_vault_secret" "openai_api_key" {
  name         = "openai-api-key"
  value        = azurerm_cognitive_account.main.primary_access_key
  key_vault_id = var.key_vault_id
  
  depends_on = [azurerm_cognitive_account.main]
}