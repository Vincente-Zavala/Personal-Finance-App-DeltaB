variable "supabase_token" {
  type      = string
  sensitive = true
}

variable "render_token" {
  type      = string
  sensitive = true
}

variable "render_owner_id" {
  type = string
}

variable "supabase_org_id" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type = string
}

variable "app_name" {
  type = string
}

variable "app_env" {
  type      = string
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "debug" {
  type      = string
  sensitive = true
}

variable "secret_key" {
  type      = string
  sensitive = true
}

variable "supabase_bucket" {
  type      = string
  sensitive = true
}

variable "supabase_public_key" {
  type      = string
  sensitive = true
}

variable "supabase_service_key" {
  type      = string
  sensitive = true
}

variable "supabase_url" {
  type      = string
  sensitive = true
}

variable "environment_id" {
  type      = string
}

variable "region" {
  type      = string
}