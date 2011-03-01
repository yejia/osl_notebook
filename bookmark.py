#!/usr/bin/env python

import sys
sys.path.append('/home/leon/projects/notebookWebapp/')

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from notebook.bookmarks.models import Bookmark

from notebook.notes.views import getT, getW, getNote

from datetime import datetime




def import_only_a(username, bookmark_file, default_vote=0, common_tag=None, common_ws=None):
    """This only get urls, and ignore all the other infos such as folders, desc."""
       
    urls = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified')) for tag in
            BeautifulSoup(bookmark_file).findAll('a')]    
    count_urls_in_file = len(urls)
    print count_urls_in_file, ' urls found in the bookmark file.'
    
    duplicate = []
    count_note_created = 0

    for url in urls:
        n, created = build_one_bookmark(username, url, default_vote)
        if not created:
            duplicate.append((url[0], url[1]))
        else:
            count_note_created+=1    
    
    print  count_note_created, ' bookmarks created'    
    print len(duplicate), ' duplicated bookmarks.'    
    #print  'duplicate is:',duplicate
    duplicate.sort()
    return count_urls_in_file, count_note_created, duplicate


def import_delicious_with_no_desc(username, bookmark_file, default_vote=0, common_tag=None, common_ws=None):
    """This import from bookmark file exported from delicious, which has tags attr inside a tag."""
       
    urls = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified'), tag.get('tags')) for tag in
            BeautifulSoup(bookmark_file).findAll('a')]    
    count_urls_in_file = len(urls)
    print count_urls_in_file, ' urls found in the bookmark file.'
    
    duplicate = []
    count_note_created = 0
    count_tag_created = 0

    for url in urls:
        n, created = build_one_bookmark(username, url, default_vote)
        num_of_tags_created = n.add_tags(url[4]+','+common_tag)        
        count_tag_created = count_tag_created + num_of_tags_created
        W = getW(username)
        w, created = W.objects.get_or_create(name=common_ws)
        w.add_tags(url[4]+','+common_tag)
        w.save()
        if not created:
            duplicate.append((url[0], url[1]))
        else:
            count_note_created+=1    
    
    print  count_note_created, ' bookmarks created'    
    print len(duplicate), ' duplicated bookmarks.'    
    #print  'duplicate is:',duplicate
    duplicate.sort()
    return count_urls_in_file, count_note_created, duplicate, count_tag_created


def import_delicious(username, bookmark_file, default_vote=0, common_tag=None, common_ws=None):
    """This import from bookmark file exported from delicious, which has tags attr inside a tag."""
       
    urls = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified'), tag.get('tags')) for tag in
            BeautifulSoup(bookmark_file).findAll('a')]    
    count_urls_in_file = len(urls)
    print count_urls_in_file, ' urls found in the bookmark file.'
    
    duplicate = []
    count_note_created = 0
    count_tag_created = 0
    bookmark_file.seek(0)
    n = None
    for line in bookmark_file:
        if line.find('<DT><A') != -1:
            url = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified'), tag.get('tags')) for tag in BeautifulSoup(line).findAll('a')][0]
            n, created = build_one_bookmark(username, url, default_vote)  
            if not created:
                duplicate.append((url[0], url[1]))
            else:
                count_note_created+=1   
            num_of_tags_created = n.add_tags(url[4]+','+common_tag)        
            count_tag_created = count_tag_created + num_of_tags_created
            W = getW(username)
            w, created = W.objects.get_or_create(name=common_ws)
            w.add_tags(url[4]+','+common_tag)
            w.save()
             
        if line.find('<DD>') != -1:
            if n:
                desc = line.strip('<DD>').strip('</DD>')  
                n.desc = desc
                n.save() 
                print 'n.desc:', n.desc
    print  count_note_created, ' bookmarks created'    
    print len(duplicate), ' duplicated bookmarks.'    
    #print  'duplicate is:',duplicate
    duplicate.sort()
    return count_urls_in_file, count_note_created, duplicate, count_tag_created


def build_one_bookmark(username, url, default_vote=0):
    N = getNote(username, 'bookmarkbook')
    
    n, created = N.objects.get_or_create(url = url[0])
    if created:
        if url[1]==None:
            n.title = ""
        else:    
            n.title   = url[1]
        if url[2]:
            a = url[2]
            #Google bookmark file uses 16 digits for the datetime. We only need 10 digits.
            if len(a)==16:
                a = a[:-6]                        
            #TODO: catch possible exceptions
            n.init_date = datetime.fromtimestamp(int(a))            
        else:
            n.init_date = datetime.now()
        if url[3]:             
            a = url[3]
            if len(a)==16:
                a = a[:-6]              
            n.last_modi_date = datetime.fromtimestamp(int(a))
        else:   
            n.last_modi_date = datetime.now()

        n.vote = default_vote
        n.save()
        print 'A bookmark is saved:', n
    return n, created


#This method only works with exported google bookmark files correctly, since google bookmark has no folders, and google bookmark
#file puts tags in where browsers put folders. This function can be deleted, use import_with_tags2 instead, which works with google bookmark file as well.
from django.utils.encoding import smart_str, smart_unicode
def import_with_tags(username, bookmark_file, default_vote=0, common_tag=None, common_ws=None):
    """This not only gets all the urls, but also turns the folders in the file into tags"""
    
    
    T = getT(username)
    W = getW(username)
    
    urls = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified')) for tag in
            BeautifulSoup(bookmark_file).findAll('a')]  
    count_urls_in_file = len(urls)
    print count_urls_in_file, ' urls found in the bookmark file.'
    
    bookmark_file.seek(0)
    folders = [tag.string for tag in BeautifulSoup(bookmark_file).findAll('h3')]
    print 'folders:', folders
    print len(folders), ' folders found in the bookmark file.'
    
    count_tag_created = 0
    
    w = W.objects.get(name="bookmarks")
    
    #make each of them into a tag
    for folder in folders:
        print 'type(folder):', type(folder)
        print 'folder:', folder
        
        #some bug with BeautifulSoup's custom unicode. So upcast back to unicode itself. See http://code.djangoproject.com/ticket/11932
        folderstr = unicode(folder)
        print 'type(folderstr):', type(folderstr)
        print 'folderstr:', folderstr
        
        if folderstr not in [u'Unsorted Bookmarks', u'[Folder Name]', u'Bookmarks Toolbar']:
             
            t, created = T.objects.get_or_create(name = folderstr)                    
            print 'tag ', t, ' created ', created
            print 't.name:', t.name
            if created:
                #print 'tag:', t, ' is created.'
                count_tag_created += 1
            w.tags.add(t)    
            w.save()
    
    print  count_tag_created, 'tags are created.'
    
    count_note_created = 0
    duplicate = []
    #move the ponter back to the beginning of the file
    bookmark_file.seek(0)
    t = None
    for line in bookmark_file:
        if line.find('<DT><A')  != -1:
            url = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified')) for tag in BeautifulSoup(line).findAll('a')][0]
            n, created = build_one_bookmark(username, url, default_vote)  
            if not created:
                duplicate.append((url[0], url[1]))          
            else:
                count_note_created +=1            
            if t:
                n.tags.add(t) 
                n.save()                   
        elif  line.find('<DT><H3') != -1:    
            tname =  [tag.string for tag in BeautifulSoup(line).findAll('h3')][0]
            if unicode(tname) not in [u'Unsorted Bookmarks', u'[Folder Name]', u'Bookmarks Toolbar']:
                print 'unicode(tname) is:', unicode(tname)
                t = T.objects.get(name__exact=unicode(tname))            
        else:
            continue

    print  count_note_created, ' bookmarks created' 
    print len(duplicate), ' duplicated bookmarks.'
    #print  'duplicate is:', duplicate
    duplicate.sort()
    return count_urls_in_file, count_note_created, duplicate, count_tag_created
 

from django.utils.encoding import smart_str, smart_unicode
def import_with_tags2(username, bookmark_file, default_vote=0, common_tag=None, common_ws=None):
    """This not only gets all the urls, but also turns the folders in the file into tags"""    
    
    T = getT(username)
    W = getW(username)
    
    urls = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified')) for tag in
            BeautifulSoup(bookmark_file).findAll('a')]  
    count_urls_in_file = len(urls)
    #print count_urls_in_file, ' urls found in the bookmark file.'
    
    count_tag_created = 0
    
    w = W.objects.get(name="bookmarks")    
    
    count_note_created = 0
    duplicate = []
    #move the pointer back to the beginning of the file
    bookmark_file.seek(0)
    b = None
    folder_list = []    
    for line in bookmark_file:
        if line.find('<DT><H3') != -1:               
            tname =  [tag.string for tag in BeautifulSoup(line).findAll('h3')][0]
            folder_list.append({tname:[]})
            #print 'one folder with folder name ',tname,' pushed to stack.'
        if line.find('</DL><P>')  != -1 or line.find('</DL><p>')  != -1:#FF and Chrome use <p> while Opera uses <P>
            
            #there is one extra '</DL><P>' at the end of the file for <H1>Bookmarks</H1>. So when it comes to the
            #it, just skip
            if len(folder_list) == 0:                
                continue
            folder_of_urls = folder_list.pop()  
            #print 'one folder ',folder_of_urls,' popped out of stack.'
            folder = folder_of_urls.keys()[0]
            urls = folder_of_urls.get(folder)
            folderstr = unicode(folder)
            if folderstr not in [u'Unsorted Bookmarks', u'[Folder Name]', u'Bookmarks Toolbar']:
                t, created = T.objects.get_or_create(name = folderstr)  
                if created:
                    count_tag_created += 1 
                w.tags.add(t)    
                w.save()                   
                for url in urls:    
                    #print 'url in the popped out stack is: ', url                 
                    url.tags.add(t) 
                    num_of_tags_created = url.add_tags(common_tag)
                    count_tag_created = count_tag_created + num_of_tags_created
                    url.save()         
        if line.find('<DT><A') != -1:
            u = [(tag['href'], tag.string, tag.get('add_date'), tag.get('last_modified')) for tag in BeautifulSoup(line).findAll('a')][0]
            b, created = build_one_bookmark(username, u, default_vote) 
            if not created:
                duplicate.append((u[0], u[1]))          
            else:
                count_note_created +=1               
            #for url that is at the top, simply create the bookmark without adding it to any tag
            if len(folder_list) == 0:
                pass
            else:
                for i in range(len(folder_list)):#add this url to every folder on the stack
                    f_of_bs = folder_list[i]
                    f = f_of_bs.keys()[0]
                    bs = f_of_bs.get(f)
                    bs.append(b)
                    f_of_bs.update({f:bs})
                    folder_list[i] = f_of_bs
                    #print 'one url ', b, 'is added to a folder on stack ', f
        if line.find('<DD>') != -1:
            if b:
                desc = line.strip('<DD>').strip('</DD>')  
                b.desc = desc
                b.save() 
                print 'b.desc:', b.desc
            

    #print  count_note_created, ' bookmarks created' 
    #print len(duplicate), ' duplicated bookmarks.'
    #print  'duplicate is:', duplicate
    duplicate.sort()
    return count_urls_in_file, count_note_created, duplicate, count_tag_created



#TODO:  more help for the command inputs. Also make ignoring_folder a command line argument
if __name__ == "__main__":
    
    username = sys.argv[1]
    bookmark_file = open(sys.argv[2]) 
    if len(sys.argv) > 3:
        default_vote = int(sys.argv[3])
    else:
        default_vote = 0     
    
    import_with_tags2(username, bookmark_file, default_vote)  
    #import_only_a(username, bookmark_file, default_vote)   


