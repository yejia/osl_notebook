from django import template

register = template.Library()





@register.inclusion_tag('framebook/notes/note/children.html',  takes_context=True)
def tree_view_tag(context, frame):    
    frame.owner_name = context['profile_username']   
    print 'frame.owner_name:', frame.owner_name
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