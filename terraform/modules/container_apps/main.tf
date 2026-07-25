# Azure Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                = var.environment_name
  location            = var.location
  resource_group_name = var.resource_group_name
  
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  tags = var.tags
}

# User-assigned managed identity for the container app
resource "azurerm_user_assigned_identity" "container_app" {
  name                = "${var.environment_name}-identity"
  resource_group_name = var.resource_group_name
  location            = var.location
  
  tags = var.tags
}

# Azure Container App
resource "azurerm_container_app" "main" {
  name                         = var.container_app_name
  location                     = var.location
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Multiple"
  
  tags = var.tags
  
  # Managed identity
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.container_app.id]
  }
  
  # Ingress configuration
  ingress {
    external_enabled           = true
    target_port                = 8000
    traffic_weight {
      percentage              = 100
      latest_revision         = true
    }
    
    # Custom domain (optional)
    dynamic "custom_domain" {
      for_each = var.custom_domain_name != "" ? [var.custom_domain_name] : []
      content {
        certificate_name = var.certificate_name
        name             = custom_domain_name.value
      }
    }
  }
  
  # Secret configuration
  secret {
    name  = "openai-api-key"
    value = var.openai_api_key
  }
  
  secret {
    name  = "search-admin-key"
    value = var.search_admin_key
  }
  
  secret {
    name  = "storage-connection-string"
    value = var.storage_connection_string
  }
  
  secret {
    name  = "app-insights-connection-string"
    value = var.app_insights_connection_string
  }
  
  # Container configuration
  container {
    name   = "ai-api"
    image  = var.container_image
    cpu    = var.cpu
    memory = var.memory
    
    # Environment variables
    env {
      name  = "AZURE_OPENAI_ENDPOINT"
      value = var.openai_endpoint
    }
    
    env {
      name  = "AZURE_OPENAI_API_VERSION"
      value = "2024-02-15-preview"
    }
    
    env {
      name  = "AZURE_OPENAI_CHAT_DEPLOYMENT"
      value = var.openai_chat_deployment
    }
    
    env {
      name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
      value = "text-embedding-ada-002"
    }
    
    env {
      name  = "AZURE_SEARCH_ENDPOINT"
      value = var.search_endpoint
    }
    
    env {
      name  = "AZURE_SEARCH_INDEX"
      value = "ai-knowledge-base"
    }
    
    env {
      name  = "AZURE_STORAGE_ACCOUNT"
      value = var.storage_account_name
    }
    
    env {
      name  = "AZURE_STORAGE_CONTAINER"
      value = "documents"
    }
    
    env {
      name  = "AZURE_KEY_VAULT_NAME"
      value = var.key_vault_name
    }
    
    env {
      name  = "AZURE_CLIENT_ID"
      value = azurerm_user_assigned_identity.container_app.client_id
    }
    
    env {
      name  = "LOG_LEVEL"
      value = "INFO"
    }
    
    env {
      name  = "APP_NAME"
      value = var.app_name
    }
    
    env {
      name  = "APP_VERSION"
      value = var.app_version
    }
    
    env {
      name  = "APP_ENVIRONMENT"
      value = var.environment
    }
    
    # Secret references
    dynamic "env" {
      for_each = var.enable_openai_secret ? [1] : []
      content {
        name        = "AZURE_OPENAI_API_KEY"
        secret_ref  = "openai-api-key"
      }
    }
    
    dynamic "env" {
      for_each = var.enable_search_secret ? [1] : []
      content {
        name        = "AZURE_SEARCH_ADMIN_KEY"
        secret_ref  = "search-admin-key"
      }
    }
    
    dynamic "env" {
      for_each = var.enable_storage_secret ? [1] : []
      content {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_ref  = "storage-connection-string"
      }
    }
    
    dynamic "env" {
      for_each = var.enable_monitoring_secret ? [1] : []
      content {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_ref  = "app-insights-connection-string"
      }
    }
    
    # Health check
    liveness_probe {
      http_get {
        path = "/health"
      }
      initial_delay_seconds = 30
      period_seconds        = 10
      timeout_seconds       = 5
      success_threshold     = 1
      failure_threshold     = 3
    }
    
    readiness_probe {
      http_get {
        path = "/health"
      }
      initial_delay_seconds = 10
      period_seconds        = 5
      timeout_seconds       = 3
      success_threshold     = 1
      failure_threshold     = 3
    }
    
    # Resource limits
    resources {
      cpu    = var.cpu
      memory = var.memory
    }
  }
  
  # Auto-scaling configuration
  dynamic "scale" {
    for_each = var.enable_auto_scaling ? [1] : []
    content {
      min_replicas = var.min_replicas
      max_replicas = var.max_replicas
      
      rules {
        name = "cpu-scaling"
        custom {
          type = "http"
          metadata = {
            concurrent_requests = "10"
          }
        }
      }
    }
  }
}

# Role assignment for managed identity to access Key Vault
resource "azurerm_role_assignment" "container_app_key_vault" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# Role assignment for managed identity to access Cognitive Search
resource "azurerm_role_assignment" "container_app_search" {
  scope                = var.search_service_id
  role_definition_name = "Search Service Contributor"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# Role assignment for managed identity to access Storage
resource "azurerm_role_assignment" "container_app_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# Role assignment for managed identity to send telemetry
resource "azurerm_role_assignment" "container_app_monitoring" {
  scope                = var.app_insights_id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}