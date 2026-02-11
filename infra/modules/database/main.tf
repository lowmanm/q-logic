resource "google_sql_database_instance" "main" {
  name             = "${var.project_prefix}-db"
  database_version = "POSTGRES_16"
  region           = var.region

  depends_on = [var.private_vpc_connection]

  settings {
    tier              = var.db_tier
    availability_type = var.high_availability ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = var.disk_size_gb

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 3
      update_track = "stable"
    }

    database_flags {
      name  = "max_connections"
      value = "200"
    }
  }

  deletion_protection = var.deletion_protection
}

resource "google_sql_database" "app" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = var.db_password
}
