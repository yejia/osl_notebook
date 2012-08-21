from django import template

register = template.Library()

from notebook.snippets.models import Snippet
from notebook.bookmarks.models import Bookmark
from notebook.scraps.models import Scrap
from notebook.notes.models import Frame, Note

from notebook.notes.constants import *

@register.inclusion_tag('framebook/notes/note/children.html',  takes_context=True)
def tree_view_tag(context, frame):    
    frame.owner_name = context['profile_username']   
    #print 'frame.owner_name:', frame.owner_name
    sort = context['sort'] 
    children = frame.get_notes_in_order(sort) 
    for child in children:
        child.owner_name = frame.owner_name
    return {'children': children, 'profile_username':context['profile_username'], \
            'book_uri_prefix':context['book_uri_prefix'], 'sort':sort, 'pick_lang':context['pick_lang']}



@register.inclusion_tag('framebook/notes/note/children.html',  takes_context=True)
def social_tree_view_tag(context, frame):       
    sort = context['sort'] 
    children = frame.get_notes_in_order(sort) 
    return {'children': children, \
            'book_uri_prefix':context['book_uri_prefix'], 'sort':sort, 'pick_lang':context['pick_lang']}
    


from notebook.tags.views import AddTagFrameForm    

@register.inclusion_tag('tagframes/children.html',  takes_context=True)
def tag_tree_view_tag(context, frame):    
    frame.owner_name = context['profile_username']   
    #print 'frame.owner_name:', frame.owner_name
    sort = context['sort'] 
    children = frame.get_tags_in_order(sort) 
    for child in children:
        child.owner_name = frame.owner_name
        if child.get_tag_type() == 'Leaf' or child.note_set.count():            
            child.snippets_count = Snippet.objects.using(child.owner_name).filter(deleted=False, tags=child).count() 
            child.public_snippets_count = Snippet.objects.using(child.owner_name).filter(deleted=False, private=False, tags=child).count()
            child.bookmarks_count = Bookmark.objects.using(child.owner_name).filter(deleted=False, tags=child).count() 
            child.public_bookmarks_count = Bookmark.objects.using(child.owner_name).filter(deleted=False,private=False, tags=child).count() 
            child.scraps_count = Scrap.objects.using(child.owner_name).filter(deleted=False, tags=child).count() 
            child.public_scraps_count = Scrap.objects.using(child.owner_name).filter(deleted=False, private=False, tags=child).count()
            child.frames_count = Frame.objects.using(child.owner_name).filter(deleted=False, tags=child).count() 
            child.public_frames_count = Frame.objects.using(child.owner_name).filter(deleted=False, private=False, tags=child).count()
            child.notes_count = Note.objects.using(child.owner_name).filter(deleted=False, tags=child).count() 
            child.public_notes_count = Note.objects.using(child.owner_name).filter(deleted=False, private=False, tags=child).count()
    
    addTagFrameForm = AddTagFrameForm()
    
    
    return {'children': children, 'profile_username':context['profile_username'], \
             'sort':sort, 'addTagFrameForm':addTagFrameForm, 'frame':frame, 
              'username':context['username'], 'profile_username':context['profile_username'], 'all_words':all_words,'private':context['private'],
              'true_words':context['true_words'], 'all_words':context['all_words'], 'false_words':context['false_words'] 
              #'pick_lang':context['pick_lang']
             }    