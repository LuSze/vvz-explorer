import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-yv!jl856dk$+*x06sagndgy^(sz_!h6+sy$3h1#ulh#v9krey#')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True') == 'True'

DEFAULT_SEMESTER = '2026S'

SEMESTER_DB_MAP = {
    '2026S': ('lectures_FS2026.db', 'embeddings_FS2026.db'),
    '2026W': ('lectures_HS2026.db', 'embeddings_HS2026.db'),
    '2025W': ('lectures_HS2025.db', 'embeddings_HS2025.db'),
    '2025S': ('lectures_FS2025.db', 'embeddings_FS2025.db'),
    '2024W': ('lectures_HS2024.db', 'embeddings_HS2024.db'),
}

DATA_DIR = Path(os.environ.get('DATA_DIR', str(BASE_DIR / '..' / '..' / 'data')))
LECTURES_DB_PATH = DATA_DIR / 'lectures_FS2026.db'
EMBEDDINGS_DB_PATH = DATA_DIR / 'embeddings_FS2026.db'
EMBEDDING_MODEL_NAME = 'nomic-ai/nomic-embed-text-v1.5'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
}