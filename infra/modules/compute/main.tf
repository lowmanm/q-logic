# ── Cloud Run: Backend ─────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.project_prefix}-backend"
  location = var.region

  template {
    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }
      env {
        name  = "DB_HOST"
        value = var.db_host
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_NAME"
        value = var.db_name
      }
      env {
        name  = "DB_USER"
        value = var.db_user
      }
      env {
        name  = "DB_SSL_MODE"
        value = "require"
      }
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "db-password"
            version = "latest"
          }
        }
      }
      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = "jwt-secret"
            version = "latest"
          }
        }
      }
      env {
        name = "CORS_ORIGINS"
        value_source {
          secret_key_ref {
            secret  = "cors-origins"
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
      }

      startup_probe {
        http_get {
          path = "/api/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get {
          path = "/api/health"
          port = 8000
        }
        period_seconds    = 30
        failure_threshold = 3
      }
    }

    service_account = var.service_account_email
  }
}

# ── Cloud Run: Frontend ───────────────────────────────────────
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.project_prefix}-frontend"
  location = var.region

  template {
    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 80
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }
    }
  }
}

# ── Public access ─────────────────────────────────────────────
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
