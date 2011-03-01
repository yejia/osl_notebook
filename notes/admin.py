from notebook.notes.models import Note, Tag, LinkageNote, Folder, WorkingSet
from notebook.social.models import Group
from django.contrib import admin

class NoteAdmin(admin.ModelAdmin):
    list_display = ('title','event','desc','init_date','last_modi_date','private')
    list_filter = ['init_date']
    search_fields = ['title','event','desc']
    date_hierarchy = 'init_date'
    list_per_page = 20

admin.site.register(Note,NoteAdmin)
admin.site.register(Tag)

admin.site.register(LinkageNote)
admin.site.register(Folder)

