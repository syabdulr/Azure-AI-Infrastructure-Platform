# Azure Key Vault
resource "azurerm_key_vault" "main" {
  name                       = var.key_vault_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = var.sku_name
  soft_delete_retention_days = var.soft_delete_retention_days
  enable_purge_protection    = var.enable_purge_protection
  
  tags = var.tags
  
  # Access policy for current user
  dynamic "access_policy" {
    for_each = var.admin_object_ids
    content {
      tenant_id = var.tenant_id
      object_id = access_policy.value
      
      secret_permissions = [
        "Get",
        "List",
        "Set",
        "Delete",
        "Purge",
        "Recover",
      ]
      
      certificate_permissions = [
        "Get",
        "List",
        "Create",
        "Import",
        "Delete",
        "Purge",
        "Recover",
      ]
      
      key_permissions = [
        "Get",
        "List",
        "Create",
        "Import",
        "Delete",
        "Purge",
        "Recover",
      ]
    }
  }
  
  # Access policy for managed identity
  dynamic "access_policy" {
    for_each = var.managed_identity_principal_ids != null ? [1] : []
    content {
      tenant_id = var.tenant_id
      object_id = var.managed_identity_principal_ids
      
      secret_permissions = [
        "Get",
        "List",
      ]
      
      certificate_permissions = [
        "Get",
        "List",
      ]
      
      key_permissions = [
        "Get",
        "List",
      ]
    }
  }
  
  # Network rules
  network_acls {
    default_action             = "Allow"
    bypass                     = "AzureServices"
    ip_rules                   = var.ip_rules
    virtual_network_subnet_ids = var.virtual_network_subnet_ids
  }
  
  # Enable Azure RBAC for authorization
  enable_rbac_authorization = var.enable_rbac_authorization
}

# Store managed identity client ID (for use by application)
resource "azurerm_key_vault_secret" "managed_identity_client_id" {
  count       = var.managed_identity_client_id != "" ? 1 : 0
  name         = "managed-identity-client-id"
  value        = var.managed_identity_client_id
  key_vault_id = azurerm_key_vault.main.id
}

# Store Application Insights instrumentation key
resource "azurerm_key_vault_secret" "app_insights_instrumentation_key" {
  count       = var.app_insights_instrumentation_key != "" ? 1 : 0
  name         = "app-insights-instrumentation-key"
  value        = var.app_insights_instrumentation_key
  key_vault_id = azurerm_key_vault.main.id
}