from notebook.notes.models import Note, Tag, LinkageNote, Folder, Cache, WorkingSet, UserAuth
from notebook.social.models import Group, Social_Note, Social_Tag, Member, Social_Note_Comment, Social_Note_Vote, Friend_Rel
from django.contrib import admin
from django.contrib.auth.models import User #, Group

from notification.models import Notice, NoticeType
from postman.models import Message


class MultiDBModelAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.
    using = 'default'
    #using = 'yuanxi'
    

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super(MultiDBModelAdmin, self).queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request=request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request=request, using=self.using, **kwargs)
        

class NotesAdmin(MultiDBModelAdmin):
    list_display = ('desc', 'title', 'display_tags', 'init_date','last_modi_date','private','deleted')
    #list_display = ('title', 'desc','display_tags')
    list_filter = ['init_date','tags','deleted']
    search_fields = ['title','desc']
    date_hierarchy = 'init_date'
    list_per_page = 30
    #list_editable = ('desc','private')

class LinkageNotesAdmin(MultiDBModelAdmin):
    list_display = ('desc','title','init_date','last_modi_date','private','deleted')
    list_filter = ['init_date','tags','deleted']
    search_fields = ['title','desc']
    date_hierarchy = 'init_date'
    list_per_page = 30
    select_related = ('tags','notes')  
    #list_editable = ('desc','private')

class TagAdmin(MultiDBModelAdmin):
    pass
    
class FolderAdmin(MultiDBModelAdmin):
    pass  

class CacheAdmin(MultiDBModelAdmin):
    pass
    
class UserAdmin(MultiDBModelAdmin):
     list_display = ('username', 'email', 'last_login')  
     ordering = ('-last_login',)

class GroupAdmin(MultiDBModelAdmin):
    pass

class Social_NoteAdmin(MultiDBModelAdmin):
     list_display = ('id','title', 'desc', 'private', 'deleted','init_date', 'owner', 'owner_note_id') 
     select_related = ('tags')  
     search_fields = ['title','desc','owner_note_id']

class Social_Note_CommentAdmin(MultiDBModelAdmin):
     list_display = ('note', 'desc', 'commenter', 'init_date') 

class Social_TagAdmin(MultiDBModelAdmin):
     list_display = ('id', 'name', 'private')  
     search_fields = ['name', 'id']

class Social_Note_VoteAdmin(MultiDBModelAdmin):
     list_display = ('note', 'voter', 'useful', 'init_date') 

class Friend_RelAdmin(MultiDBModelAdmin):
     list_display = ('friend1', 'friend2', 'init_date', 'confirmed')  

class UserAuthAdmin(MultiDBModelAdmin):
     list_display = ('user', 'site')  

  
   
class NoticeAdmin(MultiDBModelAdmin):
     list_display = ('recipient', 'sender', 'message', 'added') 

class NoticeTypeAdmin(MultiDBModelAdmin):
     list_display = ('label', 'display', 'description') 

class MessageAdmin(MultiDBModelAdmin):
     list_display = ('subject', 'body', 'sender','recipient','sent_at','read_at') 




site = admin.AdminSite()

site.register(Note,NotesAdmin)
site.register(Tag, TagAdmin)
site.register(LinkageNote,LinkageNotesAdmin)
site.register(Folder, FolderAdmin)
site.register(Cache, CacheAdmin)
site.register(WorkingSet)
site.register(Group)
site.register(Social_Note, Social_NoteAdmin)
site.register(Social_Tag, Social_TagAdmin)
site.register(Member)
site.register(User, UserAdmin)
site.register(Social_Note_Comment, Social_Note_CommentAdmin)
site.register(Social_Note_Vote, Social_Note_VoteAdmin)
site.register(Friend_Rel, Friend_RelAdmin)
site.register(UserAuth, UserAuthAdmin)




#site.register(Group, GroupAdmin)

#should comment out below
site.register(Notice, NoticeAdmin)
site.register(NoticeType, NoticeTypeAdmin)
site.register(Message, MessageAdmin)



#TODO: register Site as well



