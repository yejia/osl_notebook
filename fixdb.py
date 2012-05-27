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
    

from django.db import connections,  transaction
def fix_table(sql):    
    for alias in connections.databases.keys():
        if alias not in ['leon', 'default']: #TODO: get rid of this
            print 'for db ', alias
            cursor = connections[alias].cursor()
            cursor.execute(sql)
            transaction.commit_unless_managed(using=alias)
        



#notes from personal notebook deleted(or privated) before implemenation of "withdrawn from social notebook if 
#deleted or made private from personal" are still in social notebook (for example, those with private=True, deleted=False) 
#should be removed from db by the following script (although they cannot be viewed in social notebook now)   TODO:privacy
#def cleanup_social():
     #check inconsistence of db, and fix them
#    pass

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
        if command=='fix_table':
            print "add _order column to all db's notes_frame_notes table..."
            #TODO: get sql from command input
            fix_table('ALTER TABLE notes_frame_notes ADD COLUMN _order integer;')
          
         
