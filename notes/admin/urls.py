from django.conf.urls.defaults import *
from notebook.notes.models import Note, Tag

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import notes

urlpatterns = patterns('',#'notebook.notes.views',
    # Example:
    #(r'^notebook/', include('notebook.foo.urls')),
    #(r'^$', 'index'),
    #(r'^$', 'django.views.generic.list_detail.object_list', info_dict),
     (r'', include(notes.site.urls)),
 
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #(r'^admin/', include(admin.site.urls)),
)
