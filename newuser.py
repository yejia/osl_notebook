#!/usr/bin/env python

import sys, os

from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from notebook.env_settings import *



from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)



from notebook.notes.views import getT, getW
from notebook.social.models import Member

#from django.contrib.auth.models import User



def dryrun():
    print 'HOME_PATH: ', HOME_PATH


def create_member(username, email, passwd):
    m = Member.objects.create_user(username, email, passwd)
    m.is_active = True
    m.save()  
    created = True  
    return m, created
                                     


#create the database file for the user
#TODO: do I need to specify a super user after this (since it installed a new auth system). Otherwise cannot manage with myadmin?
#This function doesn't work on local machine since the local dev server will reload the settings.py if it is changed making 
def create_db(username):   
    command_to_run = 'cp '+DB_ROOT+'notesdb_init  '+DB_ROOT+'notesdb_'+username
    #below is for working with Chinese name. But even with the user creation and db creation passed, there is still
    #issue when logging in. The system cannot use the Chinese alias to find connection even the connection does exist. TODO:
    #command_to_run = (u'cp '+DB_ROOT+u'notesdb_init  '+DB_ROOT+u'notesdb_'+username).encode('utf8')
    
    os.system(command_to_run)

    #as the last resort, put this at the end or registration code to restart the server 
    #os.system(command_to_restart_server)  

    #print 'execute syncdb with shell'
    #os.system('python manage.py syncdb --database='+username)
    
    #reload(notebook.settings)

    #reload(notebook.notes.views) 

    newDatabase = {}
    newDatabase["id"] = username
    newDatabase['ENGINE'] = 'django.db.backends.sqlite3'
    newDatabase['NAME'] = DB_ROOT+'/notesdb_'+username
    newDatabase['USER'] = ''
    newDatabase['PASSWORD'] = ''
    #newDatabase['HOST'] = ''
    #newDatabase['PORT'] = ''  
    settings.DATABASES[username] = newDatabase
    save_db_settings_to_file(newDatabase)

    #print 'get the setting.py, write to it the config for the new db'
#===============================================================================
#    f = open(HOME_PATH+'notebook/settings.py', 'r+')
#    lines = f.readlines()
#    for i in range(len(lines)):
#        if lines[i].find('DATABASES = {')!=-1:
#            lines.insert(i+1,"""\n'"""+username+"""': {
#                        'NAME': DB_ROOT+'/notesdb_"""+username+"""',
#                        'ENGINE': 'django.db.backends.sqlite3' ,
#                        'USER': '',
#                        'PASSWORD': ''
#                        },\n""")
#                        
# 
#    f.seek(0)
#    for line in lines:
#        f.write(line)
#    f.flush()
#    f.close()
#===============================================================================
    

def save_db_settings_to_file(db_settings):
    path_to_store_settings  
    newDbString = """
DATABASES['%(id)s'] = {
        'ENGINE': '%(ENGINE)s', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '%(NAME)s',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.    
         } """ % db_settings
    file_to_store_settings = os.path.join(path_to_store_settings, db_settings['id'] + ".py") 
    f = open(file_to_store_settings, 'w')
    f.write(newDbString)    
    #f.write(newDbString.encode('utf8'))  

    
    
def add_tags_2_ws(username, ws_name):
    T = getT(username)
    W = getW(username)   
    w = W.objects.get(name=ws_name)
    w.tags = T.objects.all()
    
    
if __name__ == "__main__":    
    username = sys.argv[1] 
    command =  sys.argv[2]
    #TODO: cannot run all command together. Problem is that init method has to be run separatly. If run together, it cannot
    #find the connection for the db.  It might because it couldn't find the newly created db file from memory or simply setting
    #was not reloaded
    if command=='all':  
        email = sys.argv[3]
        passwd = sys.argv[4] 
        create_member(username, email, passwd)         
        create_db(username)                
    elif command=='create_db':
        create_db(username)    
    elif command=='add_tags_2_ws':
        add_tags_2_ws(username, sys.argv[3])    
    elif command=='create_member':
        email = sys.argv[3]
        passwd = sys.argv[4]
        create_member(username, email, passwd)
    elif command=='dryrun':
        dryrun()  


