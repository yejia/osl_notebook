# Django settings for notebook project.

from env_setting import DEBUG, TEMPLATE_DEBUG, DB_ROOT, MEDIA_ROOT, TEMPLATE_DIRS, WEBAPP_ROOT



ADMINS = (
     ('Yuanliang', 'yuanliangliu@gmail.com'),
)



DATABASES = {

'test': {
                        'NAME': DB_ROOT+'/notesdb_test',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },





'yx': {
                        'NAME': DB_ROOT+'notesdb_yx',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'lywang': {
                        'NAME': DB_ROOT+'notesdb_lywang',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },



'songbo': {
                        'NAME': DB_ROOT+'notesdb_songbo',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'shunfeng': {
                        'NAME': DB_ROOT+'notesdb_shunfeng',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },



'guest': {
                        'NAME': DB_ROOT+'notesdb_guest',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'xlzhuang': {
                        'NAME': DB_ROOT+'notesdb_xlzhuang',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'alexyu': {
                        'NAME': DB_ROOT+'notesdb_alexyu',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },



'daniellyian': {
                        'NAME': DB_ROOT+'notesdb_daniellyian',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'lxy': {
                        'NAME': DB_ROOT+'notesdb_lxy',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'estebistec': {
                        'NAME': DB_ROOT+'notesdb_estebistec',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },



'shilei': {
                        'NAME': DB_ROOT+'notesdb_shilei',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },



'young': {
                        'NAME': DB_ROOT+'notesdb_young',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'yuanxi': {
                        'NAME': DB_ROOT+'notesdb_yuanxi',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'yangjun': {
                        'NAME': DB_ROOT+'notesdb_yangjun',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },

'dipzjjz': {
                        'NAME': DB_ROOT+'notesdb_dipzjjz',
                        'ENGINE': 'django.db.backends.sqlite3' ,
                        'USER': '',
                        'PASSWORD': ''
                        },


    'default': {
        'NAME': DB_ROOT+'notesdb',
        'ENGINE': 'django.db.backends.sqlite3' ,
        'USER': '',
        'PASSWORD': ''
    },
    'leon': {
        'NAME': DB_ROOT+'notesdb_leon',
        'ENGINE': 'django.db.backends.sqlite3' ,
        'USER': '',
        'PASSWORD': ''
    },


    'yuanliang': {
        'NAME': DB_ROOT+'notesdb_yuanliang',
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': ''
    },

   


}

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ee)$g*c_29j6+c=zsz!#aj0e#dqo4+ffeulv5wgk5h$^kyvs7&'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',     
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'notebook.urls'

#SESSION_ENGINE = 'django.contrib.sessions.backends.file'


TEMPLATE_CONTEXT_PROCESSORS = (
"django.contrib.auth.context_processors.auth",
"django.core.context_processors.debug",
"django.core.context_processors.i18n",
"django.core.context_processors.media",
"django.contrib.messages.context_processors.messages",
"django.core.context_processors.request",
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

    'django.contrib.databrowse',
    'django.contrib.messages',
    'django.contrib.admindocs', 
)

EMAIL_HOST =  'smtp.googlemail.com' #'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'yuanliangliu'
EMAIL_HOST_PASSWORD = 'peiman457' #TODO:get rid of
SERVER_EMAIL = 'yuanliangliu@gmail.com' #'root@localhost'
EMAIL_USE_TLS = True

#SEND_BROKEN_LINK_EMAILS = True

import logging
LOG_FILE = WEBAPP_ROOT+'/osl.log'
LOG_LEVEL = logging.DEBUG
