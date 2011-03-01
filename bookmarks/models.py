from django.db import models
from notebook.notes.models import Note, Tag, WorkingSet, Folder, Cache




class Bookmark(Note):
    #We don't want to validate if the url is broken or not for the reason everyone knows :) :(
    url = models.CharField(max_length=300)#models.URLField(max_length=300)

    class Meta:
        unique_together = (('url'),)

    def __unicode__(self):
        return self.url
    
    
class Bookmark_Folder(Folder):
    pass    
        


class Bookmark_Cache(Cache):
    cache_id = models.AutoField(primary_key=True)
             
            

#class Bookmark_Backup(models.Model):
#    url = models.CharField(max_length=300)#models.URLField(max_length=300)
#    title = models.CharField(blank=True,max_length=100)
#    desc =  models.TextField(blank=True,max_length=200)
#    extra = models.TextField(blank=True,max_length=300)    
#    tags = models.ManyToManyField(Tag,blank=True)  
#    private = models.BooleanField(default=False)
#    init_date = models.DateTimeField('date created', auto_now_add=True)
#    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
#    deleted = models.BooleanField(default=False)
#    vote =  models.IntegerField(default=0) 
    



            
class Linkage_Of_Bookmark(models.Model):
    title = models.CharField(blank=True, max_length=30) #TODO: need title?
    desc =  models.TextField(blank=True, max_length=200)
    tags = models.ManyToManyField(Tag, blank=True)
    private = models.BooleanField(default=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
    deleted = models.BooleanField(default=False)
    vote =  models.IntegerField(default=0, blank=True)
    notes = models.ManyToManyField(Bookmark) #TODO: so far doesn't allow linkage of linkange note

    
    class Meta:
#        unique_together = (("linkage_id","user"),)
        verbose_name = "linkage"


    def __unicode__(self):
        return ','.join([str(note.id) for note in self.notes.all()])   
    
    def is_private(self):
        #check the private field of this Bookmark. if so, private. If not, 
        #check the tags to see if any tag is private        
        if self.private == True:
            return True
        else:                        
            for tag in self.tags.all():
                if tag.private == True:
                    return True   

    def get_sum_of_note_tags(self):
        ts = set([])
        for n in self.notes.all():
            for t in n.tags.all():
                ts.add(t.name)
        return list(ts)    

    def get_display_of_sum_of_note_tags(self):
        ts = self.get_sum_of_note_tags()
        return ','.join(ts)        
    
    def get_unique_extra_tags(self):
        ts = self.get_sum_of_note_tags()
        return list(set(self.get_tags()).difference(set(ts)))
        
    def get_display_of_unique_extra_tags(self):    
        return ','.join(self.get_unique_extra_tags())
    
    def get_tags(self):
        return [t.name for t in self.tags.all()]
        
    
    def display_tags(self):
        return ','.join(self.get_tags())   

    def get_desc_short(self):
        if len(self.desc)>97:
            return self.desc[0:97]+'...'
        else:
            return self.desc
           
    def get_desc_super_short(self):
        if len(self.desc)>30:
            return self.desc[0:30]+'...'
        else:
            return self.desc       
               
    def display_notes(self):
       
        return [(n.id, n.title, n.desc,n.display_tags()) for n in self.notes.all()]             
    
    def display_public_notes(self):
       
        return [(n.id, n.title, n.desc,n.display_tags()) for n in self.notes.all() if n.private==False] 
    
    #TODO: need save?
    def update_tags(self, tags_str):    
        new_tags_list = [name.lstrip().rstrip() for name in tags_str.split(',')] #assume distinct here. TODO:       

        self.tags.clear()
        for tname in new_tags_list:             
            t = Tag.objects.using(self.owner_name).get(name=tname) 
            self.tags.add(t) 

    def add_notes(self, noteids_str):
        note_id_list = [note_id.lstrip().rstrip() for note_id in noteids_str.split(',')]
        for note_id in note_id_list:          
            n = Bookmark.objects.using(self.owner_name).get(id=note_id)           
            self.notes.add(n)
    
     
    def remove_note(self, note_id):
        n = Bookmark.objects.using(self.owner_name).get(id=note_id)
        self.notes.remove(n)    



