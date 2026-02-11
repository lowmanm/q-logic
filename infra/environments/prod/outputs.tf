output "backend_url" {
  value = module.compute.backend_url
}

output "frontend_url" {
  value = module.compute.frontend_url
}

output "db_connection_name" {
  value = module.database.connection_name
}

output "db_private_ip" {
  value     = module.database.private_ip
  sensitive = true
}
