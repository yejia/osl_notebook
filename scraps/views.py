from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.forms import ModelForm
from django.db.models import F
from django.db import connection
from django.utils import simplejson
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mass_mail
from django.utils.translation import ugettext as _

from notebook.notes.models import create_model, create_model_form
from notebook.scraps.models import Scrap, Folder
from notebook.notes.views import getT, getW, getNote, get_public_notes, get_public_tags, remove_private_tag_notes, __get_ws_tags 
from notebook.notes.views import folders_index, settings_tag_add, settings_tag_update, settings_tag, settings_tags
from notebook.notes.views import getSearchResults, getlogger,  __getQStr, __get_notes_context
from notebook.notes.views import __get_folder_context, __get_pre_url

import notebook

import datetime
from datetime import date



log = getlogger('scraps.views')


#this method is used for processing the request users send via the browser button    
@login_required 
def add_scrap(request):
    username = request.user.username
    N = getNote(username, 'scrapbook')
    T = getT(username)
    W = getW(username)
    w = W.objects.get(name='scrapbook')  
    if request.method == 'POST': 
            tags = T.objects.all()
            AddNForm = create_model_form("AddNForm_add_scrap_post_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=tags)})     
            n = N() 
            post = request.POST.copy()
            tag_names = post.getlist('item[tags][]')
            tags = []
            for tag_name in tag_names:
                t, created = T.objects.get_or_create(name=tag_name)
                if created or not w.tags.filter(name=t.name).exists():
                    w.tags.add(t)
                tags.append(t.id)    
            
            if not tag_names:           
                tags = [T.objects.get(name='untagged').id]
            post.setlist('tags', tags) 
            f = AddNForm(post, instance=n)
            log.debug("f.errors:"+str(f.errors))
            #TODO:handle errors such as url broken
            f.save()
            n.save() #called this specifically to save the url to the social db as well
            return render_to_response("include/notes/addNote_result.html",\
                                      {'message':_('Scrap is successfully added! You can close this window, or it will be closed for you in 1 second.')})
       
    else:
        
        tags = __get_ws_tags(request, username, 'scrapbook')        
        
        from django.forms import TextInput
        #by adding the tags field specifically here, we avoided it using tags of another user (a strange error which repeat even after changing class names and variable names)
        AddNForm_scrap = create_model_form("AddNForm_add_scrap_get_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=tags)}, options={'exclude':['deleted'],
                                                             'fields':['url','title','tags','desc','vote','private'],
                                                             'widgets':{'title': TextInput(attrs={'size': 80}),
                                                                       }})
        
        url = request.GET.get('url')
        title = request.GET.get('title')
        desc = request.GET.get('desc')
       
        default_tag_id = T.objects.get(name='untagged').id  
        addNoteForm = AddNForm_scrap(initial={'url': url, 'title':title, 'desc':desc, 'tags': [default_tag_id]})
        #no need of the custimized form in the scrapbook template
        return render_to_response('scrapbook/notes/addNote.html', {'addNoteForm': addNoteForm, 'desc':desc, 'url':url, 'tags':tags})
    
   
    

@login_required
def share(request, username):   
    print 'share in note called'   
    note_ids = request.POST.getlist('note_ids')   
    N = getNote(username)   
    msgs = [] 
    for note_id in note_ids:         
        note = N.objects.get(id=note_id)  
        message = 'From osl scraps:'+' '+note.title+' '+note.url+'  '
        desc = note.desc
        desc = desc.replace('\r','')
        desc = desc.replace('\n','')#TODO:
        if len(desc) > 100:
            desc = desc[:300] + '...... view more from http://new.notebook.opensourcelearning.org/'+\
                                username+'/scrapbook/scraps/note/'+unicode(note.id)+'/'
        
        message = message+desc
        msg = (message.encode('utf8'), '', 'yuanliangliu@gmail.com', ['buzz@gmail.com'])   
        msgs.append(msg)         
        #share_note(note_id, username)
    send_mass_mail(tuple(msgs), fail_silently=False) 
    return HttpResponse('success', mimetype="text/plain")  

    


