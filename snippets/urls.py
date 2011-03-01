from django.conf.urls.defaults import *
from django.contrib import databrowse
from django.views.generic import list_detail

from notebook.notes.models import Note, Tag



# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


#databrowse.site.register(Note)
#databrowse.site.register(Tag)

urlpatterns = patterns('',    
 

)
