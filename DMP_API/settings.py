from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

import sys, os, urllib, adal, struct, time



BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-m%nw21a8@kgq+9s)2($agh=%%@i(!w5phvuakw@z4tfj*+pl3%'
DEBUG = True
ALLOWED_HOSTS = ['*']



# SQL Alchemy Configuration
def get_engine(user, passwd, host, port, db):
    url = f"postgresql://{user}:{passwd}@{host}:{port}/{db}"
    if not database_exists(url):
        create_database(url)
    engine = create_engine(url, pool_size=50, echo=False)
    return engine



DATABASE_SERVER =  'localhost'
DATABASE_NAME ='db_dmp'
DATABASE_USER= 'postgres'
DATABASE_PASSWORD= 'Farid612'
DATABASE_PORT= '5432'
TENANT_ID = ""
CLIENT_ID = ""
SECRET = ""


# postgresql= {
#         'DATABASE_SERVER': DATABASE_SERVER,
#         'DATABASE_USER': DATABASE_USER,
#         'DATABASE_PASSWORD': DATABASE_PASSWORD,
#         'DATABASE_NAME': DATABASE_NAME,
#         'DATABASE_PORT':DATABASE_PORT,
# }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'db_dmp',
#         'USER': 'postgres',
#         'PASSWORD': 'Farid612',
#         'HOST': DATABASE_SERVER,
#         'PORT': '5433',
#     }
# }


engine = get_engine(DATABASE_USER, DATABASE_PASSWORD, DATABASE_SERVER, DATABASE_PORT, DATABASE_NAME)
# @event.listens_for(engine, 'do_connect')

def get_engine_from_settings():
    keys = ['DATABASE_USER','DATABASE_PASSWORD','DATABASE_SERVER','DATABASE_PORT','DATABASE_NAME']
    # if not all(key in keys for key in postgresql.keys()):
    #     raise Exception('Bad config file')
        
    return get_engine(DATABASE_USER,
                      DATABASE_PASSWORD,
                      DATABASE_SERVER,
                      DATABASE_PORT,
                      DATABASE_NAME)




# Password validation
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_HOST= 'smtp.gmail.com'
EMAIL_PORT= '587'
EMAIL_HOST_USER='dmp.bestrack@gmail.com'
EMAIL_HOST_PASSWORD='dmp.bestrack2021' 
EMAIL_USE_TLS=True      







INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages', 
    'django.contrib.staticfiles',
    'DMP_APP',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'DMP_API.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'DMP_API.wsgi.application'




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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ]
