from django.db import models

from notebook.notes.models import Note, Tag, WorkingSet, Folder, Cache



class Scrap(Note):
    url = models.CharField(max_length=2000)#models.URLField(max_length=300)


    def __unicode__(self):
        return self.desc

    def get_note_type(self):
        return 'Scrap'
    
    

#class Scrap_Backup(models.Model):
#    url = models.CharField(max_length=300)#models.URLField(max_length=300)  
#    desc =  models.TextField(max_length=200)  #TODO: doesn't seem to be limiting the size
#    title = models.CharField(blank=True,max_length=100)    
#    extra = models.TextField(blank=True,max_length=300)    
#    tags = models.ManyToManyField(Tag,blank=True)  
#    private = models.BooleanField(default=False)
#    init_date = models.DateTimeField('date created', auto_now_add=True)
#    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
#    deleted = models.BooleanField(default=False)
#    vote =  models.IntegerField(default=0) 


  

   
            
#TODO: change back to just Folder, it will be a different db table because of different app
class Scrap_Folder(Folder):
    pass


class Scrap_Cache(Cache):
    cache_id = models.AutoField(primary_key=True)
    


#===============================================================================
# class Bag_Of_Scrap(Bag_Of_Note):    
#    notes = models.ManyToManyField(Scrap) 
#===============================================================================
    

    
class Linkage_Of_Scrap(models.Model):
    title = models.CharField(blank=True, max_length=2000) #TODO: need title?
    desc =  models.TextField(blank=True, max_length=2000)
    tags = models.ManyToManyField(Tag, blank=True)
    private = models.BooleanField(default=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
    deleted = models.BooleanField(default=False)
    vote =  models.IntegerField(default=0, blank=True)
    notes = models.ManyToManyField(Scrap) #TODO: so far doesn't allow linkage of linkange note

    
    class Meta:
#        unique_together = (("linkage_id","user"),)
        verbose_name = "linkage"    
