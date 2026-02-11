resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = var.repository_name
  format        = "DOCKER"
  description   = "Q-Logic Docker images"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
}
