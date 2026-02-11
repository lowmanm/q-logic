variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "db_password" {
  description = "Database password for qlogic_app user"
  type        = string
  sensitive   = true
}

variable "cloud_run_sa_email" {
  description = "Service account email for Cloud Run services"
  type        = string
}

variable "notification_channels" {
  description = "Monitoring notification channel IDs"
  type        = list(string)
  default     = []
}
