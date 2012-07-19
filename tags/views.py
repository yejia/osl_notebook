# -*- coding: utf-8 -*-

from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.forms import ModelForm
from django.db.models import Q, F, Avg, Max, Min, Count
from django.db import connection
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils import simplejson
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.sites.models import Site
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.core.mail import send_mass_mail

from django.db import connections,  transaction



from notebook.tags.models import *
from notebook.notes.constants import *
from notebook.notes.util import *
from notebook.notes.views import __get_pre_url, getlogger, __get_view_theme

log = getlogger('tags.views')  




class AddTagFrameForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Tag_Frame  
        exclude = ('tags', 'current')    
        


def index(request, username):
    
    tag_tree, created = Tag_Frame.objects.using(username).get_or_create(name='Root')
    addTagFrameForm = AddTagFrameForm()
    tags = Tag.objects.using(username).all().order_by('name')
    
    top_tag_trees = []
    for tf in Tag_Frame.objects.using(username).all():
        tf.owner_name = username
        if tf.name != 'Root' and not tf.in_frames.all():
            top_tag_trees.append(tf)   
    
    print 'tag_trees', top_tag_trees
    
    
    #TODO: think of applying other view theme in addition to private
    theme = __get_view_theme(request)
    private =    theme['private'] 
    #print 'private', private
    return render_to_response('tagframe/index.html',{'tag_tree':tag_tree, 'top_tag_trees':top_tag_trees,'addTagFrameForm':addTagFrameForm, \
                            'tags':tags, 'sort':'', 'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))


def add_tag_frame(request, username):
    post = request.POST.copy()  
    #tag_names = post.getlist('item[tags][]')
    #tag_ids = [ST.objects.get(name=tag_name).id for tag_name in tag_names]         
    #post.setlist('tags', tag_ids) 
    
    
    #tf, created = Tag_Frame.objects.using(username).get_or_create(name=post.get('name'))
    TF = getTagFrame(username)
    tf = TF()
#===============================================================================
#    if not created:
#        pass #TODO:
#    tf.desc = post.get('desc')
#    tf.private = post.get('private', False)
#===============================================================================
    name = post.get('name')
    if Tag.objects.using(username).filter(name=name).exists():
        if not TF.objects.filter(name=name).exists():
            t = Tag.objects.using(username).get(name=name)
            cursor = connections[username].cursor()
            cursor.execute('insert into tags_tag_frame (tag_ptr_id, current) values('+str(t.id)+',FALSE)')
            transaction.commit_unless_managed()
            #tf = TF.objects.raw('insert into tagframe_frame_tags (tag_ptr_id, current) values('+str(t.id)+',FALSE)')
        tf = TF.objects.get(name=name)
    else:
        f = AddTagFrameForm(post, instance=tf)
        if not f.is_valid(): 
            log.debug("add tag frame form errors:"+str(f.errors))            
        else:
            f.save()  
    #tf.save()
    parent_name =  post.get('parent_name')
    #print 'parent:', parent_name
    if parent_name:
        parent_node = TF.objects.get(name=parent_name)
        FTS = getFrameTags(username)
        fts = FTS(frame=parent_node,tag=tf)
        fts.save()
    return HttpResponseRedirect(__get_pre_url(request))  



def add_tags_2_frame(request, username):
    parent_name = request.GET.get('parent_name')    
    tags_to_add = request.GET.get('tags_to_add')    
    TF = getTagFrame(username)
    parent_node = TF.objects.get(name=parent_name)
    parent_node.add_tags(tags_to_add)
    return HttpResponse('successful', mimetype="text/plain")  
    


def remove_frame(request, username):   
    parent_name = request.POST.get('parent_name')
    #print 'parent_name', parent_name
    tag_name = request.POST.get('tag_name')
    #print 'tag_name', tag_name    
    #print 'username', username
    FTS = getFrameTags(username)
    fts = FTS.objects.get(frame__name=parent_name, tag__name=tag_name)
    fts.delete()
    return HttpResponse('successful', mimetype="text/plain") 


def delete_frame(request, username):
    frame_name = request.POST.get('frame_name')
    TF = getTagFrame(username)
    tf = TF.objects.get(name=frame_name)
    tf.delete()
    return HttpResponse('successful', mimetype="text/plain") 


from notebook.notes.views import tags

def notes_by_tag(request, username, tag_path, bookname):   
    tag_list = tag_path.split('-')
    #print tag_list
    tag_name = tag_list[-1]
    #print tag_name
    request.appname = 'tagframe'
    request.tag_path = tag_path
    return tags(request, username, bookname, tag_name, 'notes')
    