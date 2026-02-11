resource "google_compute_network" "vpc" {
  name                    = "${var.project_prefix}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private" {
  name          = "${var.project_prefix}-private"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}

# Private Services Access for Cloud SQL
resource "google_compute_global_address" "private_ip" {
  name          = "${var.project_prefix}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]
}

# Serverless VPC Access connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "${var.project_prefix}-connector"
  region        = var.region
  subnet {
    name = google_compute_subnetwork.private.name
  }
  min_instances = 2
  max_instances = 3
}
