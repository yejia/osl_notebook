from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from notebook.notes.constants import *


#TODO: refactor out. It is duplicated with the code from notes.models
#from time import gmtime, strftime  
def get_storage_loc(instance, filename):    
    #timepath= strftime('/%Y/%m/%d/')    
    return 'icons/'+instance.username+'/'+filename   

from django.core.files.storage import FileSystemStorage    
from notebook.env_setting import DB_ROOT
fs = FileSystemStorage(location=DB_ROOT)



class Member(User):
    ROLE_CHOICES = (        
        ('l', 'learner'),
        ('t', 'teacher'),
        
    )  
    GENDER_CHOICES = (        
        ('f', 'female'),
        ('m', 'male'),        
    )
      
    nickname = models.CharField(max_length=50, blank=True)   
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, blank=True) 
    #TODO: change to avatar
    icon = models.ImageField(upload_to=get_storage_loc,blank=True, storage=fs)    #TODO:
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True) 
    #maynot be a good way to do like this. TODO:
    # Use UserManager to get the create_user method, etc.
    objects = UserManager()
    #TODO:
    #timezone = models.CharField(max_length=50, default='Europe/London')
    
    #viewing mode. Later think of adding other viewing modes here so user can set these in their profile
    viewing_private = models.CharField(max_length=20, blank=True)
    
    
    
    def __unicode__(self): 
        return self.username   
    


    def get_friends(self):
        q1 = Q(friend1=self)
        q2 = Q(friend2=self)
        friend_rels = Friend_Rel.objects.filter(q1 | q2)#TODO: confirmed
        fl = [friend_rel.get_friend(self)  for friend_rel in friend_rels]
        fl.sort(key=lambda r: r.username) 
        return fl
   
   
    def get_friends_names(self):
        friends = self.get_friends()        
        return [friend.username for friend in friends]
       
       
   
    def get_groups(self):
        return Group.objects.filter(members=self).order_by('name')
   

class Social_Tag(models.Model):    
    name = models.CharField(max_length=150)
    private = models.BooleanField(default=False)
    
    class Meta:
        unique_together = (("name"),)
    
    def __unicode__(self):
        return self.name


    def get_social_snippet(self):
        return self.social_social_snippet_related.all().count()


#TODO: subclass Note and in dbrouter add allrelation for the two tables
class Social_Note(models.Model):
    owner = models.ForeignKey(Member)
    owner_note_id = models.IntegerField()#reference to the id of the note in the user's db
    title = models.CharField(blank=True, max_length=2000, help_text="The size of the title is limited to 50 characaters.") #maybe 20 is enough
    #event = models.CharField(blank=True,max_length=300)
    desc =  models.TextField(max_length=2000, help_text="The size of the desc is limited to 200 characaters.")
    tags = models.ManyToManyField(Social_Tag, blank=True) #, related_name="%(app_label)s_%(class)s_related" this only works for abstract base class
    #not actually used, just have it here so filters from notes.view can still be used since that note/bookmark/scrap has this field
    private = models.BooleanField(default=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
    #not actually used, just have it here so filters from notes.view can still be used since that note/bookmark/scrap has this field
    deleted = models.BooleanField(default=False)
    vote =  models.IntegerField(default=0)    
    #attachment = models.FileField(upload_to=get_storage_loc,blank=True, storage=fs)
    
    
    
    def __unicode__(self):
        return self.desc + u' by ' + self.owner.username
    

    def get_note_type(self):
        try:
            self.social_snippet
            return 'Snippet'
        except ObjectDoesNotExist:
            try:
                self.social_bookmark
                return 'Bookmark'    
            except ObjectDoesNotExist:
                try:
                    self.social_scrap
                    return 'Scrap'
                except ObjectDoesNotExist:
                    try:
                        self.social_frame
                        return 'Frame'
                    except ObjectDoesNotExist:   
                        log.info('No note type found!')
                        return 'Note' #TODO:
                
    def get_note_bookname(self):        
        return model_book_dict.get(self.get_note_type())
   
   
    def display_tags(self):
        return ','.join([t.name for t in self.tags.filter(private=False).order_by('name')])
    
    def display_all_tags(self):
        return ','.join([t.name for t in self.tags.all().order_by('name')])  
    
    def get_tags(self):
        return [t.name for t in self.tags.filter(private=False).order_by('name')] 
    
    def get_all_tags(self):
        return [t.name for t in self.tags.all().order_by('name')]   
    
    
    #TODO:so far not used yet in the view
    def get_tags_for_group(self, group):
        group_tag_name = group.get_group_tag_name()
        q1 = Q(private=False)
        q2 = Q(name=group_tag_name)
        return [t.name for t in self.tags.filter(q1 | q2).order_by('name').order_by('name')] 
        
        
               

    def get_useful_votes(self):
        votes = Social_Note_Vote.objects.filter(note=self, useful=True)        
        useful_votes = votes.count()
        #print 'useful_votes', useful_votes
        return useful_votes
      
        
    def get_unuseful_votes(self):
        votes = Social_Note_Vote.objects.filter(note=self, useful=False)
        unuseful_votes  = votes.count()
        return unuseful_votes

    def get_total_votes(self):
        votes = Social_Note_Vote.objects.filter(note=self)
        return votes.count()
    
    #TODO: algorithm
    #total*(useful - unuseful)    
    def get_usefulness(self):
        if self.get_useful_votes() or self.get_unuseful_votes():
            return self.get_total_votes()*(self.get_useful_votes() - self.get_unuseful_votes())
        else:
            return 0        


    def get_comments(self):          
        comments = Social_Note_Comment.objects.filter(note=self) 
        return comments 
    


class Social_Snippet(Social_Note):
    pass


class Social_Bookmark(Social_Note):
    url = models.CharField(max_length=2000)
    
    
    def __unicode__(self):
        return self.url + u' by ' + self.owner.username
    
    

class Social_Scrap(Social_Note):
    url = models.CharField(max_length=2000)
    
    
    def __unicode__(self):
        return self.url + u' by ' + self.owner.username



class Social_Frame(Social_Note):
    attachment = models.FileField(upload_to=get_storage_loc, blank=True, storage=fs)   
    notes = models.ManyToManyField(Social_Note, related_name='in_frames')
    
    def __unicode__(self):
        return ','.join([str(note.id) for note in self.notes.all()])   




class Social_Note_Comment(models.Model):
    note =  models.ForeignKey(Social_Note)
    commenter = models.ForeignKey(Member)
    desc = models.TextField(max_length=2000)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    
    def __unicode__(self):
        #TODO:use ugettext for translation
        return self.commenter.username+" on "+self.note.owner.username+"'s note: "+self.desc 



class Social_Note_Vote(models.Model):      
    note = models.ForeignKey(Social_Note)
    voter =  models.ForeignKey(Member)
    useful = models.BooleanField()#default??
    init_date = models.DateTimeField('date created', auto_now_add=True)

    class Meta:
        unique_together = (("note","voter"),)  
    
    def __unicode__(self): 
        return self.note.__unicode__()+" voted by "+self.voter.__unicode__()



class Group(models.Model):
    name = models.CharField(blank=False,max_length=50)
    desc = models.TextField(blank=True,max_length=500)
    tags = models.ManyToManyField(Social_Tag)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    private = models.BooleanField(blank=True)     
    members = models.ManyToManyField(Member, related_name='members')
    creator = models.ForeignKey(Member)#creater and admins have to be in members
    admins = models.ManyToManyField(Member, related_name='admins') #TODO: only one admin?
    
    
    class Meta:
        unique_together = (("name"),)
    
    
    def __unicode__(self):
        return self.name
  
  
    #TODO: check amin right??
    def add_tags(self, username, tags_to_add):   
        pass
            
    
    #tags_to_add is a list of tag names
    def remove_tags(self, tags_to_remove):              
        pass
            
       
    def get_group_tag_name(self):
        return "sharinggroup:"+self.name        
        
     
    def get_tag_names(self):
        return [tag.name for tag in self.tags.all()]     

           
            
#Activity Stream such as adding friend, posting...
#class Activity(models.Model): 
#    pass


#one relation has one entry in this table (although two entries make it easy for query).  TODO: enforce no redundance?
#TODO: confirm          
class Friend_Rel(models.Model): 
    confirmed = models.BooleanField(default=False) 
    friend1 = models.ForeignKey(Member, related_name='friend1')
    friend2 = models.ForeignKey(Member, related_name='friend2')
    init_date = models.DateTimeField('date created', auto_now_add=True)

    def __unicode__(self): 
        return self.friend1.__unicode__()  + u" and " + self.friend2.__unicode__()
    
    def get_friend(self, member):
        if self.friend1 == member:
            return self.friend2
        if self.friend2 == member:
            return self.friend1
        else:
            return None
        
  
class Fan(models.Model):     
    idol = models.ForeignKey(Member, related_name='idol')
    fan = models.ForeignKey(Member, related_name='fan')
    #tags =
    init_date = models.DateTimeField('date created', auto_now_add=True)
    
    def __unicode__(self): 
        return self.fan.__unicode__()  + u" is a fan of " + self.idol.__unicode__()


    def get_feed_display(self):
        return u'<a href="/user/'+unicode(self.fan.id)+'/">'+ self.fan.__unicode__() + u'</a>' +\
               u'followed' + u'<a href="/user/' + unicode(self.idol.id) + u'/">' + self.idol.__unicode__()+ u'</a>'    
