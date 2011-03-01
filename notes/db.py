#!/usr/bin/env python


import sys; print('%s %s' % (sys.executable or sys.platform, sys.version))

sys.path.append('/home/leon/projects/notebookWebapp')

from django.core import management;import notebook.settings as settings;management.setup_environ(settings)
from django.contrib.auth.models import User


from notebook.notes.models import Note, Tag, LinkageNote, Folder, Cache

def build_linkage_tags():
    #TODO: how to get users from the LinkageNote table directly
    users = User.objects.all()
    for user in users:
        linkages = LinkageNote.objects.filter(user__username__exact=user.username)        
    
        for linkage in linkages:
            linkage.update_tags(linkage.get_display_of_sum_of_note_tags())
            linkage.save()
        

def build_linkage_votes():
    linkages = LinkageNote.objects.all()
    for linkage in linkages:
        votes = 0
        for n in linkage.notes.all():
            votes += n.vote
        linkage.vote = votes  
        linkage.save()  


if __name__ == "__main__":
    name = sys.argv[1]
    if name == 'build_linkage_tags':
        build_linkage_tags()
    if name == 'build_linkage_votes':
        build_linkage_votes()  
    sys.exit(0)      
