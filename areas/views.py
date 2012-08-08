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
from notebook.notes.views import __get_pre_url, getlogger, __get_view_theme 
from notebook.notes.util import *

log = getlogger('areas.views')  





class AddAreaForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Area  
        

    


def index(request, username): 
    print  'username',username
    if request.method == 'POST': 
        post = request.POST.copy()
        print 'post', post  
        
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
        
        
    areas = Area.objects.using(username).all()
    #Just getting tag frames is enought.  Pure tags shouldn't be made as root tag tree
    tags = Tag_Frame.objects.using(username).all().order_by('name')
    addAreaForm = AddAreaForm()
    #TODO: think of applying other view theme in addition to private
    theme = __get_view_theme(request)
    private =    theme['private'] 
    #print 'private', private
    return render_to_response('areas/index.html',{'areas':areas, 'addAreaForm':addAreaForm, 'tags':tags, \
                            'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))
    
    

def area(request, username, areaname):     
    area = Area.objects.using(username).get(name=areaname)
    area.owner_name = username
    tags = Tag_Frame.objects.using(username).all().order_by('name')
    #TODO:need this?
    theme = __get_view_theme(request)
    private =    theme['private'] 
    return render_to_response('areas/area.html',{'area':area,  'tags':tags, \
                            'username':request.user.username,'profile_username':username,  'private':private}, \
                    context_instance=RequestContext(request,  {}))