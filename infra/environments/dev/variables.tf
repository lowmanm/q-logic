variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "cloud_run_sa_email" {
  type = string
}
