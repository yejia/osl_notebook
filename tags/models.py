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
    #whether this tag belong to a group that this member is in    
    #group_tag = models.BooleanField(default=False) 



# class Group_Tag(models.Model):
#     tag = models.ForeignKey(Tag)
    
    
    
    
    
    #tag_id = models.IntegerField()
    #user = models.ForeignKey(User)
#    if not standalone:
#        objects = MultiUserManager(owner_name)

    class Meta:
        unique_together = (("name"),)           
        ordering = ['name']

    def __unicode__(self):
        return self.name
    
    def name_as_list(self):        
        return self.name.split(':')

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

#cannot use below since notes.models import this module. Change this (putting them together)? TODO:;
#===============================================================================
#    def get_notes_count(self):  
#        try:
#            return Note.objects.using(self.owner_name).filter(tags=tag).count()
#        except AttributeError:
#            return 0 
#===============================================================================



class Tag_Frame(Tag):
    """class Frame is for notes. And Tag_Frame is frame used to put tags in a frame. Itself is a tag too."""
    tags = models.ManyToManyField(Tag, related_name='in_frames', through="Frame_Tags")     
    #TODO: at the most only one can have this to be true per user
    current = models.BooleanField(default=False)     


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
    


    def get_public_tags_in_order(self, sort=None):
        order = self.get_tags_order()
        ts = []
        for tag_id in order:
            t = Tag.objects.using(self.owner_name).get(id=tag_id)
            if not t.private:
                #add below so it can keep pointing to the right db
                t.owner_name = self.owner_name
                ts.append(t)
            else:
                print 'tag is private'    
        #if sort and sort == 'vote':
        #    ns.sort(key=lambda r: r.vote, reverse=True)  
        #print 'ts', ts
        return ts
    


    #TODO:get children and grandchildren under direct siblings as well
    def get_siblings(self, tag_name):
        #print 'self.get_tags_in_order()', self.get_tags_in_order()
        tag_names = [tag.name for tag in self.get_tags_in_order()]        
        tag_names.remove(tag_name)
        return tag_names
     
     
    
    def get_offsprings(self):
        offsprings = [t.name for t in self.tags.all()]#it is managed, can it use .tags reference directly? TODO:
        for child in self.tags.all():
            child.owner_name = self.owner_name
            #no need for the if check below now, since the UI guarantee that only tag frames are added as children
            if child.get_tag_type() == 'Nonleaf': 
                child.tag_frame.owner_name = self.owner_name 
                offsprings.extend(child.tag_frame.get_offsprings())
        #print 'offsprings',offsprings
        offsprings.sort() 
        return  list(set(offsprings))        
   
    
    
    def get_public_offsprings(self):
        #don't count private tags' children, even if they are public
        offsprings = [t.name for t in self.tags.all() if not t.private]#it is managed, can it use .tags reference directly? TODO:
        for child in self.tags.all():
            child.owner_name = self.owner_name
            #no need for the if check below now, since the UI guarantee that only tag frames are added as children
            if child.get_tag_type() == 'Nonleaf': 
                child.tag_frame.owner_name = self.owner_name 
                offsprings.extend(child.tag_frame.get_public_offsprings())
        #print 'offsprings',offsprings
        offsprings.sort() 
        return  list(set(offsprings)) 
        
     
    def add_tags(self, tag_names_str):
        if tag_names_str:
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
    


