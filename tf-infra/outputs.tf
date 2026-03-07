output "environment_context" {
  value = "Currently viewing the ${terraform.workspace} environment"
}

output "database_url" {
  value = "https://${supabase_project.finance_db.id}.supabase.co"
}

output "app_url" {
  value = render_web_service.finance_app.url
}