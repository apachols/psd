# Django settings for psd project.

SITE_DIR = 'dallas'
DEBUG = False
TEMPLATE_DEBUG = DEBUG

HOMEDIR = '/home/psd'
SUBDIR = '/site_' + SITE_DIR
APPSLUG = '/reg'
URLPREFIX = '/psd/' + SITE_DIR
PROJECT_PATH = HOMEDIR + SUBDIR
WEBSITE_PATH = HOMEDIR+'/public_html/'

APPDIR = HOMEDIR + SUBDIR

ADMINS = (
    ('Luke Miratrix', 'luke_' + SITE_DIR + '_psd@vzvz.org' ),
)
ADMIN_FOR = ('register','psd.register',)
MANAGERS = (
    ('Luke Miratrix', 'luke_' + SITE_DIR + '_psd@vzvz.org' ),
    ('Another Person', 'fake_psd@vzvz.org' ),
)

EMAIL_SUBJECT_PREFIX = '[Dallas PSD] '
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'polyspeeddating'
EMAIL_HOST_PASSWORD = 'XXXXXXXXX'
EMAIL_USE_TLS = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'adsl;aj;dkfja;sja;ldskfja;sdlkfja;sdlkfjavnkrijga'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': APPDIR + '/mydb'
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = PROJECT_PATH+'/psd/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'psd.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    PROJECT_PATH+'/sites/' + SITE_DIR,
    PROJECT_PATH+'/psd/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'psd.register',
)

LOGIN_URL = URLPREFIX + APPSLUG + '/accounts/login'
LOGIN_REDIRECT_URL = URLPREFIX + APPSLUG + '/accounts/view/'



TEMPLATE_CONTEXT_PROCESSORS = ("django.core.context_processors.auth",
                            "django.core.context_processors.debug",
                            "django.core.context_processors.i18n",
                            "django.core.context_processors.media",
                            "django.core.context_processors.request",)



R_SOURCE_DIR = PROJECT_PATH+'/Rs/'

LOG_DIR = PROJECT_PATH+'/logs/'

import logging
logging.basicConfig(filename=LOG_DIR+"logfile.log",level=logging.DEBUG)


APPEND_SLASH = True
