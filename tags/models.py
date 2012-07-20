# -*- coding: utf-8 -*-

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

#TODO: remove WorkingSet later





#TODO: add delete field? add desc field?
class Tag(models.Model):
    name = models.CharField(max_length=150)
    private = models.BooleanField(default=False)
    desc =  models.TextField(blank=True, max_length=200)
    #deleted = models.BooleanField(default=False)
    
    
    
    
    #tag_id = models.IntegerField()
    #user = models.ForeignKey(User)
#    if not standalone:
#        objects = MultiUserManager(owner_name)

    class Meta:
        unique_together = (("name"),)           
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_working_sets(self):
        return self.workingset_set.filter(deleted=False)
    
    def get_working_sets_list(self):
        return self.get_working_sets.values_list('name', flat=True)



        #TODO:better to move this method and the next one outside of this class?
    def get_tag_type(self):
        try:
            self.tag_frame
            return 'Nonleaf'
        except ObjectDoesNotExist:   
            return 'Leaf' 
   
   
#===============================================================================
#    def get_tags_counts(self):
#        related = []
#        for t in Tag.objects.using(self.owner_name).exclude(name=self.name):            
#            related.append((t.name, Note.objects.using(self.owner_name).filter(tags__name__in = [self.name,t.name]).count()))
#        return related    
#===============================================================================
   
#===============================================================================
#    def get_snippets_count(self):  
#        if self.owner_name:
#            return Snippet.objects.using(owner_name).filter(tags=tag).count()
#        else:
#            return 0 
#        
#    
#    def get_public_snippets_count(self): 
#        pass               
#===============================================================================




#class Frame is for notes. And Tag_Frame is for putting tags in a frame
class Tag_Frame(Tag):
    tags = models.ManyToManyField(Tag, related_name='in_frames', through="Frame_Tags")     
    #TODO: at the most only one can have this to be true per user
    current = models.BooleanField(default=False)     
    #name = models.CharField(max_length=50)
    #desc =  models.TextField(blank=True, max_length=200)    
    #private = models.BooleanField(default=False)
    #deleted = models.BooleanField(default=False)
    #parent = models.ForeignKey(Tag_Frame)   

    class Meta:
        verbose_name = "tag frame"          
                


    def __unicode__(self):
        return self.name 
    
    
    #replace the original get_frame_notes_order coming with the django model for order_with_respect_to 
    def get_tags_order(self):  
        id = self.id      
        fts = Frame_Tags.objects.using(self.owner_name).filter(frame__id=self.id).order_by('id')
        fts_list = [ft for ft in fts]
        for ft in fts:
            ft.owner_name = self.owner_name
        if None in [ft._order for ft in fts]:
            return [ft.tag.id for ft in fns]
        else:
            
            fts_list.sort(key=lambda r: r._order)            
            return [ft.tag.id for ft in fts_list]
            
 
 
    def set_tags_order(self, order):        
        seq = 0
        for note_id in order:
            ft = Frame_Tags.objects.using(self.owner_name).get(frame__id=self.id, tag__id=tag_id)
            ft.owner_name = self.owner_name
            ft._order = seq            
            ft.save()
            seq = seq + 1
        self.save() #save the order to the social note
        
        
        
    def get_tags_in_order(self, sort=None):
        order = self.get_tags_order()
        ts = []
        for tag_id in order:
            t = Tag.objects.using(self.owner_name).get(id=tag_id)
            #add below so it can keep pointing to the right db
            t.owner_name = self.owner_name
            ts.append(t)
        #if sort and sort == 'vote':
        #    ns.sort(key=lambda r: r.vote, reverse=True)  
        return ts    
    
    
    #TODO:get children and grandchildren under direct siblings as well
    def get_siblings(self, tag_name):
        #print 'self.get_tags_in_order()', self.get_tags_in_order()
        tag_names = [tag.name for tag in self.get_tags_in_order()]        
        tag_names.remove(tag_name)
        return tag_names
     
     
   
        
     
    def add_tags(self, tag_names_str):
        tag_name_list = [tag_name.lstrip().rstrip() for tag_name in tag_names_str.split(',')]        
        current_num_of_tags = len(self.get_tags_order())
        self.db = self.owner_name
        for tag_name in tag_name_list:  
            #TODO: handling adding new tags         
            t = Tag.objects.using(self.owner_name).get(name=tag_name)              
            ft,created = Frame_Tags.objects.using(self.owner_name).get_or_create(frame=self, tag=t)
            if created:
                ft._order=current_num_of_tags
                current_num_of_tags += 1   
                 
      
#===============================================================================
# def get_parents_old(tf):
#        parents = [fts.frame for fts in Frame_Tags.objects.using(tf.owner_name).filter(tag__name=tf.name)]
#        return list(set(parents))
# 
# def get_parents(tf):
#    fts = Frame_Tags.objects.using(tf.owner_name).filter(tag__name=tf.name)
#    print 'fts', fts
#    parents = [ft.frame for ft in fts] 
#        
#    return list(set(parents))    
#===============================================================================
             
             
#solution copied from http://stackoverflow.com/questions/10287169/django-model-inheritance-delete-subclass-keep-superclass
#but it doesn't seem to work in my case due to the extra m2m field (there is no reference back from Frame_Tag although it is managed through Frame_Tags)
#Might add Fake_Frame_Tags too, but what the heck. It is too much work to do it this way. Raw sql is better.
#===============================================================================
# class Fake_Tag_Frame(models.Model):
#    tag_ptr = models.PositiveIntegerField(db_column="tag_ptr_id", primary_key=True)
#    tags = models.ManyToManyField(Tag, related_name='fake_in_frames', through="Frame_Tags")  
#    current = models.BooleanField(default=False) 
#    
#    class Meta:
#        app_label = Tag_Frame._meta.app_label
#        db_table = Tag_Frame._meta.db_table
#        managed = True
#        
#===============================================================================

       
class Frame_Tags(models.Model):
    frame = models.ForeignKey(Tag_Frame, related_name='tag_and_frame') #TODO:
    tag = models.ForeignKey(Tag)
    
    class Meta:
        order_with_respect_to = 'frame'
        unique_together = (("frame","tag"),) 
        
    def __unicode__(self):
        return self.frame.name + '-' + self.tag.name         
    