DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_restapi_tests.polls'
)

ROOT_URLCONF = 'django_restapi_tests.urls'

DATABASE_NAME = ':memory:' 
DATABASE_ENGINE = 'sqlite3'
TEMPLATE_DIRS = 'templates'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.middleware.common.CommonMiddleware',
#    'django.middleware.doc.XViewMiddleware',
)