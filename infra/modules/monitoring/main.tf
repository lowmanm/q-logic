# ── Uptime check on /api/health ───────────────────────────────
resource "google_monitoring_uptime_check_config" "health" {
  display_name = "${var.project_prefix} Health Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/api/health"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.backend_host
    }
  }
}

# ── Alert: 5xx error rate ─────────────────────────────────────
resource "google_monitoring_alert_policy" "error_rate" {
  display_name = "${var.project_prefix} 5xx Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "5xx rate > 1%"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.01
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.notification_channels
}

# ── Alert: High latency ──────────────────────────────────────
resource "google_monitoring_alert_policy" "latency" {
  display_name = "${var.project_prefix} High Latency"
  combiner     = "OR"

  conditions {
    display_name = "p99 latency > 5s"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_latencies\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5000
      duration        = "300s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
      }
    }
  }

  notification_channels = var.notification_channels
}

# ── Alert: Cloud SQL CPU ──────────────────────────────────────
resource "google_monitoring_alert_policy" "db_cpu" {
  display_name = "${var.project_prefix} DB CPU High"
  combiner     = "OR"

  conditions {
    display_name = "Cloud SQL CPU > 80%"
    condition_threshold {
      filter          = "resource.type = \"cloudsql_database\" AND metric.type = \"cloudsql.googleapis.com/database/cpu/utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels
}
