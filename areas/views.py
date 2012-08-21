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



from notebook.areas.models import *
from notebook.notes.views import __get_pre_url, getlogger, __get_view_theme, __getQStr, getSearchResults, __get_context 
from notebook.notes.util import *
from notebook.notes.constants import *


log = getlogger('areas.views')  





class AddAreaForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Area  
        

    


def index(request, username): 
    #print  'username',username
    if request.method == 'POST': 
        post = request.POST.copy()
        #print 'post', post  
        
        #copied from social.views.groups()
        tag_names = post.getlist('item[tags][]')
        tag_ids = [Tag_Frame.objects.using(username).get(name=tag_name).id for tag_name in tag_names]  
               
         
        A = getArea(username)
        a = A()
        a.owner_name = username
#===============================================================================
#        addAreaForm = AddAreaForm(post, instance=a)
#        if not addAreaForm.is_valid(): 
#            log.debug("add area form errors:"+str(addAreaForm.errors))            
#        else:
#            addAreaForm.save()       
#===============================================================================
        a.name = post.get('name')
        a.desc = post.get('desc')
        a.private = post.get('private', False)
        #TODO: warn of empty root_note_frame and root_tag_frame. They cannot be null
        if post.get('root_note_frame'):
            a.root_note_frame = Frame.objects.using(username).get(id=post.get('root_note_frame'))
        if tag_ids:  
            a.root_tag_frame = Tag_Frame.objects.using(username).get(id=tag_ids[0])  
        a.save()   
    if request.user.username == username:
        areas = Area.objects.using(username).all()    
    else:
        areas = Area.objects.using(username).filter(private=False)    
    
    #Just getting tag frames is enought.  Pure tags shouldn't be made as root tag tree
    tags = Tag_Frame.objects.using(username).all().order_by('name')
    addAreaForm = AddAreaForm()
    #TODO: think of applying other view theme in addition to private
    #theme = __get_view_theme(request)
    profile_member = Member.objects.get(username=username)
    private = profile_member.viewing_private    
    #print 'private', private
    return render_to_response('areas/index.html',{'areas':areas, 'addAreaForm':addAreaForm, 'tags':tags, \
                            'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))
    
    

def area(request, username, areaname):  
    if request.method == 'POST': 
        #below copied from index. merge. TODO:
        post = request.POST.copy()
        tag_names = post.getlist('item[tags][]')
        tag_ids = [Tag_Frame.objects.using(username).get(name=tag_name).id for tag_name in tag_names]         
        A = getArea(username)
        a = A.objects.get(id=post.get('id'))
        a.owner_name = username
        a.name = post.get('name')
        a.desc = post.get('desc')
        a.private = post.get('private', False)
        #TODO: warn of empty root_note_frame and root_tag_frame. They cannot be null
        if post.get('root_note_frame'):
            a.root_note_frame = Frame.objects.using(username).get(id=post.get('root_note_frame'))
        if tag_ids:  
            a.root_tag_frame = Tag_Frame.objects.using(username).get(id=tag_ids[0])  
        a.save() 
           
    
    area = Area.objects.using(username).get(name=areaname)
       
    area.owner_name = username
    area.root_tag_frame.owner_name = username
    area.root_note_frame.owner_name = username
    #tags = Tag_Frame.objects.using(username).all().order_by('name')
    area_tags =  Tag.objects.using(username).filter(name__in=area.root_tag_frame.get_offsprings())
    area_tags_with_count = []
    for t in area_tags:
        note_list = Note.objects.using(username).filter(tags__name = t.name)
        area_tags_with_count.append([t, note_list.count()])
    
    groups = Group.objects.exclude(id__in=[g.id for g in area.get_groups()])
    editAreaForm = AddAreaForm(instance=area)
    tags = Tag_Frame.objects.using(username).all().order_by('name')

        
    #TODO:need this?
    theme = __get_view_theme(request)
    private =    theme['private'] 
    return render_to_response('areas/area.html',{'area':area,  'area_tags_with_count':area_tags_with_count, 'editAreaForm':editAreaForm,'tags':tags, \
                            'username':request.user.username,'profile_username':username,  'private':private, 'groups':groups}, \
                    context_instance=RequestContext(request,  {'book_uri_prefix':'/'+username+'/areas/area/'+area.name}))
    
 

def add_groups_2_area(request,username, areaname):
    area = Area.objects.using(username).get(name=areaname)
    area.owner_name = username
    group_names = request.POST.getlist('item[tags][]')
    groups = Group.objects.filter(name__in=group_names)
    group_ids = [g.id for g in groups]
    area.add_groups(group_ids)
    return HttpResponseRedirect(__get_pre_url(request)) 
    
    

def remove_group_from_area(request,username, areaname):
    print 'delete_group'
    group_id = request.POST.get('group_id')
    area = Area.objects.using(username).get(name=areaname)
    area.owner_name = username
    area.remove_group(group_id)
    return HttpResponse(simplejson.dumps({'type':'success','msg':_('You have successfully removed the group from the area.')}), "application/json")
    
    
    
    
def area_notes(request, username, areaname, bookname):  
    area = Area.objects.using(username).get(name=areaname)
    area.owner_name = username
    note_list = area.get_notes(bookname)
    qstr = __getQStr(request)    
    note_list  = getSearchResults(note_list, qstr)
    
    
    
    default_tag_id = Tag.objects.using(username).get(name='untagged').id    
    context = __get_context(request, note_list, default_tag_id, username, bookname)
    context['area'] = area
     
    
    #context['tags'] = tags
    #profile_member = 
    return render_to_response(book_template_dict.get(bookname)+'notes/notes.html', context, \
                              context_instance=RequestContext(request,{'bookname': bookname,'book_uri_prefix':'/'+username, 'appname':'areas'}))
    
    
    
def get_area_tags(request, username, areaname, bookname):  
    print 'get_area_tags'
    area = Area.objects.using(username).get(name=areaname)
    area.owner_name = username
    area.root_tag_frame.owner_name = username
    tags = area.root_tag_frame.get_offsprings()
    tags_return = []
    for tag in tags:
        count = Note.objects.using(username).filter(tags__name=tag).count()
        t = {'name':tag, 'note_count':count}
        tags_return.append(t)
    return HttpResponse(simplejson.dumps(tags_return), "application/json")
        