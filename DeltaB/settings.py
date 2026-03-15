"""
Django settings for Delta project.

"""

from pathlib import Path
import dj_database_url
import os
import logging
import time
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)
ENV = os.environ.get("APP_ENV", "staging")
SOURCE_TOKEN = os.environ.get("SOURCE_TOKEN")

if ENV != 'production':
    load_dotenv(os.path.join(BASE_DIR, ".env"))

LOGGING_LEVEL = logging.INFO if ENV != "production" else logging.INFO


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": jsonlogger.JsonFormatter,
            "fmt": "%(asctime)s %(levelname)s %(name)s %(module)s %(lineno)d %(message)s",
        },
    },
    "handlers": {
        'logtail': {
            'class': 'logtail.LogtailHandler',
            'source_token': SOURCE_TOKEN,
            'host': 'https://s1671097.eu-nbg-2.betterstackdata.com',
            "formatter": "json",
            "level": "INFO",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": LOGGING_LEVEL,
        },
    },
    "root": {
        "handlers": ["console", "logtail"],
        "level": LOGGING_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "logtail"],
            "level": LOGGING_LEVEL,
            "propagate": True,
        },
    },
}


class Config:
    """
    Centralized configuration management.
    Handles environment variables and validation.
    """
    ENV = os.getenv("APP_ENV", "staging")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_PUBLIC_KEY = os.getenv("SUPABASE_PUBLIC_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

    @classmethod
    def validate(cls):
        """Ensures all critical environment variables are set before the app starts."""
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "SUPABASE_URL",
            "SUPABASE_PUBLIC_KEY",
            "SUPABASE_SERVICE_KEY",
        ]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Critical Configuration Missing: {', '.join(missing)}")


# Validate configuration
Config.validate()


SECRET_KEY = Config.SECRET_KEY
DATABASE_URL = Config.DATABASE_URL
SUPABASE_URL = Config.SUPABASE_URL
SUPABASE_PUBLIC_KEY = Config.SUPABASE_PUBLIC_KEY
SUPABASE_SERVICE_KEY = Config.SUPABASE_SERVICE_KEY
SUPABASE_BUCKET = Config.SUPABASE_BUCKET
DEBUG = Config.DEBUG


DEFAULT_FILE_STORAGE = "DeltaBApp.supabaseupload.SupabaseStorage"
SUPABASE_USE_SECURE_URLS = True


ALLOWED_HOSTS = [
    "deltab.onrender.com",
    "deltab-staging.onrender.com",
    "127.0.0.1",
    "localhost",
    "0.0.0.0"
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://deltab.onrender.com",
    "https://deltab-staging.onrender.com",
]


REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "DeltaBApp",
]

LOGIN_URL = 'signin'
LOGIN_REDIRECT_URL = 'overview'
AUTH_USER_MODEL = 'DeltaBApp.CustomUser'


MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "DeltaBApp.middleware.performance.PerformanceMiddleware",
    "DeltaBApp.middleware.memory_usage.MemoryUsageMiddleware",
]

ROOT_URLCONF = "DeltaB.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "DeltaBApp.contextprocessors.typeiconmap",
                "DeltaBApp.contextprocessors.accounticonmap",
            ],
        },
    },
]

WSGI_APPLICATION = "DeltaB.wsgi.application"



DATABASES = {
    "default": dj_database_url.parse(
        Config.DATABASE_URL,
        conn_max_age=0, 
        conn_health_checks=True,
        ssl_require=True,
    )
}

MAX_RETRIES = 3
for i in range(MAX_RETRIES):
    try:
        # Your DB Config here...
        break
    except Exception as e:
        if i < MAX_RETRIES - 1:
            # This is better than print() because it marks it as a WARNING
            logger.warning(f"Database connection attempt {i+1} failed. Retrying...")
            time.sleep(5)
        else:
            logger.error("Database connection failed after maximum retries.")
            raise e


ALLOWED_ENVS = ("staging", "production", "development")

if ENV not in ALLOWED_ENVS:
    logger.critical(f"CRITICAL: Environment '{ENV}' is not recognized. Shutdown initiated.")
    raise RuntimeError(f"Invalid APP_ENV: {ENV}")


ALLOW_REGISTRATION = False


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"