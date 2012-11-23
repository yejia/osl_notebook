# -*- coding: utf-8 -*-

import datetime

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
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, FieldError


from notebook.salons.models import *
from notebook.notes.views import __get_pre_url, getlogger



log = getlogger('salons.views')  


    

class AddSalonForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'    
    class Meta:
        model = Salon  
        exclude = ('private', 'last_modi_date', 'status', 'fee') 
        

def salons(request):    
    past = request.GET.get('past')
    if past and past=='y':
        salons = Salon.objects.filter(private=False).exclude(end_date__gte=datetime.date.today()).order_by('start_date', 'start_time')
    else:
        salons = Salon.objects.filter(private=False, end_date__gte=datetime.date.today()).order_by('start_date', 'start_time')
    return render_to_response('salons/index.html',{'salons':salons, 'past':past}, \
                    context_instance=RequestContext(request,  {}))


@login_required
def my_salons(request):    
    past = request.GET.get('past')
    signups = Salon_Signup.objects.filter(member=request.user.member).values_list('salon', flat=True)
    if past and past=='y':
        salons = Salon.objects.filter(private=False, id__in=signups).exclude(end_date__gte=datetime.date.today()).order_by('start_date', 'start_time')
    else:                
        salons = Salon.objects.filter(private=False, end_date__gte=datetime.date.today(), id__in=signups).order_by('start_date', 'start_time')
    return render_to_response('salons/my.html',{'salons':salons, 'past':past}, \
                    context_instance=RequestContext(request,  {}))


@login_required
def group_salons(request, groupid):
    group = Group.objects.get(id=groupid)
    if request.method == 'POST': 
        #TODO:check if end date is before start date, and so on
        post = request.POST.copy()  
        post['creator'] = request.user.member.id
        post['group'] = group.id  
        s = Salon()
        s.fee = 0
        addSalonForm = AddSalonForm(post, request.FILES,  instance=s) 
        log.debug('form errors:'+str(addSalonForm.errors))
        addSalonForm.save()
    past = request.GET.get('past')
    if past and past=='y':
        salons = Salon.objects.filter(group__name=group.name, private=False).exclude(end_date__gte=datetime.date.today()).order_by('start_date', 'start_time')     
    else:
        salons = Salon.objects.filter(group__name=group.name, private=False, end_date__gte=datetime.date.today()).order_by('start_date', 'start_time') 
    
    addSalonForm = AddSalonForm(initial={'creator': request.user.member.id, 'group':group.id})    
    
    return render_to_response('salons/group_salons.html',{'salons':salons, 'addSalonForm':addSalonForm, 
                                                   'groupname':group.name,
                                                   'group':group,'past':past}, \
                    context_instance=RequestContext(request,  {}))
    
    

@login_required
def group_salon_signup(request, groupid, salon_id): 
    salon = Salon.objects.get(group__id=groupid, id=salon_id) 
    group = Group.objects.get(id=groupid)
    signup = request.GET.get('signup')
    group.members.add(request.user.member)
    if signup == 'y':          
        salon.signup(request.user.username)    
    elif signup == 'm': 
        salon.maybe(request.user.username)  
    else:    
        salon.cancel(request.user.username)   
    
    return HttpResponseRedirect('/groups/'+groupid+'/salons/salon/'+salon_id+'/')  
    
    
def group_salon(request, groupid, salon_id):  
    salon = Salon.objects.get(group__id=int(groupid), id=salon_id) 
    group = Group.objects.get(id=groupid)
    if request.method == 'POST': 
        #check if the user has the permission to update this 
        if request.user.username == salon.creator.username: 
            post = request.POST.copy()  
            post['creator'] = salon.creator.id
            post['group'] = group.id     
            editSalonForm = AddSalonForm(post, request.FILES, instance=salon)
            #print ('form errors:'+str(editSalonForm.errors))
            editSalonForm.save()
    
         
    editSalonForm = AddSalonForm(instance=salon)
    if request.user.is_anonymous():
        is_in_group = False
    else:
        is_in_group =  request.user.member.is_in_group(group.name) 
    
    signed_ids = salon.get_signed()
    signed = Member.objects.filter(id__in=signed_ids)
    maybe_ids = salon.get_maybe()
    maybe = Member.objects.filter(id__in=maybe_ids)
    return render_to_response('salons/salon.html',{'salon':salon, 'editSalonForm':editSalonForm, 
                                                   'groupname':group.name, 'is_in_group': is_in_group,
                                                   'group':group, 'signed':signed, 'maybe':maybe}, \
                    context_instance=RequestContext(request,  {}))