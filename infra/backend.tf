terraform {
  backend "gcs" {
    # Bucket name injected per-environment via -backend-config
    # Example: terraform init -backend-config="bucket=qlogic-prod-terraform-state"
    prefix = "terraform/state"
  }
}
