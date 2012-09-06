# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext as _

from notebook.social.models import Member, Group, get_storage_loc, fs
from notebook.areas.models import Area
from notebook.notes.constants import *


#salon is per group? TODO:
class Salon(models.Model):
    STATUS_CHOICES = (        
        ('p', 'pending'),
        ('a', 'active'),        
        ('e', 'expired'),        
    )  
    #creator has to be the group admin
    creator = models.ForeignKey(Member)
    #area =  models.ForeignKey(Area)
    group =  models.ForeignKey(Group)
    name = models.CharField(max_length=150)
    #have private salons? TODO:
    private = models.BooleanField(default=False)
    desc =  models.TextField(max_length=9000)
    location = models.TextField(max_length=2000)
    max_people = models.IntegerField(default=0, blank=True)
    min_people = models.IntegerField(default=0, blank=True)
    start_date = models.DateTimeField('Starting date', auto_now_add=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES) 
    group_only =  models.BooleanField(default=True)
    fee =  models.IntegerField(default=0, blank=True)
    poster = models.ImageField(upload_to=get_storage_loc,blank=True, storage=fs, verbose_name=ugettext_lazy('Poster')) 
    #TODO:tags?
    #tags = 
    
    class Meta:
        ordering = ['name']
        unique_together = (('name', 'group'),)# ('name', 'root_tag_frame', 'root_note_frame'),) 
        
    def __unicode__(self):
        return self.name
        




class Salon_Signup(models.Model):
    STATUS_CHOICES = (        
        ('y', 'yes'),
        ('n', 'no'),
        ('m', 'maybe'),        
    )  
    #member has to be group member first
    member = models.ForeignKey(Member)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True) 
    
    