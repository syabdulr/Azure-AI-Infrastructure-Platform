variable "log_analytics_workspace_name" {
  description = "Name of the Log Analytics Workspace"
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

variable "log_analytics_sku" {
  description = "SKU of the Log Analytics Workspace"
  type        = string
  default     = "PerGB2018"
}

variable "retention_days" {
  description = "Retention period in days for logs"
  type        = number
  default     = 30
  validation {
    condition     = var.retention_days >= 7 && var.retention_days <= 730
    error_message = "Retention must be between 7 and 730 days."
  }
}

variable "daily_quota_gb" {
  description = "Daily data quota in GB (null for unlimited)"
  type        = number
  default     = null
}

variable "app_insights_name" {
  description = "Name of Application Insights"
  type        = string
}

variable "disable_ip_masking" {
  description = "Disable IP masking in Application Insights"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "enable_web_tests" {
  description = "Enable web tests"
  type        = bool
  default     = true
}

variable "web_test_url" {
  description = "URL for web test health checks"
  type        = string
  default     = ""
}

variable "alert_action_group_id" {
  description = "Action group ID for alerts"
  type        = string
  default     = ""
}

variable "key_vault_id" {
  description = "ID of the Key Vault to store Application Insights key"
  type        = string
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics Workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics Workspace"
  value       = azurerm_log_analytics_workspace.main.name
}

output "application_insights_id" {
  description = "ID of Application Insights"
  value       = azurerm_application_insights.main.id
}

output "application_insights_instrumentation_key_id" {
  description = "ID of the Key Vault secret containing the instrumentation key"
  value       = azurerm_key_vault_secret.app_insights_instrumentation_key.id
}

output "dashboard_id" {
  description = "ID of the Azure dashboard"
  value       = azurerm_portal_dashboard.ai_platform.id
}