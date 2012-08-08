# -*- coding: utf-8 -*-

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from notebook.tags.models import Tag_Frame
from notebook.notes.models import Frame
from notebook.social.models import Group


class Area(models.Model):
    name = models.CharField(max_length=150)
    private = models.BooleanField(default=False)
    desc =  models.TextField(blank=True, max_length=2000)
    root_tag_frame = models.ForeignKey(Tag_Frame, blank=True)
    root_note_frame = models.ForeignKey(Frame, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = (('name'),)# ('name', 'root_tag_frame', 'root_note_frame'),) 
        
    def __unicode__(self):
        return self.name
        
    
    def get_pushed_tag_frames(self):
        Area_Tag_Frame.objects.using(self.owner_name).filter(area=self)
    
    def get_pushed_note_frames(self):
        Frame.objects.using(self.owner_name).filter(tags='sharingarea:'+self.name)
    
#    def get_pulled_tag_frames(self):
#        pass
    
    #pulled frames are those that have tags in the area's root tag tree.
    def get_pulled_note_frames(self):
        pass           


#store tag_frame that 
class Area_Tag_Frame(models.Model):
    area = models.ForeignKey(Area)
    tag_frame = models.ForeignKey(Tag_Frame)
    #root = models.BooleanField(default=False)
    
    
    
#can one class join several areas?
class Area_Group(models.Model):
    area = models.ForeignKey(Area)
    group = models.ForeignKey(Group)
   
    
class Meta:
    verbose_name = "group in area"                   


    def __unicode__(self):
        return self.area.name + '-' + self.group.name   
    
    