variable "project_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_connector_id" {
  type = string
}

variable "service_account_email" {
  type = string
}

variable "log_level" {
  type    = string
  default = "INFO"
}

# Backend
variable "backend_image" {
  type = string
}

variable "backend_min_instances" {
  type    = number
  default = 1
}

variable "backend_max_instances" {
  type    = number
  default = 10
}

variable "backend_cpu" {
  type    = string
  default = "2"
}

variable "backend_memory" {
  type    = string
  default = "1Gi"
}

# Frontend
variable "frontend_image" {
  type = string
}

variable "frontend_min_instances" {
  type    = number
  default = 1
}

variable "frontend_max_instances" {
  type    = number
  default = 5
}

# Database connection
variable "db_host" {
  type = string
}

variable "db_name" {
  type    = string
  default = "qlogic"
}

variable "db_user" {
  type    = string
  default = "qlogic_app"
}
