# -*- coding: utf-8 -*-

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from notebook.tags.models import Tag_Frame
from notebook.notes.models import Frame, create_model
from notebook.social.models import Group
from notebook.notes.util import book_model_dict, getNote
from notebook.notes.constants import *




def getArea(username):
    return create_model("Area"+str(username), Area, username)


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


    #TODO: private ones? 
    def get_all_tags(self):
        self.root_tag_frame.owner_name = self.owner_name
        area_tags_names = self.root_tag_frame.get_offsprings()
        area_tags_names.append(self.root_tag_frame.name)
        area_tags_names = [t for t in area_tags_names if t not in system_tags]        
        area_tags_names.sort()
        return area_tags_names
        
        


    def get_notes(self, bookname='notebook'):
        self.root_tag_frame.owner_name = self.owner_name
        tag_names = self.get_all_tags()
        q = Q(tags__name__in=tag_names) 
        N = getNote(self.owner_name, bookname)
        note_list = N.objects.using(self.owner_name).filter(deleted=False)
        note_list =  note_list.filter(q)        
        return note_list.distinct() 
   
   
    def get_public_notes(self, bookname='notebook'):
        note_list = self.get_notes(bookname)
        note_list.filter(private=False)
        return note_list
 

    

    def get_snippets(self):
        return self.get_notes('snippetbook')

    def get_public_snippets(self):
        return self.get_public_notes('snippetbook')    


    def get_public_bookmarks(self):
        return self.get_public_notes('bookmarkbook')
    
    
    def get_public_scraps(self):
        return self.get_public_notes('scrapbook')
    
    
    def get_public_frames(self):
        return self.get_public_notes('framebook')
        
    
    def get_groups(self):
        ags = Area_Group.objects.using(self.owner_name).filter(area=self)
        return Group.objects.filter(id__in=[ag.group_id for ag in ags])
    
    
    def add_groups(self, group_ids):
        for group_id in group_ids:
            a, created = Area_Group.objects.using(self.owner_name).get_or_create(area=self, group_id=group_id)
            
    
    def remove_group(self, group_id):
        ag = Area_Group.objects.using(self.owner_name).get(area=self, group_id=group_id)
        ag.owner_name = self.owner_name
        ag.delete()
            
    
        
#store tag_frame that 
class Area_Tag_Frame(models.Model):
    area = models.ForeignKey(Area)
    tag_frame = models.ForeignKey(Tag_Frame)
    #root = models.BooleanField(default=False)
    
    
    
#can one class join several areas?
class Area_Group(models.Model):
    area = models.ForeignKey(Area)
    #reference to the id of the group in the social db. Since they are on different db, foreign key cannot be used.TODO:
    group_id = models.IntegerField()
   
    
class Meta:
    verbose_name = "group in area"                   


    def __unicode__(self):
        return self.area.name + '-' + self.group_id   
    
    