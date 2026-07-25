# Azure Cognitive Search Service
resource "azurerm_search_service" "main" {
  name                = var.search_service_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku_name
  
  # Public network access configuration
  public_network_access_enabled = var.public_network_access_enabled
  
  # Disable local authentication
  local_authentication_enabled = var.local_authentication_enabled
  
  tags = var.tags
  
  # Replica and partition count
  replica_count = var.replica_count
  partition_count = var.partition_count
  
  # Identity for accessing other resources
  identity {
    type = "SystemAssigned"
  }
}

# Create search index for AI knowledge base
resource "azurerm_search_index" "ai_knowledge_base" {
  name                = var.index_name
  search_service_name = azurerm_search_service.main.name
  resource_group_name = var.resource_group_name
  
  # Index fields
  fields {
    name        = "id"
    type        = "Edm.String"
    key         = true
    searchable  = true
    filterable  = true
    sortable    = true
    facetable   = false
  }
  
  fields {
    name        = "content"
    type        = "Edm.String"
    searchable  = true
    filterable  = false
    sortable    = false
    facetable   = false
  }
  
  fields {
    name        = "title"
    type        = "Edm.String"
    searchable  = true
    filterable  = true
    sortable    = true
    facetable   = false
  }
  
  fields {
    name        = "source"
    type        = "Edm.String"
    searchable  = true
    filterable  = true
    sortable    = true
    facetable   = false
  }
  
  fields {
    name        = "metadata"
    type        = "Edm.String"
    searchable  = true
    filterable  = false
    sortable    = false
    facetable   = false
  }
  
  fields {
    name        = "created_at"
    type        = "Edm.DateTimeOffset"
    searchable  = false
    filterable  = true
    sortable    = true
    facetable   = false
  }
  
  fields {
    name        = "updated_at"
    type        = "Edm.DateTimeOffset"
    searchable  = false
    filterable  = true
    sortable    = true
    facetable   = false
  }
  
  # Vector search configuration
  vector_search {
    algorithm_configuration {
      name  = "my-vector-config"
      kind  = "hnsw"
      hnsw_parameters {
        m               = 4
        ef_construction = 400
        ef_search       = 500
        metric          = "cosine"
      }
    }
  }
  
  # Semantic search configuration
  semantic_search {
    default_configuration_name = "default-semantic-config"
    configurations {
      name = "default-semantic-config"
      prioritized_fields {
        prioritized_content_fields {
          field_name = "content"
        }
        title_field {
          field_name = "title"
        }
        prioritized_keywords_fields {
          field_name = "title"
        }
      }
    }
  }
  
  # Scoring profiles for relevance
  scoring_profiles {
    name = "boost-titles"
    text_weights {
      weights = {
        title   = 3.0
        content = 1.0
        source  = 1.0
      }
    }
  }
  
  # Default scoring profile
  default_scoring_profile = "boost-titles"
}

# Indexer for automated document ingestion (optional)
resource "azurerm_search_data_source" "blob_storage" {
  count               = var.enable_blob_indexer ? 1 : 0
  name                = "blob-storage-datasource"
  search_service_name = azurerm_search_service.main.name
  resource_group_name = var.resource_group_name
  type                = "azureblob"
  
  azure_blob_storage {
    storage_account_name = var.storage_account_name
    container_name        = var.storage_container_name
    connection_string     = var.storage_connection_string
  }
  
  depends_on = [azurerm_search_service.main]
}

# Store admin key in Key Vault
resource "azurerm_key_vault_secret" "search_admin_key" {
  name         = "search-admin-key"
  value        = azurerm_search_service.main.primary_access_key
  key_vault_id = var.key_vault_id
  
  depends_on = [azurerm_search_service.main]
}

# Store query key in Key Vault (for client applications)
resource "azurerm_search_query_key" "main" {
  name                = "query-key"
  search_service_name = azurerm_search_service.main.name
  resource_group_name = var.resource_group_name
}

resource "azurerm_key_vault_secret" "search_query_key" {
  name         = "search-query-key"
  value        = azurerm_search_query_key.main.key
  key_vault_id = var.key_vault_id
  
  depends_on = [azurerm_search_service.main]
}