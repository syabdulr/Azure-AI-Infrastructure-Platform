# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = var.log_analytics_workspace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.log_analytics_sku
  retention_in_days   = var.retention_days
  
  tags = var.tags
  
  # Daily data cap (optional)
  dynamic "daily_quota_gb" {
    for_each = var.daily_quota_gb != null ? [var.daily_quota_gb] : []
    content {
      limit_gb = daily_quota_gb.value
    }
  }
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = var.app_insights_name
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id         = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  
  # Disable IP masking for detailed debugging
  disable_ip_masking = var.disable_ip_masking
  
  tags = var.tags
}

# Application Insights Web Test (health check)
resource "azurerm_application_insights_web_test" "health" {
  count                  = var.enable_web_tests ? 1 : 0
  name                    = "health-check"
  location                = var.location
  resource_group_name     = var.resource_group_name
  application_insights_id = azurerm_application_insights.main.id
  enabled                 = true
  
  kind  = "ping"
  geo_locations = [
    "us-va-ash-azr",
    "emea-ru-msa-azr",
    "apac-jp-kaw-azr"
  ]
  
  configuration {
    url      = var.web_test_url
    ssl_cert_validation_disabled = false
  }
  
  request {
    request_headers = {
      "User-Agent" = "Application Insights Web Test"
    }
  }
}

# Application Insights Alert Rule
resource "azurerm_monitor_scheduled_query_rules_alert" "web_test_failure" {
  count                   = var.enable_web_tests ? 1 : 0
  name                    = "web-test-failure-alert"
  location                = var.location
  resource_group_name     = var.resource_group_name
  
  description             = "Alert when web test fails"
  severity                = 3
  enabled                 = true
  evaluation_frequency    = "PT5M"
  time_window             = "PT5M"
  query                   = <<-QUERY
    let threshold = 1;
    let searchConfig = dynamic(['*', '*', '*', '*']);
    let duration = 5m;
    let frequency = 5m;
    searchConfig
    | search *
    | where Timestamp > ago(duration)
    | where Name == "${azurerm_application_insights_web_test.health[0].name}"
    | summarize resultCount = count() by WebTest
    | where resultCount < threshold
  QUERY
  action {
    action_group = var.alert_action_group_id
  }
  
  trigger {
    operator  = "GreaterThan"
    threshold = 0
  }
  
  depends_on = [azurerm_application_insights_web_test.health]
}

# Custom Metrics Dashboard (example configuration)
resource "azurerm_portal_dashboard" "ai_platform" {
  name                = "${var.app_insights_name}-dashboard"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
  
  dashboard_properties = templatefile("${path.module}/dashboard_template.json", {
    app_insights_id = azurerm_application_insights.main.id
    location        = var.location
  })
}

# Store Application Insights key in Key Vault
resource "azurerm_key_vault_secret" "app_insights_instrumentation_key" {
  name         = "app-insights-instrumentation-key"
  value        = azurerm_application_insights.main.instrumentation_key
  key_vault_id = var.key_vault_id
  
  depends_on = [azurerm_application_insights.main]
}