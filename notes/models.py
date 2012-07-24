# -*- coding: utf-8 -*-

from django.db import models

from django.contrib.auth.models import User

from django.forms import ModelForm
from django.db.models.query import QuerySet
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from django.utils.translation import ugettext as _

from notebook.social.models import Social_Note, Social_Tag, Social_Snippet, Social_Bookmark, Social_Scrap, Social_Frame, Social_Frame_Notes
from notebook.notes.constants import *
from notebook.tags.models import Tag, Tag_Frame


standalone = False

import logging
import notebook


#TODO: put logging into a common modules so both models and views can import from it
def getlogger(name):
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler(notebook.settings.LOG_FILE)    
    formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s%(name)s,%(pathname)s,line%(lineno)d,process%(process)d,thread%(thread)d,"%(message)s"','%Y-%m-%d %a %H:%M:%S')    
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(notebook.settings.LOG_LEVEL)
    return logger

log = getlogger('notes.models')

#owner_name = ""

#TODO:move to util.py
def getT(username):
    return create_model("T_"+str(username), Tag, username)


def getL(username):
    return create_model("L_"+str(username), LinkageNote, username)

def getW(username):
    return create_model("W_"+str(username), WorkingSet, username)


def getNC(username):
    return create_model("NC_"+str(username), Note_Comment, username)


#TODO: make snippet, bookmark, scrap inherit note, so the common code can all be merged into note. This
# way note become the core engine. Might use abstrat base class since there might be many subclasses. (can it still do 
#  query on all the subclass tables if using abstract base class? seems like this is impossible)
#TODO: move code from view to model to build up the core engine
#TODO: also extends User, so a lot of user related method can be gathered there.
#user.getNote(bookname) should get the notebook needed, and the different db issue is handled there
#maybe also  user.getFriends(), user.getGroups() (might not be important)


#TODO: add a new model class to inherit User table, so maybe other things can be added. At least, user related methods can be 
# grouped there. Or maybe not a model class, but just a normal class with user related methods.


#class MultiUserManager(models.Manager):
#    use_for_related_fields = True
#    
#    def __init__(self, owner_name):
#        super(MultiUserManager, self).__init__()
#        self.owner_name = owner_name
#        self._db = owner_name 
        #self._meta = super._meta #TODO
    
#    def get_query_set(self):
#        #return super(MultiUserManager, self).get_query_set().filter(user__username__exact=self.owner_name)
#        qs = QuerySet(self.model)
#        #if self._db is not None:
#            #qs = qs.using(self._db)
#        qs = qs.using(self.owner_name)    
#        return qs
    
#    def select_related(self, *args, **kwargs):
#        return self.get_query_set().select_related(*args, **kwargs).filter(user__username__exact=self.owner_name)



#===============================================================================
# 
# class  Framable(models.Model):
#    children = models.ManyToManyField(Framable, through="Frame_Children")  
#    
#    
#    def get_children_order(self):  
#        id = self.id      
#        fcs = Frame_Children.objects.using(self.owner_name).filter(frame__id=self.id).order_by('id')
#        fcs_list = [fc for fc in fcs]
#        for fc in fcs:
#            fc.owner_name = self.owner_name
#        if None in [fc._order for fc in fcs]:
#            return [fc.child.id for fc in fcs]
#        else:
#            
#            fcs_list.sort(key=lambda r: r._order)            
#            return [fc.child.id for fc in fcs_list]
#            
# 
# 
#    def set_children_order(self, order):        
#        seq = 0
#        for child_id in order:
#            fc = Frame_Children.objects.using(self.owner_name).get(frame__id=self.id, child__id=child_id)
#            fc.owner_name = self.owner_name
#            fc._order = seq            
#            fc.save()
#            seq = seq + 1
#        self.save() #save the order to the social note
#===============================================================================




             
#===============================================================================
# 
# 
# class Frame_Children(models.Model):
#    frame = models.ForeignKey(Framable) #TODO:
#    child = models.ForeignKey(Framable)
#    
#    class Meta:
#        order_with_respect_to = 'frame'
#        
#===============================================================================




class WorkingSet(models.Model):
    name = models.CharField(max_length=50)
    desc =  models.TextField(blank=True, max_length=200)
    tags = models.ManyToManyField(Tag)
    private = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    #TODO: at the most only one workingset can have this to be true per user
    current = models.BooleanField(default=False) #TODO: is it enough to keep this info in the session? Or rename as active? Or just use delete for this purpose

    class Meta:
        unique_together = (("name"),)
        ordering = ['name']

    def __unicode__(self):
        return self.name 


    def display_tags(self):
        return ','.join([t.name for t in self.tags.all().order_by('name')])
    
     
    def get_tags(self):
        return [t.id for t in self.tags.all().order_by('name')]  
    
    
    def add_tags(self, tags_str):
        new_tags_list = [name.lstrip().rstrip() for name in tags_str.split(',')]        
        count_tag_created = 0
        for tname in new_tags_list:
            t, created = Tag.objects.using(self.owner_name).get_or_create(name=tname) 
            self.tags.add(t)
            self.save()#TODO: performance?
            
            if created:
                count_tag_created += 1 
                
        return  count_tag_created   
    
    

from django.utils.translation import ugettext_lazy

#TODO: so far, no title
#TODO: public or private field
#TODO: add importance (just 2 level or 3 level, optional)? Or maybe don't use importance level, but associate a 
# list of events with the experience. From the number of events, you can tell the importance.
class Note(models.Model):
    #For bookmarks or scraps from some sites, the title can be quite long. Force users to truncate it?
    title = models.CharField(verbose_name=ugettext_lazy('Title'), blank=True,max_length=2000, help_text=_("The size of the title is limited to 2000 characaters.")) #maybe 20 is enough
    #event = models.CharField(blank=True,max_length=300)
    #enforce in views to limit the length for snippet or enforce in save(), or move this field down to snippet
    desc =  models.TextField(verbose_name=ugettext_lazy('Description'), max_length=2000, blank=True,  help_text=_("The size of the desc is limited to 2000 characaters."))
    tags = models.ManyToManyField(Tag, verbose_name=ugettext_lazy('Tags'), blank=True,  help_text=_("Default tag is 'random thought'."))	#TODO: NOT NULL?? #TODO: set default as random thoughts?
    private = models.BooleanField(verbose_name=ugettext_lazy('Private'), default=False)
    #the current django implementation, setting auto_now or auto_now_add to True will cause the field to have editable=False and blank=True set.
    init_date = models.DateTimeField(verbose_name=ugettext_lazy('date created'), auto_now_add=True, editable=True)
    last_modi_date = models.DateTimeField(verbose_name=ugettext_lazy('date last modified'), auto_now=True)
    deleted = models.BooleanField(default=False)
    #TODO: how to display the Chinese of this one with ugettext_lazy??
    vote =  models.IntegerField(verbose_name=ugettext_lazy('self ranking'), default=0)  #TODO: change to rank  
    
    
  
    #user = models.ForeignKey(User)
    
    class Meta:
        ordering = ['-init_date','vote','desc','title']
#        unique_together = (("note_id","user"),)
#        abstract = True
         


    def __unicode__(self):
        return self.desc


    def set_translation(self, original_lang, lang, title, desc):
        trans, created =  Note_Translation.objects.using(self.owner_name).get_or_create(note=self)
        trans.original_lang = original_lang
        trans.lang = lang
        trans.title = title
        trans.desc = desc
        trans.owner_name = self.owner_name
        trans.save()
        
    
    def get_desc_en(self):
        if not self.get_lang():
            return self.desc
        elif self.get_lang() == 'E':
            return self.desc
        else:
           trans =  Note_Translation.objects.using(self.owner_name).get(note=self)
           return trans.desc 
       
       
    #get the Chinese version   
    def get_desc_cn(self):
        if not self.get_lang():
            return self.desc
        elif self.get_lang() == 'C':
            return self.desc
        else:
           trans =  Note_Translation.objects.using(self.owner_name).get(note=self)
           return trans.desc 
    
    
    def get_title_en(self):        
        if not self.get_lang():
            return self.title
        elif self.get_lang() == 'E':
            return self.title
        else:
           trans =  Note_Translation.objects.using(self.owner_name).get(note=self)
           return trans.title 
       
       
    #get the Chinese version   
    def get_title_cn(self):
        if not self.get_lang():            
            return self.title
        elif self.get_lang() == 'C':            
            return self.title
        else:
           trans =  Note_Translation.objects.using(self.owner_name).get(note=self)            
           return trans.title 
          
    
    def get_lang(self):
        if Note_Translation.objects.using(self.owner_name).filter(note=self).exists():
            trans =  Note_Translation.objects.using(self.owner_name).get(note=self)            
            return trans.original_lang
        else:
            return ''
    
    
    #TODO:better to move this method and the next one outside of this class?
    def get_note_type(self):
        try:
            self.snippet
            return 'Snippet'
        except ObjectDoesNotExist:
            try:
                self.bookmark
                return 'Bookmark'    
            except ObjectDoesNotExist:
                try:
                    self.scrap
                    return 'Scrap'
                except ObjectDoesNotExist:
                    try:
                        self.frame
                        return 'Frame'
                    except ObjectDoesNotExist:   
                        log.info('No note type found!')
                        return 'Note' #TODO:
                
      
        
    def get_note_bookname(self):           
        return model_book_dict.get(self.get_note_type())
      
    
    
    def has_attachment(self):
        if hasattr(self, 'attachment') and self.attachment:
            return True
        return False
    
       
#TODO: rewrite parts in views that get public notes. It should just use a filter or something with the help of this method
#or simply add to tempalte (this way is used and it seems to work well, but then in the note list display, the counting of notes
#won't be correct. It is better to filter in views code)
    def is_private(self):
        #check the private field of this Note. if so, private. If not, 
        #check the tags to see if any tag is private        
        if self.private == True:
            return True
        else:                        
            for tag in self.tags.all():
                if tag.private == True:
                    return True


    def display_tags(self):
        #return ','.join([t.name for t in self.tags.all()])
        return ','.join(self.get_tags())
    
     
    def get_tags_ids(self):
        return [t.id for t in self.tags.all()]    
    
    def get_tags(self):
        return [t.name for t in self.tags.all()]     
    
    def display_linkages(self):
        return ','.join([str(l.id) for l in self.linkagenote_set.all()])     
    
    def display_frames(self):
        return ','.join([str(l.id) for l in self.in_frames.all()])    
    
    def get_frame_ids_titles(self):        
        return [[l.id, l.title] for l in self.in_frames.all()] 
    
    def is_in_frame(self):
        if self.get_frame_ids_titles():
            return True
        else:
            return False

    def get_desc_short(self):
        if len(self.desc)>97:
            return self.desc[0:97]+'...'
        else:
            return self.desc       
    
    def get_desc_super_short(self):
        if len(self.desc)>50:
            return self.desc#[0:50]+'...'
        else:
            return self.desc
    
    
    
    def get_relevance(self, tag_path):
        tag_list = tag_path.split('-')
        tag_name = tag_list[-1]
        relevance = 0
        #check if this note really has tag_name as its tag.
        if not tag_name in self.get_tags():
            #print 'tag not in the note tags, return 0'
            return 0 #not related at all. May raise an error here TODO:
        
        relevant_tags = [tag_name]
        
        #merge code of direct parent with grand parents?TODO:
        direct_parent = tag_list[-2]
        relevant_tags.append(direct_parent)
        if direct_parent in self.get_tags():
            relevance += 10 * tag_list.index(direct_parent)
            
        
        ptf = Tag_Frame.objects.using(self.owner_name).get(name=direct_parent)
        ptf.owner_name = self.owner_name
        #print 'ptf.get_siblings(tag_name)', ptf.get_siblings(tag_name)
        for sib in ptf.get_siblings(tag_name):
            relevant_tags.append(sib)
            if sib in self.get_tags():
                relevance += 5
        
        #TODO: checking for cousins.
        #check for uncles
        grandparent_list = tag_list[:-2]
        grandparent_list.reverse()
        for i, grandparent in enumerate(grandparent_list):
            relevant_tags.append(grandparent)
            if grandparent in self.get_tags():
                relevance += 10 * tag_list.index(grandparent)
            child_tag_name = tag_list[-i-2]
            gtf = Tag_Frame.objects.using(self.owner_name).get(name=grandparent)
            #print 'child_tag_name:', child_tag_name, 'gtf', gtf
            gtf.owner_name = self.owner_name
            for sib in gtf.get_siblings(child_tag_name):
                relevant_tags.append(sib)
                if sib in self.get_tags():
                    relevance += len(tag_list) - i #check if always > 0
            
        log.info('relevant_tags'+str(relevant_tags))
        for t in self.get_tags():
            if not t in relevant_tags:
                relevance -= 1
        
        return relevance    
    
    
#Not used.    
#    def add_tags(self, tags_str):
#        new_tags_list = [name.lstrip().rstrip() for name in tags_str.split(',')]        
#        count_tag_created = 0
#        for tname in new_tags_list:
#            t, created = Tag.objects.using(self.owner_name).get_or_create(name=tname) 
#            self.tags.add(t)
#            self.save()#TODO: performance?
#            
#            if created:
#                count_tag_created += 1 
#                w = WorkingSet.objects.using(self.owner_name).get(name='snippetbook')
#                w.tags.add(t)
#                w.save()                
#        return  count_tag_created   
     
    
    #TODO: make bookname a class field? And it get set when calling getNote(). So the instance method doesn't need to pass bookname again.
    #TODO: this method so far is not used by bookmarks.views and scraps.views, so either merge them or get rid of bookname here. 
    #tags_to_add is a list of tag names 
    #TODO: get rid of bookname, and use hasattr to tell what the instance is. Just like how update_tags does
    def add_tags(self, tags_to_add, bookname):  
        #TODO: not right. Should tell bookname base on the instance. After using hasattr, no need to consider the case of 'notebook'
        if bookname == 'notebook':
            bookname = 'snippetbook'   
        num_of_tags_created = 0
        W = getW(self.owner_name)             
        w = W.objects.get(name=bookname)     
        for tag_name in tags_to_add:    
            t, created = Tag.objects.using(self.owner_name).get_or_create(name=tag_name) 
            #in any case, just add the tag to the snippet working set. If it is already
            # in it, just no effect.             
            try:             
                w.tags.add(t)
                w.save()                
            except Exception:
                log.error("Error in add_tags with w "+w.name+' and tag '+t.name)            
            self.tags.add(t)  
            #TODO: there seems to be no need t save this instance, as self.tags.add(t) already saved data to the m2m table  
            # but to update the social note as well, I think below is still needed        
            self.save() 
            if created:
                num_of_tags_created += 1
        return num_of_tags_created       
            
    
    #tags_to_add is a list of tag names
    def remove_tags(self, tags_to_remove):              
        for tag_name in tags_to_remove:    
            t = Tag.objects.using(self.owner_name).get(name=tag_name) 
            self.tags.remove(t)
            self.save()                           
    
    
    #TODO: merge the ws part with add_tags or maybe move that into save() (seems better since save will be called anyway to update social note)
    def update_tags(self, tags_str):
        new_tags_list = [name.lstrip().rstrip() for name in tags_str.split(',')]
        #TODO:for now, just remove all the old tags and then add all the new ones
        #might want to improve the algorithm later
        self.tags.clear()
        count_tag_created = 0
        
        W = getW(self.owner_name)
        
        if hasattr(self, 'snippet'):
            w = W.objects.get(name='snippetbook')
            #w = WorkingSet.objects.using(self.owner_name).get(name='snippetbook')
        if hasattr(self, 'bookmark'):
            w = W.objects.get(name='bookmarkbook')
            #w = WorkingSet.objects.using(self.owner_name).get(name='bookmarkbook')
        if hasattr(self, 'scrap'):
            w = W.objects.get(name='scrapbook')
            #w = WorkingSet.objects.using(self.owner_name).get(name='scrapbook')
        
        for tname in new_tags_list:            
            t, created = Tag.objects.using(self.owner_name).get_or_create(name=tname) 
            self.tags.add(t)
            
            self.save()#TODO: performance?            
            if created:
                count_tag_created += 1  
            w.tags.add(t)           
            w.save()            
            
        return  count_tag_created              


    def get_comments(self):        
        comments = Note_Comment.objects.using(self.owner_name).filter(note=self)         
        return comments 
        #return ''.join([comment.desc for comment in comments])
    
    def display_comments(self):
        comments = self.get_comments()
        return [{'id':comment.id,'desc':comment.desc} for comment in comments]
    

    def get_social_note(self): 
        try:       
            sn = Social_Note.objects.get(owner__username=self.owner_name, owner_note_id=self.id)
            return sn
        except ObjectDoesNotExist:    
            return ''
        


    #is attachment img? TODO: better ways of telling if the attach is an img or not
    def is_img(self):
        file_type = None
        if self.get_note_type() == 'Snippet':
            if self.snippet.attachment.name:
                splits = self.snippet.attachment.name.split('.')
                file_type = splits[len(splits)-1]
        elif self.get_note_type() == 'Frame':
            if self.frame.attachment.name:
                splits = self.frame.attachment.name.split('.')
                file_type = splits[len(splits)-1]
        if file_type in ['jpg','JPG','jpeg','JPEG','png','PNG', 'gif']:
            return True
        else: 
            return False    



    #TODO:so far, notes of private tag cannot be viewed by others in the person's notebook. But should it be viewed by others in a group?
    #  maybe the logic should be notes of private tags are not really private. It is just that the tag is private and that private tag will not
    #  not show in tags list. But if that note has other tags, you can still find that note. 
    #The problem with notes of private tags not showing up in social notes is that if a group member sets his own tag such as *** as a private
    #tag, then his notes in *** won't show in the group 
    #TODO:refactor out to several sync methods
   #TODO:when a note become public again, should the frame that it is in get a save too so that the social frame can be updated?
    def save(self, *args, **kwargs):             
        #do_something()
        super(Note, self).save(*args, **kwargs) # Call the "real" save() method.        
        owner = User.objects.get(username=self.owner_name)
        
        #TODO:if note is set deleted=True, then it should be removed from frames it is in. How about the frame in the social notebook?
        #below doesn't work. Not sure why. TODO:
#===============================================================================
#        if self.deleted:#            
#            if self.in_frames.all():#TODO:need self.owner_name?#                
#                for f in self.in_frames.using(self.owner_name).all():
#                    print 'remove self from frame:', f.id
#                    f.notes.remove(self)
#                    f.save()
#===============================================================================
        
        
        #TODO: consider moving this into various subclasses
        #TODO: shouldn't this check if the note is private or delete?
        if hasattr(self, 'snippet'):
            sn, created = Social_Snippet.objects.get_or_create(owner=owner.member, owner_note_id=self.id) 
        if hasattr(self, 'bookmark'):
            sn, created = Social_Bookmark.objects.get_or_create(owner=owner.member, owner_note_id=self.id) 
        if hasattr(self, 'scrap'):
            sn, created = Social_Scrap.objects.get_or_create(owner=owner.member, owner_note_id=self.id)  
        if hasattr(self, 'frame'):
            sn, created = Social_Frame.objects.get_or_create(owner=owner.member, owner_note_id=self.id)            
        
        
        #if the note has sharinggroup: prefixed tag, then it still need to be in the social space
        #if not created and (self.private or self.deleted) and not self.tags.filter(name__startswith="sharinggroup:").exists():   
        if (self.private or self.deleted) and not self.tags.filter(name__startswith="sharinggroup:").exists():  
            #if the note is already in social note, and the note in the original db is changed to priviate or delete
            #   then needs to delete it from the social note
            #TODO: still, deleting the child won't delete the parent. Will this be an issue? So at least disable mixed.
            try:
                sn = Social_Note.objects.get(owner=owner.member, owner_note_id=self.id)
                sn.delete()
            except ObjectDoesNotExist:    
                pass
           
        else:               
            #whether the note is first created or just an update, below applies to both situations
            sts = [] 
            for t in self.tags.all():  
                #private tags should not be pushed to the social space, unless it contains "sharinggroup:"  
                if not t.private or t.name.startswith("sharinggroup:"):                
                    st, created = Social_Tag.objects.get_or_create(name=t.name)
                    sts.append(st)
            
            
            
            if hasattr(self, 'bookmark') or hasattr(self, 'scrap'):
                log.debug('having attribute bookmark or scrap')
                if hasattr(self, 'bookmark'):
                    sn.url = self.bookmark.url
                if hasattr(self, 'scrap'):
                    sn.url = self.scrap.url
            
            
            if hasattr(self, 'snippet') or hasattr(self, 'frame'):
                log.debug('having attribute snippet or frame')
                if hasattr(self, 'snippet'):
                    sn.attachment = self.snippet.attachment                    
                if hasattr(self, 'frame'):
                    sn.attachment = self.frame.attachment
            
                        
            #sns_included = []   
            #TODO:test below 
            if hasattr(self, 'frame'):
                self.frame.owner_name = self.owner_name
                self.vote = self.frame.get_vote()
                #for n_included in self.frame.notes.using(self.owner_name).all():
                
                order = self.frame.get_notes_order()
                #clear the included notes for the social note first
                sn.notes.clear()
                for note_id in order:
                    #TODO:how about deleted?
                    n_included = Note.objects.using(self.owner_name).get(id=note_id)
                    if not n_included.is_private():
                        sn_included = Social_Note.objects.get(owner=owner.member, owner_note_id=n_included.id)                        
                        #sns_included.append(sn_included)
                        sfn, created = Social_Frame_Notes.objects.get_or_create(social_frame=sn, social_note=sn_included)
                        sfn._order = order.index(note_id)
                        sfn.save()                                            
              
                #sn.notes = sns_included   
                
            sn.desc = self.desc
            sn.title = self.title
            #sn.event = self.event            
            sn.last_modi_date = self.last_modi_date
            sn.init_date = self.init_date
            sn.vote = self.vote
            sn.private = self.private
            #attachment
            sn.tags.clear()
            for st in sts:
                sn.tags.add(st)
            
            
            #save the translation
            if self.get_lang():
                trans =  Note_Translation.objects.using(self.owner_name).get(note=self)
                sn.set_translation(trans.original_lang, trans.lang, trans.title, trans.desc)
            
            
            #TODO: for group members that want every note posted to the group, email them the newly posted note. Might want to disable this 
            #due to privcy reason (for example, the user can make a note private to take it back after posting) 
            
            sn.save()        




from time import gmtime, strftime  
def get_storage_loc(instance, filename):    
    timepath= strftime('/%Y/%m/%d/')    
    return 'noteattachments/'+instance.owner_name+timepath+filename   #TODO: test added '/'+

from django.core.files.storage import FileSystemStorage    
from notebook.env_settings import DB_ROOT
fs = FileSystemStorage(location=DB_ROOT)



#class Note_Backup(models.Model):
#    title = models.CharField(blank=True,max_length=50, help_text="The size of the title is limited to 50 characaters.") #maybe 20 is enough
#    #event = models.CharField(blank=True,max_length=300)
#    desc =  models.TextField(max_length=200, help_text="The size of the desc is limited to 200 characaters.")
#    tags = models.ManyToManyField(Tag,blank=True,  help_text="Default tag is 'random thought'.")    #TODO: NOT NULL?? #TODO: set default as random thoughts?
#    private = models.BooleanField(default=False)
#    init_date = models.DateTimeField('date created', auto_now_add=True)
#    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
#    deleted = models.BooleanField(default=False)
#    vote =  models.IntegerField(default=0)  #TODO: change to rank  
#    attachment = models.FileField(upload_to=get_storage_loc,blank=True, storage=fs) 


class Note_Comment(models.Model):
    note =  models.ForeignKey(Note)   
    #commenter = models.ForeignKey(User) 
    desc = models.TextField(max_length=2000)
    init_date = models.DateTimeField('date created', auto_now_add=True)  
    
    def __unicode__(self):
        return self.desc  
        
    class Meta:
        ordering = ['-init_date','note','desc']
                

#For now, we don't make frame of Snippet/Bookmark/Scrap. There are only frames of Notes. 
#TODO: clean up code that duplicate with those in Note
class Frame(Note):       
    attachment = models.FileField(upload_to=get_storage_loc, blank=True, storage=fs, verbose_name=ugettext_lazy('Attachment'))    
    
    #TODO: notes reference to the id of Note instead of note_id. Unlike ForeignKey field, ManyToManyField
    #doesn't allow specifying a to_field argument. Think of whether to reference to note_id.
    notes = models.ManyToManyField(Note, related_name='in_frames', through="Frame_Notes") 
    
    
    class Meta:
#        unique_together = (("linkage_id","user"),)
        verbose_name = "frame"           
       

    def __unicode__(self):
        return ','.join([str(note.id) for note in self.notes.all()])     
    

#===============================================================================
#    def get_note_order(self):
#        return [n.id for n in self.notes.all()]
#    
#    def set_note_order(self, ordered_ids):
#        
#===============================================================================
        

    def get_vote(self):        
        v = 0  
        #TODO:using(self.owner_name)?
        for n in self.notes.using(self.owner_name).all(): 
            v = v + n.vote            
        return v

    def get_sum_of_note_tags(self):
        ts = set([])
        #TODO:using(self.owner_name)?
        for n in self.notes.using(self.owner_name).all():
            for t in n.tags.using(self.owner_name).all():
                ts.add(t.name)
        return list(ts)    

    
    def get_sum_of_note_tag_ids(self): 
        ts = set([])
        #TODO:using(self.owner_name)?
        for n in self.notes.using(self.owner_name).all():
            for t in n.tags.using(self.owner_name).all():
                ts.add(t.id)
        return list(ts) 


    def get_display_of_sum_of_note_tags(self):
        ts = self.get_sum_of_note_tags()
        return ','.join(ts)        
    
    #not useful anymore, since a frame's tags should just be the sum of its included notes' tags
    def get_unique_extra_tags(self):
        ts = self.get_sum_of_note_tags()
        return list(set(self.get_tags()).difference(set(ts)))
        
    def get_display_of_unique_extra_tags(self):    
        return ','.join(self.get_unique_extra_tags())
    
 
    def get_notes_in_order(self, sort=None):
        order = self.get_notes_order()
        ns = []
        for note_id in order:
            n = Note.objects.using(self.owner_name).get(id=note_id)
            #add below so it can keep pointing to the right db
            n.owner_name = self.owner_name
            ns.append(n)
        if sort and sort == 'vote':
            ns.sort(key=lambda r: r.vote, reverse=True)  
        return ns
    
    
 
    
    def get_public_notes_in_order(self):
        order = self.get_notes_order()
        ns = []
        for note_id in order:
            n = Note.objects.using(self.owner_name).get(id=note_id)
            n.owner_name = self.owner_name
            if n.private == False:
                ns.append(n)
        if sort and sort == 'vote':
            ns.sort(key=lambda r: r.vote, reverse=True)  
        return ns
     
               
#===============================================================================
#    def display_notes(self):        
#        return [[n.id, n.title, n.desc, n.vote, n.get_note_bookname, n.get_note_type] for n in self.get_notes_in_order()]    
#                
#    
#    def display_public_notes(self):         
#        return [[n.id, n.title, n.desc, n.vote, n.get_note_bookname, n.get_note_type] for n in self.get_public_notes_in_order()]   
#===============================================================================
            
    
    #TODO: need save?
    def update_tags(self, tags_str):    
        new_tags_list = [name.lstrip().rstrip() for name in tags_str.split(',')] #assume distinct here. TODO:       
        #TODO:for now, just remove all the old tags and then add all the new ones
        #might want to improve the algorithm later
        self.tags.clear()
        for tname in new_tags_list:             
            t = Tag.objects.using(self.owner_name).get(name=tname) 
            self.tags.add(t) 
        #return True

    #TODO: need save?
    def add_notes(self, noteids_str):
        note_id_list = [note_id.lstrip().rstrip() for note_id in noteids_str.split(',')]        
        current_num_of_notes = len(self.get_notes_order())
        self.db = self.owner_name
        for note_id in note_id_list:          
            n = Note.objects.using(self.owner_name).get(id=note_id)              
            fn,created = Frame_Notes.objects.using(self.owner_name).get_or_create(frame=self, note=n)
            if created:
                fn._order=current_num_of_notes
                current_num_of_notes += 1         
            #self.notes.add(n)
    
    #TODO:note_id or id?        
    def remove_note(self, note_id):
        n = Note.objects.using(self.owner_name).get(id=note_id)
        #self.notes.remove(n)   
        fn = Frame_Notes.objects.using(self.owner_name).get(frame=self, note=n) 
        #TODO: need to move the seq number over?
        fn.owner_name = self.owner_name
        fn.delete()
        #Need to update the social one
        self.save()


#===============================================================================
#   def get_owner_name(self):
#       if self.owner_name:
#           return  self.owner_name
#       else:
#           if 
#===============================================================================


    #replace the original get_frame_notes_order coming with the django model for order_with_respect_to 
    def get_notes_order(self):  
        id = self.id      
        fns = Frame_Notes.objects.using(self.owner_name).filter(frame__id=self.id).order_by('id')
        fns_list = [fn for fn in fns]
        for fn in fns_list:
            fn.owner_name = self.owner_name
        if None in [fn._order for fn in fns_list]:
            return [fn.note.id for fn in fns]
        else:
            
            fns_list.sort(key=lambda r: r._order)            
            return [fn.note.id for fn in fns_list]
            


    def set_notes_order(self, order):        
        seq = 0
        for note_id in order:
            fn = Frame_Notes.objects.using(self.owner_name).get(frame__id=self.id, note__id=note_id)
            fn.owner_name = self.owner_name
            fn._order = seq            
            fn.save()
            seq = seq + 1
        self.save() #save the order to the social note


    def has_attachment(self):
        if hasattr(self, 'attachment') and self.attachment:
            return True
        notes = self.get_notes_in_order()        
        for note in notes:            
            if note.get_note_type() == 'Snippet' and note.snippet.has_attachment():                 
                return True
            if note.get_note_type() == 'Frame':
                note.frame.owner_name = self.owner_name   
                if note.frame.has_attachment():              
                    return True
        return False



    def get_related_frames(self):        
        related = []    
        offsprings = self.get_offsprings()   
        for child in self.notes.all():        
            child.owner_name = self.owner_name
            uncles = child.get_frame_ids_titles()        
                  
            for uncle in uncles:        
                uncle.append('(note '+str(child.id)+')  '+child.title+':  '+child.desc)  
                if uncle[0] != self.id and uncle[0] not in self.get_offsprings() and uncle not in related:
                    related.append(uncle)        
            #for now, don't go up further TODO:
            if child.get_note_type() == 'Frame':            
                child.frame.owner_name = self.owner_name           
                related.extend(child.frame.get_related_frames())        
        
        
        return related    
    


    def get_offsprings(self):
        offsprings = [n.id for n in self.notes.all()]
        for child in self.notes.all():
            child.owner_name = self.owner_name
            if child.get_note_type() == 'Frame': 
                child.frame.owner_name = self.owner_name 
                offsprings.extend(child.frame.get_offsprings())
        print 'offsprings', offsprings
        return   offsprings       
            



class Frame_Notes(models.Model):
    frame = models.ForeignKey(Frame, related_name='note_and_frame') #TODO:
    note = models.ForeignKey(Note)
    
    class Meta:
        order_with_respect_to = 'frame'


#TODO:for now LinkageNote is kept, but only for viewing old linkages. Frame is used to "frame" notes together. 
#TODO:clean up web UI
#TODO: or merge this with Note field, and add field is_linkage, type_of_linkage.  If you do so, linkage can link linkage, that
#might make it too complicated. If there is a level of grouping above linkage, make it another thing in the future?
class LinkageNote(models.Model):
    LINKAGE_TYPE_CHOICES = (
        ('T', 'the same topic'),
        ('E', 'the same event'),
    )
    type_of_linkage = models.CharField(max_length=1, choices=LINKAGE_TYPE_CHOICES,blank=True)
    title = models.CharField(blank=True, max_length=2000) #TODO: need title?
    desc =  models.TextField(blank=True, max_length=2000)
    tags = models.ManyToManyField(Tag, blank=True)#TODO: get rid of
    private = models.BooleanField(default=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    last_modi_date = models.DateTimeField('date last modified', auto_now=True)
    deleted = models.BooleanField(default=False)
    vote =  models.IntegerField(default=0, blank=True)#TODO: get rid of
    attachment = models.FileField(upload_to=get_storage_loc, blank=True, storage=fs)    
    
    #TODO: notes reference to the id of Note instead of note_id. Unlike ForeignKey field, ManyToManyField
    #doesn't allow specifying a to_field argument. Think of whether to reference to note_id.
    notes = models.ManyToManyField(Note) #TODO: so far doesn't allow linkage of linkange note
    #linkage_id = models.IntegerField()
#    user = models.ForeignKey(User)
    
    class Meta:
#        unique_together = (("linkage_id","user"),)
        verbose_name = "linkage"


    def __unicode__(self):
        return ','.join([str(note.id) for note in self.notes.all()])	 
    
    def is_private(self):
        #check the private field of this Note. if so, private. If not, 
        #check the tags to see if any tag is private        
        if self.private == True:
            return True
        else:                        
            for tag in self.tags.all():
                if tag.private == True:
                    return True


    def get_vote(self):        
        v = 0  
        for n in self.notes.all(): 
            v = v + n.vote
        return v

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
        #return [(n.note_id, n.title, n.desc,n.display_tags()) for n in self.notes.all()]
        return [[n.id, n.title, n.desc] for n in self.notes.all()]  	       
    
    def display_public_notes(self):
        q = ~Q(tags__private=True)
        return [(n.id, n.title, n.desc,n.display_tags()) for n in self.notes.filter(q) if n.private==False] 
    
    #TODO: need save?
    def update_tags(self, tags_str):	
        new_tags_list = [name.lstrip().rstrip() for name in tags_str.split(',')] #assume distinct here. TODO:       
        #TODO:for now, just remove all the old tags and then add all the new ones
        #might want to improve the algorithm later
        self.tags.clear()
        for tname in new_tags_list:	     	
            t = Tag.objects.using(self.owner_name).get(name=tname) 
            self.tags.add(t) 
        #return True

    #TODO: need save?
    def add_notes(self, noteids_str):
        note_id_list = [note_id.lstrip().rstrip() for note_id in noteids_str.split(',')]
        for note_id in note_id_list:          
            n = Note.objects.using(self.owner_name).get(id=note_id)           
            self.notes.add(n)
    
    #TODO:note_id or id?        
    def remove_note(self, note_id):
#        if self.__class__.owner_name:
#            n = Note.objects.using(self.__class__.owner_name).get(id=note_id)
#        else:
#            n = Note.objects.get(id=note_id)
        n = Note.objects.using(self.owner_name).get(id=note_id)
        self.notes.remove(n)	





#TODO: should folder be universal for snippets/bookmarks/scraps??

#search can be saved as dynamic folder
class Folder(models.Model):
    name = models.CharField(blank=False,max_length=50) #False should be the default value, right? TODO:
    value = models.CharField(blank=False,max_length=200)
    desc = models.CharField(blank=True,max_length=500)
    deleted = models.BooleanField(default=False)
    init_date = models.DateTimeField('date created', auto_now_add=True)
    private = models.BooleanField(default=False)   #TODO:need it?
    #folder_id = models.IntegerField()
    #user = models.ForeignKey(User)
    
    class Meta:            
        ordering = ['name', '-init_date']
#        unique_together = (("folder_id","user"), ("name","user"),)

    def __unicode__(self):
        return self.name
        
    #~ def getName(self, v):
        #~ return 


class Frame_Folder(Folder):
    pass    
        

#think of implementing this with NonSql
#Fold similiar notes together, and only show the reprensentative one. TODO:
#For notes folded, if not the representative one, mark them as deleted. So they never show up
#in normal notes list. And for the representative one, just provide more notes as alternative explanations
#===============================================================================
# class Fold(models.Model):
#    repr =  models.ForeignKey(Note)
#    note_ids =  models.CharField(blank=False,max_length=800)   
#    
#===============================================================================
       


class Cache(models.Model):
    note_ids =  models.CharField(blank=False,max_length=800)
#    cache_id = models.IntegerField()
#    user = models.ForeignKey(User)
    
#    class Meta:
#        unique_together = (("cache_id","user"),)
    
    def __unicode__(self):
        return self.note_ids


class Frame_Cache(Cache):
    cache_id = models.AutoField(primary_key=True)


#Store the alternative language translation for notes.
class Note_Translation(models.Model):
    note = models.ForeignKey(Note)
    LANG_TYPE_CHOICES = (
        ('C', 'Chinese'),
        ('E', 'English'),
    )
    lang = models.CharField(max_length=1, choices=LANG_TYPE_CHOICES, verbose_name=ugettext_lazy('Language'),) #mark the language in the original note
    original_lang = models.CharField(max_length=1, choices=LANG_TYPE_CHOICES, verbose_name=ugettext_lazy('Original language'),)
    title = models.CharField(verbose_name=ugettext_lazy('Title'), blank=True,max_length=2000, help_text=_("The size of the title is limited to 2000 characaters."))
    desc =  models.TextField(verbose_name=ugettext_lazy('Description'), max_length=2000, blank=True,  help_text=_("The size of the desc is limited to 2000 characaters."))
    
    
       

#TODO:should this table be here?
class UserAuth(models.Model):
    user = models.ForeignKey(User)
    site = models.CharField(blank=False,max_length=20)
    access_token_key = models.CharField(blank=False,max_length=80)
    access_token_secret  = models.CharField(blank=False,max_length=80)
    #TODO: store user's profile name on the site?
    #profile_name = models.CharField(blank=False,max_length=80)
    
    class Meta:
        unique_together = (("user","site"),)
    
    
    def __unicode__(self):
        return self.user.__unicode__()+'@'+site
    
    
def getAccessKey(username, site):
    user = User.objects.get(username=username)   
    ua = UserAuth.objects.get(user=user, site=site) 
    return ua.access_token_key, ua.access_token_secret

def getBoundSites(username):
    user = User.objects.get(username=username)   
    uas = UserAuth.objects.filter(user=user)
    return [ua.site for ua in uas]
    

from django.contrib import admin    
    
def _create_model(name, base=models.Model, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)


    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (base,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass
        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model    

#TODO: will this only create one model instead of duplicated
def create_model(name, base, owner_name, #db_table, 
                 fields={}, options={}):
    '''create a proxy model using a MultiUserManager manager.'''
    #fields.update({'objects':MultiUserManager(owner_name)})
#    if base==Note or base==LinkageNote:
#        fields.update({'attachment':models.FileField(upload_to='noteattachments/'+owner_name+'/%Y/%m/%d', blank=True) })
        
    options.update({'proxy':True})
    fields.update({'owner_name':owner_name})
    #options.update({'db_table':db_table})
    return _create_model(name=name, base=base, fields=fields,
                        app_label='notebook.notes', module='notebook.notes.models', options=options)


def create_model_form(name, model, base=ModelForm, fields={}, options={}): 
    from django import forms     
    if 'tags' in dir(model):  
   
        if ('tags' not in fields) and (not options.get('exclude') or 'tags' not in options.get('exclude')):           
    #    fields.update({'tags':forms.ModelMultipleChoiceField(queryset=Tag.objects.filter(user__username__exact=model.objects.owner_name).order_by('name'))})
            fields.update({'tags':forms.ModelMultipleChoiceField(queryset=Tag.objects.using(model.owner_name).all().order_by('name'))})
    
    if 'notes' in dir(model):   
        if (not options.get('exclude')) or ('notes' not in options.get('exclude')):                 
    #    fields.update({'tags':forms.ModelMultipleChoiceField(queryset=Tag.objects.filter(user__username__exact=model.objects.owner_name).order_by('name'))})
            fields.update({'notes':forms.ModelMultipleChoiceField(queryset=Note.objects.using(model.owner_name).all().order_by('id'))})
    
         
    options.update({'model':model})
    return _create_model(name=name, base=base, fields=fields,
                        app_label='notebook.notes', module='notebook.notes.models', options=options)
    
    
    
