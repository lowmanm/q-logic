variable "project_prefix" {
  type = string
}

variable "project_id" {
  type = string
}

variable "backend_host" {
  description = "Hostname of the backend Cloud Run service"
  type        = string
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}
