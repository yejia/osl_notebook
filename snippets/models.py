from django.db import models

from notebook.notes.models import Note, Tag, WorkingSet, Folder, Cache, get_storage_loc, fs



    
class Snippet(Note):
    attachment = models.FileField(upload_to=get_storage_loc,blank=True, storage=fs) #TODO:validate the file for security reason    
                
    def __unicode__(self):
        return self.desc
    
                    
class Snippet_Folder(Folder):
    pass


class Snippet_Cache(Cache):
    cache_id = models.AutoField(primary_key=True)