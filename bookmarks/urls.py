from django.conf.urls.defaults import *
from django.contrib import databrowse
from django.views.generic import list_detail



# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('', 

  
    (r'^share/$','notebook.bookmarks.views.share'),
    

)
