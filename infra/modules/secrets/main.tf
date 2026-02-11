resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(var.secret_names)
  secret_id = each.value

  replication {
    auto {}
  }
}

# Grant the Cloud Run service account access to all secrets
resource "google_secret_manager_secret_iam_member" "accessor" {
  for_each  = toset(var.secret_names)
  secret_id = google_secret_manager_secret.secrets[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}
