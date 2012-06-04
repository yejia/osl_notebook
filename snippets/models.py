from django.utils.translation import ugettext_lazy
from django.db import models



from notebook.notes.models import Note, Tag, WorkingSet, Folder, Cache, get_storage_loc, fs



    
class Snippet(Note):
    attachment = models.FileField(upload_to=get_storage_loc,blank=True, storage=fs, verbose_name=ugettext_lazy('Attachment'),) #TODO:validate the file for security reason    
                
    def __unicode__(self):
        return self.desc
    
    def get_note_type(self):
        return 'Snippet'  
    
 
    
                    
class Snippet_Folder(Folder):
    pass


class Snippet_Cache(Cache):
    cache_id = models.AutoField(primary_key=True)
    


#===============================================================================
# class Bag_Of_Snippet(Bag_Of_Note):
#    notes = models.ManyToManyField(Snippet)
#===============================================================================
    

    
class Linkage_Of_Snippet(models.Model):
    title = models.CharField(blank=True, max_length=2000) #TODO: need title?
    desc =  models.TextField(blank=True, max_length=2000)
    tags = models.ManyToManyField(Tag, blank=True)
    private = models.BooleanField(default=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
    deleted = models.BooleanField(default=False)
    vote =  models.IntegerField(default=0, blank=True)
    notes = models.ManyToManyField(Snippet) #TODO: so far doesn't allow linkage of linkange note

    
    class Meta:
#        unique_together = (("linkage_id","user"),)
        verbose_name = "linkage"    
    