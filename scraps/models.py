from django.db import models

from notebook.notes.models import Note, Tag, WorkingSet, Folder, Cache



class Scrap(Note):
    url = models.CharField(max_length=2000)#models.URLField(max_length=300)


    def __unicode__(self):
        return self.desc


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
