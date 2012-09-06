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
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, FieldError


from notebook.salons.models import *




    

class AddSalonForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'    
    class Meta:
        model = Salon  
        exclude = ('private', 'last_modi_date', 'status', 'fee') 
        

def group_salons(request, groupname):
    if request.method == 'POST': 
        s = Salon()
        s.fee = 0
        addSalonForm = AddSalonForm(request.POST, instance=s) 
        print 'form errors:', str(addSalonForm.errors)
        addSalonForm.save()
        
    salons = Salon.objects.all() 
    group = Group.objects.get(name=groupname)
    addSalonForm = AddSalonForm(initial={'creator': request.user.member, 'group':group})
    
    
    return render_to_response('salons/index.html',{'salons':salons, 'addSalonForm':addSalonForm, 
                                                   'groupname':groupname,
                                                   'group':group}, \
                    context_instance=RequestContext(request,  {}))
    
    
    
def group_salon(request, groupname, salon_name):   
     salon = Salon.objects.get(group__name=groupname, name=salon_name) 
     editSalonForm = AddSalonForm(instance=salon)
     group = Group.objects.get(name=groupname)
     return render_to_response('salons/salon.html',{'salon':salon, 'editSalonForm':editSalonForm, 
                                                   'groupname':groupname,
                                                   'group':group}, \
                    context_instance=RequestContext(request,  {}))