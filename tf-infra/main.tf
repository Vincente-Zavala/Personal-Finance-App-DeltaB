terraform {
  required_providers {
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
    render = {
      source  = "render-oss/render"
      version = "~> 1.0"
    }
  }
}

provider "supabase" {
  access_token = var.supabase_token
}

provider "render" {
  api_key  = var.render_token
  owner_id = var.render_owner_id
}

# This represents your existing Supabase project
resource "supabase_project" "finance_db" {
  name            = var.db_name
  organization_id = var.supabase_org_id
  region          = var.region
  database_password = var.db_password
  
  lifecycle {
    ignore_changes = [
      database_password,
    ]
  }
}

# This represents your existing Render web service
resource "render_web_service" "finance_app" {
  name    = var.app_name
  plan    = "free"
  region  = "oregon"
  environment_id = var.environment_id

    env_vars = {
        APP_ENV = {
            value = var.app_env
        }

        DATABASE_URL = {
            value = var.database_url
        }

        DEBUG = {
            value = var.debug
        }

        SECRET_KEY = {
            value = var.secret_key
        }

        SUPABASE_BUCKET = {
            value = var.supabase_bucket
        }

        SUPABASE_PUBLIC_KEY = {
            value = var.supabase_public_key
        }

        SUPABASE_SERVICE_KEY = {
            value = var.supabase_service_key
        }

        SUPABASE_URL = {
            value = var.supabase_url
        }    

    }

    runtime_source                = {
        native_runtime = {
            auto_deploy         = false
            auto_deploy_trigger = "off"
            branch              = "main"
            build_command       = "pip install -r requirements.txt"
            repo_url            = "https://github.com/Vincente-Zavala/Personal-Finance-App-DeltaB"
            runtime             = "python"
        }
    }
    start_command                 = "python manage.py migrate && gunicorn DeltaB.wsgi:application"
}