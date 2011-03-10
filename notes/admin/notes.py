from notebook.notes.models import Note, Tag, LinkageNote, Folder, Cache, WorkingSet
from notebook.social.models import Group, Social_Note, Social_Tag, Member
from django.contrib import admin
from django.contrib.auth.models import User #, Group


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
    pass   

class GroupAdmin(MultiDBModelAdmin):
    pass

site = admin.AdminSite()

site.register(Note,NotesAdmin)
site.register(Tag, TagAdmin)
site.register(LinkageNote,LinkageNotesAdmin)
site.register(Folder, FolderAdmin)
site.register(Cache, CacheAdmin)
site.register(WorkingSet)
site.register(Group)
site.register(Social_Note)
site.register(Social_Tag)
site.register(Member)
site.register(User, UserAdmin)
#site.register(Group, GroupAdmin)

#TODO: register Site as well



