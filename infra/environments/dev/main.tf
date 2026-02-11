terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    prefix = "terraform/state/dev"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  prefix = "qlogic-dev"
}

module "networking" {
  source         = "../../modules/networking"
  project_prefix = local.prefix
  region         = var.region
}

module "database" {
  source                 = "../../modules/database"
  project_prefix         = local.prefix
  region                 = var.region
  vpc_id                 = module.networking.vpc_id
  private_vpc_connection = module.networking.private_vpc_connection
  db_password            = var.db_password
  high_availability      = false
  db_tier                = "db-f1-micro"
  deletion_protection    = false
}

module "registry" {
  source = "../../modules/registry"
  region = var.region
}

module "compute" {
  source                = "../../modules/compute"
  project_prefix        = local.prefix
  region                = var.region
  environment           = "development"
  log_level             = "DEBUG"
  vpc_connector_id      = module.networking.vpc_connector_id
  service_account_email = var.cloud_run_sa_email
  backend_image         = "${module.registry.repository_url}/backend:latest"
  frontend_image        = "${module.registry.repository_url}/frontend:latest"
  db_host               = module.database.private_ip
  db_name               = module.database.database_name
  backend_min_instances = 0
  backend_max_instances = 2
  backend_cpu           = "1"
  backend_memory        = "512Mi"
}
