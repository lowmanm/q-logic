terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    prefix = "terraform/state/prod"
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
  prefix = "qlogic-prod"
}

# ── Networking ────────────────────────────────────────────────
module "networking" {
  source         = "../../modules/networking"
  project_prefix = local.prefix
  region         = var.region
}

# ── Database ──────────────────────────────────────────────────
module "database" {
  source                 = "../../modules/database"
  project_prefix         = local.prefix
  region                 = var.region
  vpc_id                 = module.networking.vpc_id
  private_vpc_connection = module.networking.private_vpc_connection
  db_password            = var.db_password
  high_availability      = true
  db_tier                = "db-custom-2-7680"
}

# ── Secrets ───────────────────────────────────────────────────
module "secrets" {
  source                = "../../modules/secrets"
  service_account_email = var.cloud_run_sa_email
}

# ── Artifact Registry ────────────────────────────────────────
module "registry" {
  source = "../../modules/registry"
  region = var.region
}

# ── Compute (Cloud Run) ──────────────────────────────────────
module "compute" {
  source                = "../../modules/compute"
  project_prefix        = local.prefix
  region                = var.region
  environment           = "production"
  vpc_connector_id      = module.networking.vpc_connector_id
  service_account_email = var.cloud_run_sa_email
  backend_image         = "${module.registry.repository_url}/backend:latest"
  frontend_image        = "${module.registry.repository_url}/frontend:latest"
  db_host               = module.database.private_ip
  db_name               = module.database.database_name
  backend_min_instances = 1
  backend_max_instances = 10
}

# ── Monitoring ────────────────────────────────────────────────
module "monitoring" {
  source                = "../../modules/monitoring"
  project_prefix        = local.prefix
  project_id            = var.project_id
  backend_host          = trimprefix(module.compute.backend_url, "https://")
  notification_channels = var.notification_channels
}
