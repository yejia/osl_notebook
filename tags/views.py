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
from notebook.social.models import Group_Tag_Frame, Group
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
    return render_to_response('tagframes/index.html',{'tag_tree':tag_tree, 'top_tag_trees':top_tag_trees,'addTagFrameForm':addTagFrameForm, \
                            'tags':tags, 'sort':'', 'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))



def tagframe(request, username, tagframe_name):
     tf = Tag_Frame.objects.using(username).get(name=tagframe_name)
     tags = Tag.objects.using(username).all().order_by('name')
     #TODO: need this?
     theme = __get_view_theme(request)
     private =    theme['private'] 
     #print 'private', private     
     return render_to_response('tagframes/tagframe.html',{'tag_tree':tf,\
                            'tags':tags, 'sort':'', 'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))




def push_tag_frame_2_groups(request, username, tagframe_name):
    tf = Tag_Frame.objects.using(username).get(name=tagframe_name)
    group_names = request.POST.getlist('item[tags][]')
    groups = Group.objects.filter(name__in=group_names)
    #group_ids = [g.id for g in groups]
    for group in groups:
        Group_Tag_Frame.objects.get_or_create(group=group, tag_frame_id=tf.id, tag_frame_owner=request.user.member)
    return HttpResponseRedirect(__get_pre_url(request)) 

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


#TODO: check if request.user.usrename = username 
#@user_passes_test(lambda u: u.username==username)
def add_tags_2_frame(request, username):
    parent_name = request.GET.get('parent_name')    
    tags_to_add = request.GET.get('tags_to_add')   
    
    TF = getTagFrame(username)
    parent_frame = TF.objects.get(name=parent_name)
    __add_tags_2_frame(parent_frame, tags_to_add, username)
    return HttpResponse('successful', mimetype="text/plain")  
    

#TODO: username should be obtained from parent_frame.owner_name
def __add_tags_2_frame(parent_frame, tags_to_add, username):    
    for tag in tags_to_add.split(','):        
        __create_tag_frame(tag, username)        
    parent_frame.add_tags(tags_to_add)
    
    
def __create_tag_frame(tag_name, username):
    #handling tag frame and tag creation here
    TF = getTagFrame(username)
    if Tag.objects.using(username).filter(name=tag_name).exists():           
            #if the tag already exists, and tag_frame doesn't exist yet, create only the tag_frame
            if not TF.objects.filter(name=tag_name).exists():
                t = Tag.objects.using(username).get(name=tag_name)
                cursor = connections[username].cursor()       
                print 'The following query will be executed:', 'insert into tags_tag_frame (tag_ptr_id, current) values('+str(t.id)+',FALSE)'
                #sqlite has no TRUE/FALSE as its boolean value, it use 0, 1. postgresql accepts both.          
                cursor.execute("insert into tags_tag_frame (tag_ptr_id, current) values("+str(t.id)+", '0')")                
                #it seems that unlike raw sql delete, even without using=username, the transaction is still commited
                transaction.commit_unless_managed(using=username)  
    else:
        tf = TF(name=tag_name)
        tf.save()     
    return TF.objects.get(name=tag_name)


def remove_frame(request, username):   
    parent_name = request.POST.get('parent_name')    
    tag_name = request.POST.get('tag_name')
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
    tag_name = tag_list[-1]   
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
    #username is the profile username from who you want to import the tag tree
    tag_frame_name = request.GET.get('tag_frame_name')  
    force = request.GET.get('force') 
    if request.user.username == username:                  
        return HttpResponse(simplejson.dumps({'type':'error','msg':_('You cannot import tag tree into your own notebook!')}), "application/json")
    else:
        TF = getTagFrame(username)
        tf = TF.objects.get(name=tag_frame_name)
        TFU = getTagFrame(request.user.username)
        #Only warn for the top tag in the tree. For the children and grandchildren, if the user want to import, just merge if user already has in his notebook
        if TFU.objects.filter(name=tag_frame_name).exists() and  force not in true_words:
            #TODO: allow changing the name of the tag
            return HttpResponse(simplejson.dumps({'type':'warning','msg':_('You already have a tag tree of this name in your own notebook!')}), "application/json")
        else:
            #TODO:possible conflicts with the users' own tag trees (for example, if the user alreayd have a tag frame with the same name but with different children)
            #prompt to tell the user s/he already has a tag tree with such a name, and does s/he want to rename the new or the old one? Or replace the old one? Or merge with the old one?
            #For now, the implementation of tag frame will merge the two automatically by default.  
            export_tree(tf, request.user.username)
            
                
        if force in true_words:   
            messages.success(request, _("You have successfully imported the tag tree into your own notebook!")) 
            return HttpResponseRedirect(__get_pre_url(request)) 
        return  HttpResponse(simplejson.dumps({'type':'success','msg':_('You have successfully imported the tag tree into your own notebook!')}), "application/json")


def export_tree(tf, import_user_username):    
    tag_frame_name = tf.name
    owner_name = tf.owner_name
    #print 'tag_frame_name', tag_frame_name
    tfu = __create_tag_frame(tag_frame_name, import_user_username)  
    #print 'tfu', tfu
           
    tags_to_add = ','.join([t.name for t in tf.get_public_tags_in_order()])   
    #print 'tags_to_add', tags_to_add        
    __add_tags_2_frame(tfu, tags_to_add, import_user_username) 
    for tfchild in tf.get_public_tags_in_order(): 
        #print 'tfchild:', tfchild
        #print  'tfchild.tag_frame:', tfchild.tag_frame
        tfchild.tag_frame.owner_name = owner_name
        export_tree(tfchild.tag_frame, import_user_username)
                      