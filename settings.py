# Django settings for notebook project.

from env_settings import *
import sys

sys.path.append(HOME_PATH)

DATABASE_ROUTERS = ['notebook.notes.dbrouter.Router']

MANAGERS = ADMINS

#DATABASE_ENGINE = 'django.db.backends.sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = '/home/leon/projects/notebookWebapp/notebook/db/notesdb'             # Or path to database file if using sqlite3.
#DATABASE_USER = ''             # Not used with sqlite3.
#DATABASE_PASSWORD = ''         # Not used with sqlite3.
#DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
#DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'


# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-cn'



SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://localhost:8000/site_media/' #TODO

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
 #   'django.middleware.cache.UpdateCacheMiddleware',    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',     
    'django.contrib.messages.middleware.MessageMiddleware',
    
     #for postman
    'pagination.middleware.PaginationMiddleware',

  # 'django.middleware.cache.FetchFromCacheMiddleware', 
)

#CACHE_MIDDLEWARE_ALIAS = 'default'
#CACHE_MIDDLEWARE_SECONDS = 600
#CACHE_MIDDLEWARE_KEY_PREFIX = ''

ROOT_URLCONF = 'notebook.urls'

#SESSION_ENGINE = 'django.contrib.sessions.backends.file'


TEMPLATE_CONTEXT_PROCESSORS = (
"django.contrib.auth.context_processors.auth",
"django.core.context_processors.debug",
"django.core.context_processors.i18n",
"django.core.context_processors.media",
"django.contrib.messages.context_processors.messages",
"django.core.context_processors.request",

#If you want to make use of a postman_unread_count context variable in your templates, add postman.context_processors.inbox 
"postman.context_processors.inbox",
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'notebook.notes', 
    'notebook.notes.admin', 
    'django.contrib.admin',
    'notebook.snippets',
    'notebook.bookmarks',
    'notebook.scraps',
    'notebook.social',
    'notebook.tags',
    'notebook.areas',
    'notebook.salons',

    'django.contrib.databrowse',
    'django.contrib.messages',
    'django.contrib.admindocs', 
    
    'postman',
    'pagination',
    'notification',
    'minidetector',
   
)


POSTMAN_AUTO_MODERATE_AS = True  # default is None
POSTMAN_AUTOCOMPLETER_APP = {
#'name':'ajax_select',
#'field': 'AutoCompleteField', # default is 'AutoCompleteField'
#'arg_name': 'channel', # default is 'channel'
#'arg_default': 'friends', # no default, mandatory to enable the feature
} # default is {}

#AJAX_LOOKUP_CHANNELS =  { 'friends' : dict(model='auth.User', search_field='username') }

LOCALE_PATHS = (
    HOME_PATH+'notebook/locale/postman',
    
)

POSTMAN_DISALLOW_ANONYMOUS = True # default is False
# POSTMAN_DISALLOW_MULTIRECIPIENTS = True # default is False
# POSTMAN_DISALLOW_COPIES_ON_REPLY = True # default is False
# POSTMAN_DISABLE_USER_EMAILING = True # default is False
POSTMAN_NOTIFIER_APP = 'notification' # default is 'notification'
# POSTMAN_MAILER_APP = None # default is 'mailer'

NOTIFICATION_QUEUE_ALL = True

SEND_BROKEN_LINK_EMAILS = True

import logging
LOG_FILE = WEBAPP_ROOT+'/osl.log'
LOG_LEVEL = logging.DEBUG

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

import settings_manager
