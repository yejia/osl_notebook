from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.forms import ModelForm

from notebook.notes.views import __get_ws_tags, getlogger, getNote, getT, getW, create_model_form
import notebook
from notebook.bookmarks.models import Bookmark


#TODO: below to be deleted later after merging linkage. This def is only used in fixdb.py
from notebook.notes.views import create_model
from notebook.bookmarks.models import Linkage_Of_Bookmark
def getL(username):
    return create_model("L_bookmarks_"+str(username), Linkage_Of_Bookmark, username)


log = getlogger('bookmarks.views')         




#this method is used for processing the request users send via the browser button  TODO: use code in add_note method 
#TODO: give error message if an error
@login_required    
def add_bookmark(request):
    username = request.user.username
    N = getNote(username, 'bookmarkbook')
    T = getT(username)
    #W = getW(username)
    #w = W.objects.get(name='bookmarkbook')
    if request.method == 'POST': 
        tags = T.objects.all()
        #the same as in add scrap code, here we don't use form because tags in from is required
        #AddNForm = create_model_form("AddNForm_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=tags)})     
        n = N()  
        post = request.POST.copy()
        url = post.get('url')
        if N.objects.filter(url=url).exists():            
            return render_to_response("include/notes/addNote_result.html",{'message':_('This bookmark aready exists! You can close this window, or it will be closed for you in 2 seconds.')})
        tag_names = post.getlist('item[tags][]')        
        tags = []
        for tag_name in tag_names:
            t, created = T.objects.get_or_create(name=tag_name)
#===============================================================================
#            
#            if created or not w.tags.filter(name=t.name).exists():
#                w.tags.add(t)
#===============================================================================
            #tags.append(t.id)
            tags.append(t.name) 
        
#===============================================================================
#        if not tag_names:
#            tags = [T.objects.get(name='untagged').id]
#===============================================================================
#===============================================================================
#        post.setlist('tags', tags)
#        
#        f = AddNForm(post, instance=n)        
#        log.debug("f.errors:"+str(f.errors))
#        f.save()
#===============================================================================

        if not tags or (len(tags) == 1 and tags[0] == u''):
            tags = None
        n.title = post.get('title')
        n.desc = post.get('desc')
        n.url = post.get('url')
        private = post.get('private', False)
        if private in ['true', 'on']:
            n.private = True
        else:
            n.private = False     
        #n.private = post.get('private', False)

        n.vote = post.get('vote')
        n.save()
        n.add_tags(tags, 'bookmarkbook') 
        n.save()        
        return render_to_response("include/notes/addNote_result.html",{'message':_('Bookmark is successfully added! You can close this window, or it will be closed for you in 1 second.')})
       
    else:
        tags = __get_ws_tags(request, username, 'bookmarkbook')  
        from django.forms import TextInput
        #by adding the tags field specifically here, we avoided it using tags of another user (a strange error which repeat even after changing class names and variable names)
        AddNForm = create_model_form("AddNForm_"+str(username), N, fields={},#{'tags':forms.ModelMultipleChoiceField(queryset=tags)},
                                                             options={'exclude':['deleted'],
                                                             'fields':['url','title','tags','desc','vote','private'],
                                                             'widgets':{'title': TextInput(attrs={'size': 60}),
                                                                       }})
        url = request.GET.get('url')
        if N.objects.filter(url=url).exists():
            b = N.objects.get(url=url)
            #addNoteForm = AddNForm(initial={'url': url, 'title':b.title, 'tags': b.tags.all()})
            existing = True         
            return render_to_response('bookmarkbook/notes/addNote.html', {'existing':existing, 'url':url, 'id':b.id, 'title':b.title}, context_instance=RequestContext(request)) 
        
        
        title = request.GET.get('title')          
        #default_tag_id = T.objects.get(name='untagged').id 
        addNoteForm = AddNForm(initial={'url': url, 'title':title#, 'tags': [default_tag_id]
                                        })        
        return render_to_response('bookmarkbook/notes/addNote.html', {'addNoteForm': addNoteForm, 'url':url, 'tags':tags}) #TODO:how to display url using the form's initial
    







from notebook.bookmark import import_only_a, import_with_tags2, import_delicious

#TODO: handle other types of files. So far can only import Firefox bookmark html file.
@login_required
def import_bookmark(request):
    username = request.user.username
    if request.method == 'POST':         
        bookmark_file = request.FILES.get('bookmark')  
        ignore_folders = request.POST.get('ignore_folders')
        from_delicious = request.POST.get('from_delicious')
        default_vote = request.POST.get('vote', 0)
        #TODO: make the two below a list instead of just one
        common_tag = request.POST.get('common_tag')
        common_ws = request.POST.get('common_ws')
        if ignore_folders:
            count_urls_in_file, count_note_created, duplicate = import_only_a(username, bookmark_file, default_vote, common_tag, common_ws)
            count_tag_created = 0
        elif from_delicious:
            count_urls_in_file, count_note_created, duplicate, count_tag_created = import_delicious(username, bookmark_file, default_vote, common_tag, common_ws) 
        else:
            count_urls_in_file, count_note_created, duplicate, count_tag_created = import_with_tags2(username, bookmark_file, default_vote, common_tag, common_ws) 
        
        return render_to_response('bookmarkbook/import_success.html', {'profile_username':username, 'ignore_folders':ignore_folders, 'count_urls_in_file':count_urls_in_file,                                                                              
                                                                             'count_note_created':count_note_created, 'duplicate':duplicate, 'count_tag_created':count_tag_created},
                                                  context_instance=RequestContext(request,{'bookname': 'bookmarkbook','aspect_name':'bookmarks'}))

    else:
        return render_to_response('bookmarkbook/import.html',{'profile_username':username,},context_instance=RequestContext(request, {'bookname': 'bookmarkbook','aspect_name':'bookmarks'}))




