from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.forms import ModelForm
from django.db.models import Q, F, Avg, Max, Min, Count
from django.utils import simplejson
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage

import datetime

from notebook.notes.models import Note, Tag, create_model, WorkingSet
from notebook.bookmarks.models import Bookmark
from notebook.scraps.models import Scrap
from notebook.social.models import Member, Group, Social_Note, Social_Tag, Social_Note_Vote, Social_Note_Comment, Social_Snippet, Social_Bookmark, Social_Scrap, Friend_Rel

from notebook.notes.views import User, getT, getW, getlogger, getFolder, get_public_notes, __get_folder_context
from notebook.notes.views import getSearchResults,  __getQStr, __get_view_theme, Pl, ALL_VAR


log = getlogger('social.views')  

#TODO: make this the same as in notebook.notes.views
book_entry_dict = {'notebook':'note', 'snippetbook':'snippet','bookmarkbook':'bookmark', 'scrapbook': 'scrap'}
  

def getN(username):
    return create_model("N_"+str(username), Note, username)

def getB(username):
    return create_model("B_"+str(username), Bookmark, username)

def getS(username):
    return create_model("S_"+str(username), Scrap, username)

#TODO: for now, social db is not used. Instead default is used to put those social data because social data needs user which is in default db
#otherwise, need to copy the user table over to social
#def getG():
#    return create_model("G", Group, 'default') 

G = Group

#def getSN():
#    return create_model("SN", Social_Note, 'default')

SN = Social_Note

#def getST():
#    return create_model("ST", Social_Tag, 'default')

ST = Social_Tag






class AddGroupForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Group  
        exclude = ()     
        #fields = ('type_of_linkage','desc','tags','title','private', 
        #            'attachment','notes')
        





@login_required
def wall_snippets(request, username):
    N = getN(username) 
    ns = N.objects.all().order_by('-init_date')[:30]
    #get groups for this user
    gs = G.objects.filter(members__username=username)    
    return render_to_response('social/wall_snippets.html', {'ns':ns, 'gs':gs,  'profile_username':username, 'book_name': 'snippets'}, context_instance=RequestContext(request))


@login_required
def wall_bookmarks(request, username):
    N = getN(username) 
    ns = N.objects.all().order_by('init_date')[:30]
    #get groups for this user
    gs = G.objects.filter(members__username=username)    
    return render_to_response('social/wall_snippets.html', {'ns':ns, 'gs':gs,  'profile_username':username, 'book_name': 'snippets'}, context_instance=RequestContext(request))


@login_required
def wall_scraps(request, username):
    N = getN(username) 
    ns = N.objects.all().order_by('init_date')[:30]
    #get groups for this user
    gs = G.objects.filter(members__username=username)    
    return render_to_response('social/wall_snippets.html', {'ns':ns, 'gs':gs,  'profile_username':username, 'book_name': 'snippets'}, context_instance=RequestContext(request))



@login_required
def wall(request, username):
    N = getN(username)
    B = getB(username)
    S = getS(username)
    today = datetime.date.today()
    yesterday  = today - datetime.timedelta(1)
    day_bf_yest = today - datetime.timedelta(2)
    ns = N.objects.all().order_by('init_date')[:10]
    bs = B.objects.all().order_by('init_date')[:10]
    ss = S.objects.all().order_by('init_date')[:10]
        
    #get groups for this user
    gs = G.objects.filter(members__username=username)    
    
    return render_to_response('social/wall.html', {'ns':ns, 'bs':bs, 'ss':ss, 'gs':gs}, context_instance=RequestContext(request))


@login_required
def group_index(request, groupname):
    
    return HttpResponseRedirect('/groups/'+groupname+'/snippetbook/') 



def get_groups_created_by_self(request, username):
    if username == request.user.username:
        gs_created_by_self = G.objects.filter(admins__username=username)  
    else:
        gs_created_by_self = G.objects.filter(admins__username=username, private=False)      
    return gs_created_by_self


def get_groups_following(request, username):
    if username == request.user.username:
        gs_created_by_self = G.objects.filter(members__username=username).exclude(admins__username=username)  
    else:
        gs_created_by_self = G.objects.filter(members__username=username, private=False).exclude(admins__username=username)
    return gs_created_by_self


@login_required
def profile(request, username):
    gs_created = get_groups_created_by_self(request, username)
    gs_following = get_groups_following(request, username)  
    profile_member = Member.objects.get(username=username)  
    return render_to_response('social/profile.html', {'gs_created':gs_created, 'gs_following':gs_following, \
                                                      'profile_user':User.objects.get(username=username), \
                                                      'profile_member':profile_member, 'profile_username':username}, context_instance=RequestContext(request))


@login_required
def friends(request, username):
    #friends = request.user.member.get_friends()
    return render_to_response('social/friends.html', {}, context_instance=RequestContext(request))




#TODO: think of getting username arg, since you can get it from request. Also think of 
# get rid of it in the url.py, changing to personal, or my
@login_required
def groups(request, username):
    gs_created_by_self = get_groups_created_by_self(request, username)
    gs_following = get_groups_following(request, username)
    addGroupForm = AddGroupForm(initial={'admins': [username]})
    T = getT(username) 
    tags = T.objects.filter(private=False)
    
    return render_to_response('social/groups.html', {'gs_created_by_self':gs_created_by_self, 'gs_following':gs_following,\
                                                      'addGroupForm':addGroupForm, 'tags':tags}, context_instance=RequestContext(request))


#TODO: check if the group already exists
@login_required
def add_group(request, username):
    #T = getT(username) 
    post = request.POST.copy()
    
    #TODO: move logic below to group.add_tags
    tag_names = post.getlist('item[tags][]')
    tags = [ST.objects.get(name=tag_name).id for tag_name in tag_names]
    if not tag_names:    
        #TODO: give an error page, also validation on the form       
        messages.error(request, "No tags are entered!")     
    post.setlist('tags', tags) 
    g = G()
    
#    g.creator = request.user
#    
#    g.name = post.get('name')
#    g.desc = post.get('desc')
#    g.private = post.get('private')
#    g.save()
#    
#    g.members.add(request.user)
#    g.admins.add(request.user)
#    
#    
#    g.tags = tags
    
    #TODO: whether new tags can be created in the social space?
    
    f = AddGroupForm(post, instance=g)
    
    log.debug("add group form errors:"+str(f.errors))
    
    f.save()    
    #TODO: handel tags that are created in the social space (might need to push back to the
    #personal space.)
    
    print 'newly created group name:', g.name
    
    #add sharinggroup:groupname as a new tag for this group
    gtn = "sharinggroup:"+g.name 
    st = ST(name=gtn, private=g.private)
    st.save()
    g.tags.add(st)
    
    #TODO: might modify Group model's save method to push group tags all back to user personal space
    #push this group tag back to the user's personal space
    #T = getT(username=gtn)
    #T.objects.get_or_create(name=gtn, private=g.private)
    
    push_group_tags_back(request, g.name)
    
    
    
    return HttpResponseRedirect('/'+username+'/groups/')    



#TODO: so far automatically push all back. In the future, after for user confirmation
#push group tags back to the user's space, also create a working set with the group name
@login_required
def push_group_tags_back(request, groupname):
    username = request.user.username
    T = getT(username)
    g = Group.objects.get(name=groupname)
    sts = g.tags.all()
    W = getW(username)
    w1, created  = W.objects.get_or_create(name='snippetbook')    
    w2, created  = W.objects.get_or_create(name='bookmarkbook')   
    w3, created  = W.objects.get_or_create(name='scrapbook')
    w, created  = W.objects.get_or_create(name="sharinggroup:"+g.name)
    
    for st in sts:
        t, created = T.objects.get_or_create(name=st.name)
        if created:
            t.private = st.private
        w1.tags.add(t) 
        w2.tags.add(t) 
        w3.tags.add(t) 
        w.tags.add(t)
        


book_model_dict = {'snippetbook':Social_Snippet,'bookmarkbook':Social_Bookmark, 'scrapbook': Social_Scrap}

def getSN(bookname):
    return book_model_dict.get(bookname)

@login_required
def notes(request, username, bookname):
    #profile_user = 
    note_list = book_model_dict.get(bookname).objects.filter(owner__username=username)       
    qstr = __getQStr(request)    
    note_list  = getSearchResults(note_list, qstr)
    sort, order_type,  paged_notes, cl = __get_notes_context(request, note_list)    
    
    #For now, no tags in a user's social page. Later might bring the tags from user's own db and display here.
    tags = []
    

    #So far, get folders from users' personal space, but need to be public folders TODO:
    F = getFolder(username, bookname)    
    #folders = F.objects.all()   
#    if request.user.username != username:
#        log.debug('Not the owner, getting public folders only...')      
    folders = F.objects.filter(private=False).order_by('name') 
    
    
    return render_to_response('social/social_notes.html', {'note_list':paged_notes,'sort':sort, 'bookname':bookname, \
                               'folders':folders, 'profile_username':username, 'appname':'social', 'cl':cl},\
                                                  context_instance=RequestContext(request))


@login_required
def folders(request, username, bookname, foldername):
    F = getFolder(username, bookname)    
    #T = getT(username)
    SN = getSN(bookname)
    note_list = SN.objects.filter(owner__username=username)
    if request.user.username != username:
        log.debug( 'Not the owner of the notes requested, getting public notes only...')
        #For the time being, still apply this. TODO:
        note_list = get_public_notes(note_list)    
        
    qstr = ""
    current_folder = None
    if foldername:        
        current_folder = F.objects.get(name=foldername)     
        qstr = current_folder.value        
        note_list  = getSearchResults(note_list, qstr)   
    sort, order_type,  paged_notes, cl = __get_notes_context(request, note_list)           
    folders = F.objects.filter(private=False).order_by('name') 
    
    return render_to_response('social/social_folders.html',  {'note_list':paged_notes,'sort':sort, 'bookname':bookname, \
                              'folders':folders, 'is_in_folders':True, 'current_folder':current_folder,
                               'profile_username':username, 'appname':'social', 'cl':cl}, context_instance=RequestContext(request))
     


@login_required
def add_friend(request, username):
    m1 = request.user.member
    m2 = Member.objects.get(username=username)     
    f = Friend_Rel(friend1=m1, friend2=m2)
    #So far, make it confirmed automcatically. TODO:
    f.comfirmed = True
    f.save()
    return HttpResponseRedirect('/social/'+username+'/')  
    


#what to do with tags in the user space if the group is removed? I think it is to keep it there. 
#But how about the special sharinggroup tag? Should be removed, right?

@login_required
def join_group(request, groupname):
    user = request.user
    group = G.objects.get(name=groupname)  
    group.members.add(user.member)
    group.save()
    push_group_tags_back(request, group.name)
    return HttpResponseRedirect('/groups/'+groupname+'/snippetbook/')
    


@login_required
def group_admin(request, groupname):
    g = G.objects.get(name=groupname) 
    #TODO: move below to a decorator
    if request.user.member not in g.admins.all():
        return HttpResponse("You are not an admin of this group, and thus cannot admin this group.", mimetype="text/plain") #TODO: translate
    
    tags = Social_Tag.objects.all().order_by('name')
    return render_to_response('social/admin/group.html', {'group':g,'tags':tags,\
                                                      }, context_instance=RequestContext(request))


#delete a member won't remove the group:groupname workingset from member's personal space 
@login_required    
def group_delete_member(request, groupname):
    g = G.objects.get(name=groupname) 
    #TODO: move below to a decorator
    if request.user.member not in g.admins.all():
        return HttpResponse("You are not an admin of this group, and thus cannot admin this group.", mimetype="text/plain")
    member_id = request.POST.get('member_id')
    member = User.objects.get(id=member_id)
    g.members.remove(member)
    g.admins.remove(member)
    return HttpResponse('successful', mimetype="text/plain")  
    
    
@login_required
def group_add_tags(request, groupname):
    tag_names = request.POST.getlist('item[tags][]')
    tags = [ST.objects.get(name=tag_name).name for tag_name in tag_names]
    if not tag_names:    
        #TODO: give an error page, also validation on the form       
        messages.error(request, "No tags are entered!")   
    group = G.objects.get(name=groupname)   
    
    username = request.user.username
    
    #group.add_tags(request.username, tags)
    #TODO: separate Tag, workingSet out of notebook.notes.models otherwise cannot import Tag, WorkingSet 
    for tag_name in tags: 
            #In the social space, the tag cannot be created alone. It has to be already existing.    
            t, created = Social_Tag.objects.get_or_create(name=tag_name) 
            #TODO: if not created, whether add this tag to all three books?
            if created:
                #should push back to the user's space
                user_tag, created = Tag.objects.using(username).get_or_create(name=tag_name)  
                #add this user_tag to users' three books
                w = WorkingSet.objects.using(username).get(name='snippetbook')                
                try:             
                    w.tags.add(t)
                except Exception as inst:
                    print type(inst)     
                    print inst.args      
                    print inst            
                    x, y = inst          
                    print 'x =', x
                    print 'y =', y   
                    
                w = WorkingSet.objects.using(username).get(name='bookmarkbook')                
                try:             
                    w.tags.add(t)
                except Exception as inst:
                    print type(inst)     
                    print inst.args      
                    print inst            
                    x, y = inst          
                    print 'x =', x
                    print 'y =', y    
                    
                w = WorkingSet.objects.using(username).get(name='scrapbook')                
                try:             
                    w.tags.add(t)
                except Exception as inst:
                    print type(inst)     
                    print inst.args      
                    print inst            
                    x, y = inst          
                    print 'x =', x
                    print 'y =', y           
            
            group.tags.add(t)            
    group.save()   
    
    return HttpResponseRedirect('/groups/'+groupname+'/admin/')
     


@login_required
def group_remove_tag(request, groupname):
    tag_id = request.POST.get('tag_id')
    tag = ST.objects.get(id=tag_id)
    group = G.objects.get(name=groupname) 
    group.tags.remove(tag)
    #TODO: update user's group working set
    return HttpResponse('successful', mimetype="text/plain")  
    
    
    


@login_required
def group(request, groupname, bookname):
    
    gs = G.objects.filter(members__username=request.user.username)  
    group = G.objects.get(name=groupname)  
    #tags = [t for t in group.tags.all()] 
    
    log.debug('tags of the group:'+str(group.tags.all()))
    
    tag_names = [tag.name for tag in group.tags.all()]
    
#    if bookname == 'scraps':  
#        note_list = Social_Scrap.objects.filter(tags__name__in=tag_names, owner__in=group.members.all())   
#              
#    elif bookname == 'bookmarks':
#        note_list = Social_Bookmark.objects.filter(tags__name__in=tag_names, owner__in=group.members.all())    
#    else:
#        #default snippets
#        note_list = Social_Snippet.objects.filter(tags__name__in=tag_names, owner__in=group.members.all())
        
    q1 = Q(tags__name__in=tag_names, owner__in=group.members.all(), private=False)   
    q2 = Q(tags__name="sharinggroup:"+groupname, private=True) 
    note_list = book_model_dict.get(bookname).objects.filter(q1 | q2)    
        
    #log.debug('All snippets of the group '+groupname+' :'+str(notes))
        
    #notes.sort(key=lambda r: r.init_date)  
    
    
    qstr = __getQStr(request)
    
    note_list  = getSearchResults(note_list, qstr)
    
    #print 'group notes:', note_list
    #sort, delete, private, date_range, order_type, with_attachment, paged_notes,  cl = __get_notes_context(request, note_list) 
    sort, order_type,  paged_notes, cl = __get_notes_context(request, note_list) 
      
    #group.tags.all()
    #tags = Social_Tag.objects.filter(group=group).order_by('name')#.annotate(Count('social_'+book_entry_dict.get(bookname))).order_by('name')
    tags = get_group_tags(request, groupname, bookname)
    return render_to_response('social/group_notes.html', {'group':group, 'gs':gs, 'note_list':paged_notes,'sort':sort, 'bookname':bookname, \
                                                 'tags':tags, 'appname':'groups', 'cl':cl},\
                                                  context_instance=RequestContext(request))




@login_required
def notes_tag(request, username, bookname, tag_name):   
    note_list = book_model_dict.get(bookname).objects.filter(tags__name=tag_name, owner__username=username)
    qstr = __getQStr(request)    
    note_list  = getSearchResults(note_list, qstr)
    sort, order_type,  paged_notes, cl  = __get_notes_context(request, note_list) 
    #TODO: provide tags for social public notebook
    tags = []#Social_Tag.objects.filter(notes_set=note_list).order_by('name')
    
    return render_to_response('social/social_notes.html', {'note_list':paged_notes,'sort':sort, 'current_tag':tag_name, 'bookname':bookname,\
                               'profile_username':username, 'tags':tags, 'appname':'social', 'cl':cl},\
                                                  context_instance=RequestContext(request)) 




def get_group_tags(request, groupname, bookname):
    group = G.objects.get(name=groupname) 
    tags_qs = group.tags.all().order_by('name')    
    SN = getSN(bookname)
    tags = []
    for tag in tags_qs:
        count = SN.objects.filter(tags=tag).count()
        t = {'name':tag.name, 'private':tag.private, 'note_count':count}
        tags.append(t)
    return tags    


@login_required
def group_tag(request, groupname, bookname, tag_name):    
    group = G.objects.get(name=groupname)  
    
#    if bookname == 'scraps':  
#        note_list = Social_Scrap.objects.filter(tags__name=tag_name, owner__in=group.members.all())         
#    elif bookname == 'bookmarks':
#        note_list = Social_Bookmark.objects.filter(tags__name=tag_name, owner__in=group.members.all())    
#    else:
#        #default snippets
#        note_list = Social_Snippet.objects.filter(tags__name=tag_name, owner__in=group.members.all())
    #print 'getting notes of tag:', tag_name, ' of bookname:', bookname
    note_list = book_model_dict.get(bookname).objects.filter(tags__name=tag_name, owner__in=group.members.all())
    #print 'notes of the tag:', note_list
    qstr = __getQStr(request)    
    note_list  = getSearchResults(note_list, qstr)
    sort, order_type,  paged_notes, cl  = __get_notes_context(request, note_list) 
    tags = get_group_tags(request, groupname, bookname)
    return render_to_response('social/group_notes.html', {'group':group, 'note_list':paged_notes,'sort':sort, 'current_tag':tag_name, 'bookname':bookname,\
                                                 'tags':tags, 'appname':'groups', 'cl':cl},\
                                                  context_instance=RequestContext(request))
    

@login_required
def vote_useful(request):  
    note_id = request.POST.get('id')       
    note = SN.objects.get(id=note_id)
    snv, created = Social_Note_Vote.objects.get_or_create(note=note,voter=request.user.member)    
    snv.useful=True
    snv.save()  
    result = str(note.get_useful_votes())+'/'+str(note.get_total_votes())
    print result  
    return HttpResponse(result, mimetype="text/plain") 

@login_required
def vote_unuseful(request):  
    note_id = request.POST.get('id')       
    note = SN.objects.get(id=note_id)
    snv, created = Social_Note_Vote.objects.get_or_create(note=note,voter=request.user.member)    
    snv.useful=False
    snv.save()  
    result = str(note.get_useful_votes())+'/'+str(note.get_total_votes())
    print result  
    return HttpResponse(result, mimetype="text/plain")          


@login_required
def group_add_comment(request):  
    note_id = request.POST.get('id')
    #N = getN(username)    
    note = SN.objects.get(id=note_id)
    content = request.POST.get('content')
    #NC = getNC(username)
    nc = Social_Note_Comment(note=note, commenter=request.user, desc=content)
    nc.save()
    return  HttpResponse(simplejson.dumps({'note_id':note_id, 'content':content}),
                                                                     "application/json")


@login_required   
def group_delete_comment(request):
    #note_id = request.POST.get('id')
    comment_id = request.POST.get('comment_id')    
    
    nc = Social_Note_Comment.objects.get(id=comment_id)
    nc.delete()
    return HttpResponse('successful', mimetype="text/plain")  





def __get_notes_context(request, note_list):
    theme = __get_view_theme(request)
    #view_mode = theme['view_mode']
    order_field = theme['sort']   
    #delete =    theme['delete']   
    #private =    theme['private']   
    #date_range = theme['date_range']
    #with_attachment = theme['with_attachment']
    
#    
#    if delete in true_words:
#        note_list = note_list.filter(deleted=True)
#    else:
#        note_list = note_list.filter(deleted=False)           
    
#    
#    if private in ['All', 'all']:
#        pass
#    else:
#        if private in true_words:
#            note_list = note_list.filter(private=True)
#        else:          
#            note_list = note_list.filter(private=False)    
        
#    now = date.today()
#
#                                            )    
#    if date_range in ['All', 'all']:
#        pass
#    elif date_range == 'today':
#        note_list = note_list.filter(init_date__day= now.day, init_date__month=now.month, init_date__year= now.year) 
#    elif date_range == 'past7days':
#        one_week_ago = now - datetime.timedelta(days=7)
#        note_list = note_list.filter(init_date__gte=one_week_ago.strftime('%Y-%m-%d'),  init_date__lte=now.strftime('%Y-%m-%d 23:59:59'))     
#    elif date_range == 'this_month':
#        note_list = note_list.filter(init_date__month=now.month, init_date__year= now.year) 
#    elif date_range == 'this_year':  
#        note_list = note_list.filter(init_date__year= now.year) 
#    
#        
#    if with_attachment in ['All', 'all']:
#        pass
#    elif with_attachment in true_words:
#        try:
#            note_list = note_list.filter(attachment__startswith='noteattachments/') #TODO: hard coded, change
#        except FieldError:
#            pass  
    
    order_type = request.GET.get('order_type','desc')  
    
    

    sorted_note_list = note_list    
    if order_field != 'usefulness':  
        sorted_note_list = note_list.order_by('%s%s' % ((order_type == 'desc' and '-' or ''), order_field)) 
    else:       
        #Social_Note has usefulness
        sorted_notes = [(note, note.get_usefulness()) for note in note_list]   
        sorted_notes.sort(key=lambda r: r[1],reverse = (order_type == 'desc' and True or False))  
        sorted_note_list = [r[0] for r in sorted_notes]
    #for social pages, only show 20 notes per page since it is not edited much
    list_per_page = 20
    paginator = Paginator(sorted_note_list, list_per_page) 
   
    #using code from the admin module
    cl = Pl(request)
    from django.contrib.admin.views.main import MAX_SHOW_ALL_ALLOWED 
    cl.show_all = ALL_VAR in request.GET
    result_count = paginator.count
    cl.can_show_all = result_count <= MAX_SHOW_ALL_ALLOWED
    cl.multi_page = result_count > list_per_page
    if (cl.show_all and cl.can_show_all):        
        paginator = Paginator(sorted_note_list, MAX_SHOW_ALL_ALLOWED )        
    
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('p', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        paged_notes = paginator.page(page)
    except (EmptyPage, InvalidPage):
        paged_notes = paginator.page(paginator.num_pages)          
    
    cl.paginator = paginator    
    cl.page_num = page
    cl.result_count = len(sorted_note_list)    

    return  order_field, order_type,  paged_notes, cl    
    