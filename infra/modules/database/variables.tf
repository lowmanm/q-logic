variable "project_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_vpc_connection" {
  description = "Dependency on VPC peering connection"
  type        = string
}

variable "db_tier" {
  type    = string
  default = "db-custom-2-7680"
}

variable "db_name" {
  type    = string
  default = "qlogic"
}

variable "db_user" {
  type    = string
  default = "qlogic_app"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "disk_size_gb" {
  type    = number
  default = 20
}

variable "high_availability" {
  type    = bool
  default = false
}

variable "deletion_protection" {
  type    = bool
  default = true
}
