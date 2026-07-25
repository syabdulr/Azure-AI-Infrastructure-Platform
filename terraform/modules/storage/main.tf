# Azure Storage Account
resource "azurerm_storage_account" "main" {
  name                      = var.storage_account_name
  location                  = var.location
  resource_group_name       = var.resource_group_name
  account_tier              = var.account_tier
  account_replication_type  = var.account_replication_type
  
  # Access tier for blob data
  access_tier              = var.access_tier
  
  # Enable hierarchical namespace for data lake
  is_hns_enabled           = var.enable_hierarchical_namespace
  
  # Minimum TLS version
  min_tls_version          = "TLS1_2"
  
  # Allow shared key access (for development)
  allow_shared_key_access  = var.allow_shared_key_access
  
  # Public network access
  public_network_access_enabled = var.public_network_access_enabled
  
  # Network rules
  dynamic "network_rules" {
    for_each = var.network_rules_enabled ? [1] : []
    content {
      default_action             = var.default_network_action
      bypass                     = var.bypass
      ip_rules                   = var.ip_rules
      virtual_network_subnet_ids = var.virtual_network_subnet_ids
    }
  }
  
  # Blob storage properties
  blob_properties {
    dynamic "cors_rule" {
      for_each = var.cors_rules != null ? [var.cors_rules] : []
      content {
        allowed_headers    = cors_rule.value.allowed_headers
        allowed_methods    = cors_rule.value.allowed_methods
        allowed_origins    = cors_rule.value.allowed_origins
        exposed_headers    = cors_rule.value.exposed_headers
        max_age_in_seconds = cors_rule.value.max_age_in_seconds
      }
    }
    
    delete_retention_policy {
      days = var.delete_retention_days
    }
    
    container_delete_retention_policy {
      days = var.container_delete_retention_days
    }
  }
  
  # Static website (optional)
  dynamic "static_website" {
    for_each = var.enable_static_website ? [1] : []
    content {
      index_document     = var.index_document
      error_404_document = var.error_404_document
    }
  }
  
  tags = var.tags
  
  # Customer-managed encryption key (optional)
  dynamic "customer_managed_key" {
    for_each = var.customer_managed_key != null ? [var.customer_managed_key] : []
    content {
      key_vault_key_id          = customer_managed_key.value.key_vault_key_id
      user_assigned_identity_id = customer_managed_key.value.user_assigned_identity_id
    }
  }
}

# Storage container for documents
resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Storage container for embeddings cache
resource "azurerm_storage_container" "embeddings_cache" {
  name                  = "embeddings-cache"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Storage container for uploads
resource "azurerm_storage_container" "uploads" {
  name                  = "uploads"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Lifecycle management rules
resource "azurerm_storage_management_policy" "main" {
  storage_account_id = azurerm_storage_account.main.id
  
  rule {
    name    = "lifecycle-rule"
    enabled = true
    
    filters {
      prefix_match = ["documents/", "embeddings-cache/"]
      blob_types   = ["blockBlob"]
    }
    
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.blob_delete_after_days
      }
      
      snapshot {
        delete_after_days_since_creation_greater_than = var.snapshot_delete_after_days
      }
    }
  }
}

# Store connection string in Key Vault
resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = var.key_vault_id
  
  depends_on = [azurerm_storage_account.main]
}