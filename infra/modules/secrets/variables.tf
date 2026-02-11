variable "secret_names" {
  description = "List of secret names to create in Secret Manager"
  type        = list(string)
  default     = ["db-password", "db-host", "jwt-secret", "cors-origins"]
}

variable "service_account_email" {
  description = "Service account to grant secret access to"
  type        = string
}
