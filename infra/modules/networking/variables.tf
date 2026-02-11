variable "project_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR range for the private subnet"
  type        = string
  default     = "10.0.0.0/20"
}
