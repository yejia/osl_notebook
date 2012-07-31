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
from notebook.notes.views import __get_pre_url, getlogger, __get_view_theme, __get_related_tags

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
    
    #print 'tag_trees', top_tag_trees
    
    
    #TODO: think of applying other view theme in addition to private
    theme = __get_view_theme(request)
    private =    theme['private'] 
    #print 'private', private
    return render_to_response('tagframe/index.html',{'tag_tree':tag_tree, 'top_tag_trees':top_tag_trees,'addTagFrameForm':addTagFrameForm, \
                            'tags':tags, 'sort':'', 'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))



#===============================================================================
# def add_tag_frame(request, username):
#    post = request.POST.copy()  
#    TF = getTagFrame(username)
#    tf = TF()
#    name = post.get('name')
#    if Tag.objects.using(username).filter(name=name).exists():
#        if not TF.objects.filter(name=name).exists():
#            t = Tag.objects.using(username).get(name=name)
#            cursor = connections[username].cursor()
#            cursor.execute('insert into tags_tag_frame (tag_ptr_id, current) values('+str(t.id)+',FALSE)')
#            transaction.commit_unless_managed(using=username)  
#        tf = TF.objects.get(name=name)
#    else:
#        f = AddTagFrameForm(post, instance=tf)
#        if not f.is_valid(): 
#            log.debug("add tag frame form errors:"+str(f.errors))            
#        else:
#            f.save()  
#    parent_name =  post.get('parent_name')
#    if parent_name:
#        parent_node = TF.objects.get(name=parent_name)
#        FTS = getFrameTags(username)
#        fts = FTS(frame=parent_node,tag=tf)
#        fts.save()
#    return HttpResponseRedirect(__get_pre_url(request))  
#===============================================================================



def add_tags_2_frame(request, username):
    parent_name = request.GET.get('parent_name')    
    tags_to_add = request.GET.get('tags_to_add')   
    
    TF = getTagFrame(username)
    parent_frame = TF.objects.get(name=parent_name)
    __add_tags_2_frame(parent_frame, tags_to_add)
    return HttpResponse('successful', mimetype="text/plain")  
    

def __add_tags_2_frame(parent_frame, tags_to_add):    
    for tag in tags_to_add.split(','):        
        #handling tag frame and tag creation here
        if Tag.objects.using(username).filter(name=tag).exists():
            #print 'tag existing'
            #if the tag already exists, and tag_frame doesn't exist yet, create only the tag_frame
            if not TF.objects.filter(name=tag).exists():
                #print 'tf not existing'
                t = Tag.objects.using(username).get(name=tag)
                cursor = connections[username].cursor()
                #print 'executing insert sql: ', 'insert into tags_tag_frame (tag_ptr_id, current) values('+str(t.id)+',FALSE)'
                cursor.execute('insert into tags_tag_frame (tag_ptr_id, current) values('+str(t.id)+',FALSE)')
                #print 'executed successfully'
                #it seems that unlike raw sql delete, even without using=username, the transaction is still commited
                transaction.commit_unless_managed(using=username)  
        else:
            tf = TF(name=tag)
            tf.save()     
    parent_frame.add_tags(tags_to_add)


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
    if tf.note_set.all():
        #if there are notes that have this tag, just make this tag a pure tag
        #ftf = Fake_Tag_Frame.objects.using(username).get(name=frame_name)
        #ftf.delete()
        cursor = connections[username].cursor()
        #print 'executing query:  ', "DELETE FROM tags_tag_frame WHERE tag_ptr_id in (select id from tags_tag  where name='"+frame_name+"')"
        #the parent child relation is still kept in the frame_tags table.
        cursor.execute("DELETE FROM tags_tag_frame WHERE tag_ptr_id in (select id from tags_tag  where name='"+frame_name+"')")
        transaction.commit_unless_managed(using=username)        
    else:
        #print 'deleting the tag and tag frame together'
        #this doesn't seem to delete the tag as well although the frame did get deleted, Why? TODO:
        #Is the parent child relation is still kept in the frame_tags table? TODO:
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
    
    #N = getNote(username, bookname)
    #n_list = N.objects.filter(tags__name=tag_name)    
    #if len(n_list) > 100:
#===============================================================================
#        q = request.GET.copy()
#        q.update({'q':'t:'+tag_list[-2]})
#        request.GET = q
#===============================================================================        
        #request.limited_list = tag_list[-2:]
       
    return tags(request, username, bookname, tag_name, 'notes')


def get_related_tags(request, username):
    tag_name = request.POST.get('tag_name')
    related = __get_related_tags(username, tag_name)  
    result = {'tag_name':tag_name, 'related_tags':related}      
    return HttpResponse(simplejson.dumps(result), "application/json")


def export(request, username):
    tag_frame_name = request.GET.get('tag_frame_name')
    if request.user.username == username:
        return HttpResponse(simplejson.dumps({'type':'Error','msg':_('You cannot import tag tree into your own notebook!')}), "application/json")
    else:
        TF = getTagFrame(username)
        tf = TF.objects.get(name=frame_name)
        TFU = getTagFrame(request.user.username)
        if TFU.objects.filter(name=frame_name).exists():
            #TODO: allow changing the name of the tag
            return HttpResponse(simplejson.dumps({'type':'Error','msg':_('You already have a tag tree of this name in your own notebook!')}), "application/json")
        else:
            #TODO:possible conflicts with the users' own tag trees (for example, if the user alreayd have a tag frame with the same name but with different children)
            for tag in tf.tags.all():
                add_tags_2_frame(request, username) 