#!/usr/bin/env python


import sys; print('%s %s' % (sys.executable or sys.platform, sys.version))
import os

from env_settings import HOME_PATH
sys.path.append(HOME_PATH)
#sys.path.append('/home/leon/projects/notebookWebapp')
import notebook
from django.core import management;import notebook.settings as settings;management.setup_environ(settings)
from django.contrib.auth.models import User
from django.db.utils import ConnectionDoesNotExist
from django.core.exceptions import ObjectDoesNotExist

from django.db import connections,  transaction



from notebook.notes.util import getNote, getFrame
from notebook.notes.models import Note, Tag, LinkageNote, Folder, Cache, Frame, getT

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


def build_frame_votes():
    users = User.objects.all()
    for user in users:
        print "build frame votes for user:", user.username
        try:
            F = getFrame(user.username)
            frames = F.objects.all()
            for frame in frames: 
                print "building votes for frame:",frame.id               
                frame.vote = frame.get_vote()  
                frame.save()
        except ConnectionDoesNotExist:
            print 'raised ConnectionDoesNotExist for user:'+user.username         
    #do for the default/social database 
    #shouldn't need below since the save method of each note will automatically update those in the social
#===============================================================================
#        frames = Frame.objects.all()
#        for frame in frames:
#            votes = 0
#            for n in frame.notes.all():
#                votes += n.vote
#            frame.vote = votes  
#            frame.save() 
#===============================================================================


#clean up untagged tag for notes already having other tags, add untagged tag for notes having no tags
def cleanup_tags():
    users = User.objects.all()     
    for user in users:
        N = getNote(user.username, 'notebook')
        T = getT(user.username) 
        print 'Cleaning up tags for user:'+user.username
        try:
            notes = N.objects.filter(tags__name='untagged')
            for note in notes:                
                #t = T.objects.get(name='untagged')
                if note.tags.count() > 1:
                    print 'removing the tag untagged for note:',note.id
                    note.remove_tags(['untagged'])  
                    #note.save()
            try:
                t = T.objects.get(name="") 
            except ObjectDoesNotExist: 
                print 'raise ObjectDoesNotExist when finding the empty string tag for user:'+user.username  
                continue
            notes_of_no_tags =  N.objects.filter(tags__name="")        
           
            for note in notes_of_no_tags:  
                    print 'removing the empty tag for note:',note.id                       
                    note.tags.remove(t)  
                    #note.save()
            print "removing the empty tag itself"
            t.delete()        
        except ConnectionDoesNotExist:
            print 'raised ConnectionDoesNotExist for user:'+user.username            
    
                                    
                
#TODO: this sync didn't sync the default db      
def sync_all_dbs():
    users = User.objects.all()
    for user in users:
        print 'sync db for user:', user
        os.system('python manage.py syncdb --database='+user.username) 
        #on server, use django-admin
        #os.system('python2.7 manage.py syncdb --database='+user.username) 
        #os.system('../bin/django-admin.py syncdb --database='+user.username) 
        


def rename_tag_table(users):
    if not users:
        users = [u.username for u in User.objects.all()]
    for user in users:
       print 'For user', user
       try:
           cursor = connections[user].cursor()
           cursor.execute('ALTER TABLE notes_tag RENAME TO tags_tag;')          
           transaction.commit_unless_managed()
       except Exception as inst:
           print type(inst)
           print inst.args
           print inst
       try:
           cursor.execute('ALTER TABLE tags_tag ADD COLUMN "desc" text;')
           transaction.commit_unless_managed()

       except Exception as inst:
           print type(inst)
           print inst.args
           print inst
           



def fix_notes_frame_notes_table(users):
    if not users:
         users = [u.username for u in User.objects.all()]
    for user in users:
        print 'For user', user
        try:
            cursor = connections[user].cursor()
            cursor.execute('ALTER TABLE notes_frame_notes ADD COLUMN "_order" integer;')          
            transaction.commit_unless_managed()
        except Exception as inst:
            print type(inst)
            print inst.args
            print inst   



if __name__ == "__main__":
    name = sys.argv[1]
    if name == 'build_linkage_tags':
        build_linkage_tags()
    if name == 'build_linkage_votes':
        build_linkage_votes() 
    if name == 'build_frame_votes':
        build_frame_votes()  
    if name == 'cleanup_tags':
        cleanup_tags()  
    if name == 'sync_all_dbs':
        sync_all_dbs() 
    if name == 'rename_tag_table':
        users = sys.argv[2:]
        print 'users',users 
        rename_tag_table(users)   
    if name == 'fix_nfn':
        users = sys.argv[2:]
        print 'users',users 
        fix_notes_frame_notes_table(users)         
    sys.exit(0)      
