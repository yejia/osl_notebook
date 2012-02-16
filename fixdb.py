#!/usr/bin/env python
#This fix db inconsistence, such as vote and tags of linkages (making them the same as sum of included notes)

import sys, os

#TODO: no hardcoding of home_path
#home_path = '/home/leon/projects/notebookWebapp/notebook_src'
from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)
from django.db import models

from notebook.notes.views import getL
from notebook.bookmarks.views import getL as getL2

from notebook.notes.models import get_storage_loc, fs,  create_model #Note_Backup,
from notebook.snippets.models import Snippet


from notebook.notes.views import getT, getNote
#from notebook.bookmarks.views import getN as getB
#from notebook.scraps.views import getN as getS
from notebook.social.models import Social_Snippet, Social_Tag, Social_Bookmark, Social_Scrap

from notebook.notes.models import Tag

from django.contrib.auth.models import User



try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)


from django.utils.translation import ugettext_noop as _
from django.db.models import signals

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("friends_invite", _("Invitation Received"), _("you have received an invitation"))
        notification.create_notice_type("friends_accept", _("Acceptance Received"), _("an invitation you sent has been accepted"))
        notification.create_notice_type("comment_receive", _("Comment Received"), _("you have received a comment"))
        

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"




#def getNB(username):
#    return create_model("NB_"+str(username), Note_Backup, username)

def getBB(username):
    return create_model("BB_"+str(username), Bookmark_Backup, username)

def getSB(username):
    return create_model("SB_"+str(username), Scrap_Backup, username)

def getSnip(username):
    return create_model("Snip_"+str(username), Snippet, username)


#insert snippets backed up to snippet table after letting snippet subclass note
#def restore_snippet(username):
#    NB = getNB(username)
#    nbs = NB.objects.all()
#    Snip = getSnip(username)
#    for nb in nbs:
#        s = Snip(desc=nb.desc, title=nb.title, private=nb.private, deleted=nb.deleted, attachment=nb.attachment, \
#init_date=nb.init_date, last_modi_date=nb.last_modi_date, vote=nb.vote) 
#        s.save()
#        s.tags = nb.tags.all()
        





def fix_linkage_vote(username):
    L = getL(username)
    ls = L.objects.all()
    for l in ls:
        l.vote = l.get_vote()
        l.save()
    L2 = getL2(username)
    ls2 = L2.objects.all()
    for l2 in ls2:
        l2.vote = l2.get_vote()
        l2.save()

#TODO: not tested. Also not sure if the linkage shouldn't have its own unique tags
def fix_linkage_tags(username):
    L = getL(username)
    ls = L.objects.all()
    for l in ls:
        l.update_tags(l.get_t_display_of_sum_of_note_tags())
        l.save()
    L2 = getL2(username)
    ls2 = L2.objects.all()
    for l2 in ls2:
        l.update_tags(l.get_t_display_of_sum_of_note_tags())
        l2.save()  
        
        
#this was written temporarily to fix db attachment path due to change of db structure 
#from notebook.notes.views import getN       
#def fix_db_attachment_path():        
#    N = getN(username)
#    ns = N.objects.all(attachment__startswith='noteattachments/')
#    for n in ns:
#        if ns.attachment:
#            pass #TODO:
    




#TODO: add other users' notes into the Social_Note
def init_social_db_snippet(username):
    print 'init social db...'
    user = User.objects.get(username=username)

    N = getNote(username, 'snippetbook')       
    ns = N.objects.all()       
    for n in ns:
        print 'note is:', n
        if not n.private and not n.deleted:
            sts = []
            for t in n.tags.all():
                if not t.private:  
                    st, created = Social_Tag.objects.get_or_create(name=t.name)
                    sts.append(st)
            s, created = Social_Snippet.objects.get_or_create(owner=user, owner_note_id=n.id, desc=n.desc, title=n.title,\
init_date=n.init_date, last_modi_date=n.last_modi_date, vote=n.vote) #attachment
            if created:
                for t in sts:
                    s.tags.add(t)
                s.save()
                #print 'a new sn saved'



def init_social_db_bookmark(username):
    user = User.objects.get(username=username)

    N = getNote(username, 'bookmarkbook')       
    ns = N.objects.all()   
    for n in ns:
        print 'bookmark is:', n
        if not n.private and not n.deleted:
            sts = []
            for t in n.tags.all():
                if not t.private:  
                    st, created = Social_Tag.objects.get_or_create(name=t.name)
                    sts.append(st)
            s, created = Social_Bookmark.objects.get_or_create(owner=user, owner_note_id=n.id, url=n.url, desc=n.desc, title=n.title,\
init_date=n.init_date, last_modi_date=n.last_modi_date, vote=n.vote) #attachment
            if created:
                for t in sts:
                    s.tags.add(t)
                s.save()   


def init_social_db_scrap(username):
    user = User.objects.get(username=username)

    N = getNote(username, 'scrapbook')       
    ns = N.objects.all()     
    for n in ns:
        print 'scrap is:', n
        if not n.private and not n.deleted:
            sts = []
            for t in n.tags.all():
                if not t.private:  
                    st, created = Social_Tag.objects.get_or_create(name=t.name)
                    sts.append(st)
            s, created = Social_Scrap.objects.get_or_create(owner=user, url=n.url, owner_note_id=n.id, desc=n.desc, title=n.title,\
init_date=n.init_date, last_modi_date=n.last_modi_date, vote=n.vote) #attachment
            if created:
                for t in sts:
                    s.tags.add(t)
                s.save()       
    


if __name__ == "__main__": 
    if len(sys.argv) == 1:
        pass
    else:   
        username = sys.argv[1] 
        command =  sys.argv[2]
        if command=='all':     
             fix_linkage_vote(username)
             fix_linkage_tags(username)
        if command=='vote':     
             fix_linkage_vote(username)  
        if command=='tags':     
             fix_linkage_tags(username)  
        if command=='init_social_snippet':
             init_social_db_snippet(username) 
        if command=='init_social_bookmark':
             init_social_db_bookmark(username)  
        if command=='init_social_scrap':
             init_social_db_scrap(username) 
        if command=='restore_snippet':
             restore_snippet(username) 
        if command=='restore_bookmark':
             restore_bookmark(username)
        if command=='restore_scrap':
             restore_scrap(username)
          
         
