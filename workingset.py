#!/usr/bin/env python

import sys
sys.path.append('/home/leon/projects/notebookWebapp/')

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)


from notebook.notes.views import getT, getW




def add2workingset(username):
    W = getW(username)
    T = getT(username)
    tags = T.objects.all()    
    w, created = W.objects.get_or_create(name='snippetbook')
    w.tags = tags#.values_list('id', flat=True)
    w.save()
    print 'a workingset is saved:', w.name, ' with tags: ', w.tags
    
   
   
   
#TODO:  more help for the command inputs
if __name__ == "__main__":
    add2workingset(sys.argv[1])    


