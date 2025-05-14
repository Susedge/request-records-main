from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
ENABLE_OTP_VERIFICATION = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+l_auu##_g=um5g$tf5jpi0+2$q=zri4%!d4pq^komcmp($%37'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'request-records-main.onrender.com',
    'localhost',
    '127.0.0.1',
    ]

EMAIL_HOST_USER = 'chesspiecedum2@gmail.com'
EMAIL_HOST_PASSWORD = 'btoogzanhtonxulo'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'onlinerequest.apps.OnlinerequestConfig',
    'rest_framework'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'onlinerequest.middleware.UserTypeMiddleware',
]

ROOT_URLCONF = 'records.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'onlinerequest.context_processors.user_record',
                'onlinerequest.context_processors.request_forms',
                'onlinerequest.context_processors.user_profile',
                'onlinerequest.context_processors.courses',
                'onlinerequest.context_processors.user_requests',
                'onlinerequest.context_processors.document_types',
            ],
        },
    },
]

WSGI_APPLICATION = 'records.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

PERSISTENT_STORAGE_DIR = os.environ.get('RENDER_PERSISTENT_DIR', None)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(PERSISTENT_STORAGE_DIR) / 'db.sqlite3' if PERSISTENT_STORAGE_DIR else BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'

# This is the directory where Django will collect all static files for deployment
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')

# Define potential static directories
potential_static_dirs = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'records', 'static'),
]

# Only include directories that actually exist
STATICFILES_DIRS = [d for d in potential_static_dirs if os.path.isdir(d)]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Authentication
AUTH_USER_MODEL = 'onlinerequest.User'

AUTHENTICATION_BACKENDS = ['onlinerequest.backends.EmailBackend']

# Middleware
LOGIN_REDIRECT_URL=''

REST_FRAMEWORK = {
    "DATE_INPUT_FORMATS": ["%Y-%m-%d"],
}