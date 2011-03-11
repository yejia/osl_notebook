from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.forms import ModelForm
from django.db.models import Q, F, Avg, Max, Min, Count
from django.db import connection
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils import simplejson
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.core.mail import send_mass_mail

from notebook.notes.models import Note, Tag, LinkageNote, Folder, WorkingSet, create_model, create_model_form, getNC, getW, getT, getL
from notebook.snippets.models import Snippet
from notebook.bookmarks.models import Bookmark
from notebook.scraps.models import Scrap
from notebook.social.models import Member, Friend_Rel


import notebook

import datetime
from datetime import date
import re
import operator

import logging


#TODO: group methods together and separate to another view, for example, setting, linkage, folders, cache...
#  also in url.py, map to those views


#TODO: let different log level message go to different files
def getlogger(name):
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler(notebook.settings.LOG_FILE)    
    formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s%(name)s,%(pathname)s,line%(lineno)d,process%(process)d,thread%(thread)d,"%(message)s"','%Y-%m-%d %a %H:%M:%S')    
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(notebook.settings.LOG_LEVEL)
    return logger

log = getlogger('notes.views')


    

#TODO: add post or pre processor to filter all ressult with user__username__exact=username, or maybe create db view and swtich
#among different view according to the username.
#or maybe subclass QuerySet and for every query, add user__username__exact=username filter. But this might cause slow performance.

ALL_VAR = 'all'
true_words = [True, 'True', 'true', 'Yes', 'yes', 'Y', 'y']
#TODO: not used
sort_dict = {'vote':'Vote', 'title':'Title', 'desc': 'Desc', 'init_date': 'Creation Date', 
             'last_modi_date':'Last Modification Date'}

books = ['notebook', 'snippetbook','bookmarkbook', 'scrapbook']

class AddLinkageNoteForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = LinkageNote   
        exclude = ('tags')     
        #fields = ('type_of_linkage','desc','tags','title','private', 
        #            'attachment','notes')
        
class UpdateLinkageNoteForm(ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = LinkageNote
        exclude = ('id', 'notes', 'tags')        

class AddTagForm(ModelForm): 
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Tag
 
class UpdateTagForm(ModelForm): 
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Tag
        exclude = ('id','user') 
        
        
class AddFolderForm(ModelForm): 
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Folder
 
class UpdateFolderForm(ModelForm): 
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Folder
        exclude = ('id','user') 

class UpdateWSForm(ModelForm): 
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = WorkingSet
        exclude = ('id','tags')   
        
        
class ProfileForm(ModelForm): 
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Member
        exclude = ('username','password', 'is_staff', 'is_active', 'is_superuser',\
                    'id', 'user_permissions', 'groups', 'role', 'last_login', 'date_joined')  
        

#class RegistrationForm(ModelForm): 
#    error_css_class = 'error'
#    required_css_class = 'required'
#    class Meta:
#        model = Member
#        fields = ('username')  
                       
    
def logout_view(request): 
    logout(request)
    log.debug('User logged out!')
    #render_to_response('registration/login.html',{'form':None})
    return HttpResponseRedirect('/login/') 


def login_user(request): 
    username = request.POST['username']
    password = request.POST['password']
    log.debug('username:'+username)
    
    user = authenticate(username=username, password=password)
    log.debug('user:'+str(user))
    if user is not None:        
        if user.is_active:
            login(request, user)
            next = request.POST.get('next')            
            if next:
                return HttpResponseRedirect(next)           
            return HttpResponseRedirect('/'+username+'/snippetbook/notes/') 
        else:
            pass
            # Return a 'disabled account' error message
    else:
        messages.error(request, "Username or password is not correct. Please enter again!")
        return HttpResponseRedirect('/login/') 



from notebook.newuser import create_member, create_db
#So far, this is to let existing users to register others
#just me for the time being TODO:
@user_passes_test(lambda u: u.username=='leon')
@login_required
def register_user(request): 
    if request.method == 'POST':         
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        #f = UserCreationForm(request.POST)
#        if f.errors:
#            log.debug('Registrtion form errors:'+str(f.errors))
#            return render_to_response('registration/register.html', {'form':f}) 
        #f.save()
        #TODO: might subclass UserCreationForm to save to member 
        
        #TODO: validate email
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already used by someone else. Please pick another one.")  
            return HttpResponseRedirect('/registre/')          
        if password1 == password2:        
            m, created = create_member(username, email, password1)
            if created:
                create_db(username)
                #automatically add the invited person to the inviter's friends        
                #notebook.social.views.add_friend(request, username)
                m1 = request.user.member
                m2 = Member.objects.get(username=username)         
                fr = Friend_Rel(friend1=m1, friend2=m2)
                #So far, make it confirmed automcatically. TODO:
                fr.comfirmed = True
                fr.save()
                messages.success(request, "New member created and added as your friend!")  
                return HttpResponseRedirect('/registre/') 
            else:
                messages.error(request, "Error creating a member!")  
                return HttpResponseRedirect('/registre/')   
        messages.error(request, "Passwords don't match!")
        return HttpResponseRedirect('/registre/')               
    else:     
        #registerForm = UserCreationForm()
        #registerForm = RegistrationForm()
        return render_to_response('registration/register.html', {}, context_instance=RequestContext(request)) 
       
       

@login_required
def root(request):
    user = request.user
    username = user.username
    return HttpResponseRedirect('/'+username+'/snippetbook/notes/') 

#TODO: verify if notes of private tags are excluded
def get_public_notes(note_list):    
    note_list = note_list.filter(private=False)
    n_list = remove_private_tag_notes(note_list)
    return n_list

#TODO: not working?
def remove_private_tag_notes(note_list):
    log.debug('removing notes having private tags.')
    note_list = note_list.distinct()
    log.debug('initial length of note_list:'+str(len(note_list)))
    q = ~Q(tags__private=True)
    n_list = note_list.filter(q).distinct()    
    log.debug('after filtering, length of note_list:'+str(len(n_list)))
    return n_list

#TODO: also hide notes linked that are private
def get_public_linkages(linkage_list):
    linkage_list = linkage_list.filter(private=False)
    l_list = remove_private_tag_notes(linkage_list)
    return l_list 

def get_public_tags(tags):
    return tags.filter(private=False)

#TODO:
#def get_public_folder(note_list):
#    return Folder.objects.filter(private=False)




    
    

book_model_dict = {'notebook':Note, 'snippetbook':Snippet,'bookmarkbook':Bookmark, 'scrapbook': Scrap}
book_folder_dict = {'notebook':Folder, 'snippetbook':notebook.snippets.models.Snippet_Folder,'bookmarkbook':notebook.bookmarks.models.Bookmark_Folder, 'scrapbook': notebook.scraps.models.Scrap_Folder}
book_cache_dict = {'notebook':notebook.notes.models.Cache, 'snippetbook':notebook.snippets.models.Snippet_Cache,'bookmarkbook':notebook.bookmarks.models.Bookmark_Cache, 'scrapbook': notebook.scraps.models.Scrap_Cache}
book_entry_dict = {'notebook':'', 'snippetbook':'__snippet','bookmarkbook':'__bookmark', 'scrapbook': '__scrap'}
search_fields_dict = {'notebook':('title','desc'), 'snippetbook':('title','desc'), 'bookmarkbook':('title','desc', 'url'), 'scrapbook':('title','desc', 'url')}

def getNote(username, bookname):
    return create_model("Note_"+str(bookname)+"_"+str(username), book_model_dict.get(bookname), username) 

def getFolder(username, bookname):
    return create_model("Folder_"+str(bookname)+"_"+str(username), book_folder_dict.get(bookname), username) 

def getCache(username, bookname):
    return create_model("Cache_"+str(bookname)+"_"+str(username), book_cache_dict.get(bookname), username)     


#TODO: add date range search, votes search
@login_required
def index(request, username, bookname):         
    N = getNote(username, bookname)
    connection.queries = []
    
    note_list = N.objects.all()  
    
    if request.user.username != username:
        log.info('Not the owner of the notes requested, getting public notes only...')
        note_list = get_public_notes(note_list)

    qstr = __getQStr(request)
    
    note_list  = getSearchResults(note_list, qstr, search_fields_dict.get(bookname))
    #TODO: use regex, also T and Tag
    
    
    T = getT(username)
    default_tag_id = T.objects.get(name='untagged').id    
    context = __get_context(request, note_list, default_tag_id, username, bookname)
    
    folders = context.get('folders') #TODO: if folders is empty
    folder_values, is_in_folders, current_folder = __get_folder_context(folders, qstr)
    
    queries = connection.queries
    
    extra_context = {'qstr':qstr,'folder_values':folder_values, 'is_in_folders':is_in_folders, 'current_folder':current_folder, 'aspect_name':'notes', 'queries':queries}    
    context.update(extra_context)  
    
    book_template_dict = {'notebook':'notes/notes.html', 'snippetbook':'snippetbook/notes/notes.html','bookmarkbook':'bookmarkbook/notes/notes.html', 'scrapbook': 'scrapbook/notes/notes.html'}
    
    return render_to_response(book_template_dict.get(bookname), context, context_instance=RequestContext(request,{'bookname': bookname}))


def  __getQStr(request):
    rawqstr = request.GET.get('q')    
    if rawqstr:
        qstr = rawqstr.lstrip().rstrip()
    else: qstr = None
    return qstr


#TODO: wild card
#TODO: one tag only search (not having other tags)
def getSearchResults(root_note_list, qstr, search_fields = ('title','desc')):     
    note_list = root_note_list
    #TODO: so far, not supporting mixed text search and tag search
    if qstr and (qstr.startswith('t:') or qstr.startswith('v:') or  qstr.startswith('~')): 	         
        oper_list = re.findall(r'&|\|', qstr)
        term_list = re.split(r'&|\|',qstr)
        log.debug(['oper_list:',oper_list])
        log.debug(['term_list:',term_list])       
        #for term in term_list for oper in oper_list:
        first_term =  term_list[0].split(":")
        t1 = first_term[1].strip()
        
        prefix =  first_term[0].strip()	
        
        #TODO:so this require no space between oper and the vote, e.g. ' >5' is ok, but ' > 5' is not ok.
        #it also assume vote is only one digit. Change all these.
        if (prefix.find('v') != -1):
            #TODO: probably use regex to deal with more cases, also whitespaces
            votes = int(t1[1])            
            if t1[0] == '>':                 
                q1 = Q(vote__gt = votes)
            if  t1[0] == '<': 
                q1 = Q(vote__lt = votes)
            if  t1[0] == '=': 
                q1 = Q(vote = votes)    
        else:
            q1 = Q(tags__name = t1)
        if prefix.startswith('~'):
            q1 = ~q1
        note_list = root_note_list.filter(q1) 
        
        for i in range(len(oper_list)):	    
            term = term_list[i+1].split(":")
            t2 = term[1].strip()	
            prefix = term[0].strip()            
            
            if (prefix.find('v') != -1): #TODO: DRY, refactor
                #TODO: probably use regex to deal with more cases, also whitespaces
                votes = int(t2[1])                
                if t2[0] == '>':                     
                    q2 = Q(vote__gt = votes)
                if  t2[0] == '<': 
                    q2 = Q(vote__lt = votes)
                if  t2[0] == '=': 
                    q2 = Q(vote = votes)    	    
            else:
                q2 = Q(tags__name=t2)
            if prefix.startswith('~'):
                q2 = ~q2 
            oper = oper_list[i].strip()
            
            if oper=='&':
                log.debug( '& operation')		
                note_list = note_list.filter(q2)		
              
            elif oper=='|':
                log.debug( '| operation' )
                theother_note_list = root_note_list.filter(q2)
                note_list = note_list | theother_note_list	
                
                 
    elif qstr: #TODO: for text search, not support exclude (~) so far
        #TODO: simple text search so far, no | and others  

        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        query = qstr.strip()  
        log.debug( 'query is:'+ query)
        
        note_list = root_note_list
        if search_fields and query:
            for bit in query.split():
                log.debug( 'bit:'+bit)     
                or_queries = [Q(**{construct_search(str(field_name)): bit}) for field_name in search_fields]
                #log.debug( 'or_queries:'+or_queries	)
                note_list = note_list.filter(reduce(operator.or_, or_queries))
            #~ for field_name in search_fields:
                #~ if '__' in field_name: #?
                    #~ note_list = note_list.distinct()
                    #~ break
 
    #~ else:
        #~ note_list = Note.objects.filter(delete=False) 	    
    
    return note_list.distinct()




@login_required
def get_ws_tags(request, username, bookname):
    
    ws = request.POST.get('ws')
    if ws:
        request.session["current_ws"] = ws    
    
    tags = __get_ws_tags_for_menu(request, username, bookname)    
    #from django.core import serializers
    #json_serializer = serializers.get_serializer("json")()
    #response = HttpResponse(mimetype="application/json")
    #json_serializer.serialize(tags_qs,fields=('id', 'name'), ensure_ascii=False, stream=response)
    
    
    #tags = serializers.serialize('json',tags_qs)
    
    return HttpResponse(simplejson.dumps(tags), "application/json")
    #return HttpResponse(tags) #response



#TODO: merge with the other two
#TODO: problem when viewing other people's notes since other people might not have the same working set as the
#working set in your current session. 
#On the web interface, you can pick the other person's working set.
@login_required
def __get_ws_tags_for_menu(request, username, bookname):
    """get tags for the current working set. If no current working set or if it is either bookmarks or scrapbook or snippetbook, 
    then set it as the bookname. 
    """
    #Don't use the custom model, it seems that it cannot be correctly serialize (fields are empty objects) . Might because it is proxy.TODO:
    #T = getT(username)    
    #W = getW(username)  
    print 'getting current working set, current_ws is:', request.session.get("current_ws") 
    if not request.session.get("current_ws") or request.session.get("current_ws") in books:
        request.session["current_ws"] = bookname                 
    current_ws = request.session.get("current_ws")    
    print 'current_ws is:', current_ws
    if current_ws == 'all tags' or current_ws == 'notebook':
        #this annotate get all the note's count instead of just the bookname's 
        tags_qs = Tag.objects.using(username).all().order_by('name')#.annotate(Count('note'+book_entry_dict.get(bookname))).order_by('name') 
    else:
        print 'get tags of a working set'
        w = WorkingSet.objects.using(username).get(name__exact = current_ws)
        #tags = w.tags.using(username).all().order_by('name')
        tags_qs = Tag.objects.using(username).filter(workingset=w).order_by('name')#.annotate(Count('note'+book_entry_dict.get(bookname))).order_by('name')
        
    tags = []
    N = getNote(username, bookname)
    
    for tag in tags_qs:
        count = N.objects.filter(tags=tag).count()
        t = {'name':tag.name, 'private':tag.private, 'note_count':count}
        tags.append(t)
    #print 'tags', tags
    return tags   


@login_required
def __get_ws_tags(request, username, bookname):
    """get tags for the current working set. If no current working set or if it is either bookmarks or scrapbook or snippetbook, 
    then set it as the bookname. 
    """
    #Don't use the custom model, it seems that it cannot be correctly serialize (fields are empty objects) . Might because it is proxy.TODO:
    #T = getT(username)    
    #W = getW(username)  
    print 'getting current working set, current_ws is:', request.session.get("current_ws") 
    if not request.session.get("current_ws") or request.session.get("current_ws") in books:
        request.session["current_ws"] = bookname                 
    current_ws = request.session.get("current_ws")    
    print 'current_ws is:', current_ws
    if current_ws == 'all tags' or current_ws == 'notebook':
        #this annotate get all the note's count instead of just the bookname's 
        tags_qs = Tag.objects.using(username).all().order_by('name')#.annotate(Count('note'+book_entry_dict.get(bookname))).order_by('name') 
    else:
        print 'get tags of a working set'
        w = WorkingSet.objects.using(username).get(name__exact = current_ws)
        #tags = w.tags.using(username).all().order_by('name')
        tags_qs = Tag.objects.using(username).filter(workingset=w).order_by('name')#.annotate(Count('note'+book_entry_dict.get(bookname))).order_by('name')
        
    
    return tags_qs  


def __get_view_theme(request):    
    view_mode = request.GET.get('view_mode')    
    if view_mode:
        request.session['view_mode'] = view_mode
    else:
        view_mode = request.session.get('view_mode','desc')           	   
    sort = request.GET.get('sort')	
    if sort:
        request.session['sort'] = sort
    else:
        sort = request.session.get('sort','init_date')	 
    
    delete = request.GET.get('delete')	
    if delete:
        request.session['delete'] = delete
    else:
        delete = request.session.get('delete', 'False')	 
        
    private = request.GET.get('private')	
    if private:
        request.session['private'] = private
    else:
        private = request.session.get('private', 'All')	   

    #TODO: make it possible to pick any date by giving something like /2010/8/8 in the url  
    #or pick any period of time 

    date_range = request.GET.get('date_range')
    if date_range:
        request.session['date_range'] = date_range
    else:
        date_range = request.session.get('date_range', 'All')     
    
    in_linkage = request.GET.get('in_linkage')    
    if in_linkage:
        request.session['in_linkage'] = in_linkage
    else:
        in_linkage = request.session.get('in_linkage', 'All')     
    
    with_attachment = request.GET.get('with_attachment')    
    if with_attachment:
        request.session['with_attachment'] = with_attachment
    else:
        with_attachment = request.session.get('with_attachment', 'All')     
    
    #return dict(view_mode=view_mode, sort=sort, delete=delete, private=private, month=month, year=year, day=day, week=week)	   
    return dict(view_mode=view_mode, sort=sort, delete=delete, private=private, date_range=date_range, in_linkage=in_linkage, with_attachment=with_attachment)


#TODO:refactor similar code as in index method into another method
#TODO: change aspect_name to another name to reduce confusion
@login_required
def tags(request, username, bookname, tag_name, aspect_name):     
    log.debug('requesting notes of tag:'+tag_name)	
    N = getNote(username, bookname)

    T = getT(username)
    if tag_name: #TODO: if not tag_name
        t = T.objects.get(name=tag_name)       
        if aspect_name=='notes':
            #n_list = t.note_set
            n_list = N.objects.filter(tags__name=tag_name)
        else:
            n_list = t.linkagenote_set
        
        if request.user.username != username:
            log.info('Not the owner of the notes requested, getting public notes only...')            
            note_list = remove_private_tag_notes(n_list.filter(private=False))           
        else:
            note_list = n_list           
        
        default_tag_id = t.id   
        context = __get_context(request, note_list, default_tag_id, username, bookname, aspect_name)   
        queries = connection.queries	
        extra_context = {'current_tag':tag_name, 'aspect_name':aspect_name, 'queries':queries}
        context.update(extra_context)
        
       
        book_template_dict = {'notebook':'notes/notes.html', 'snippetbook':'snippetbook/notes/notes.html','bookmarkbook':'bookmarkbook/notes/notes.html', 'scrapbook': 'scrapbook/notes/notes.html'}
        book_template_linkage_dict = {'notebook':'notes/linkages.html', 'snippetbook':'notes/linkages.html','bookmarkbook':'bookmarkbook/notes/linkages.html', 'scrapbook': 'scrapbook/notes/linkages.html'}
        
    
        if aspect_name=='notes':
            return render_to_response(book_template_dict.get(bookname), context, context_instance=RequestContext(request,{'bookname': bookname, 'advanced': get_advanced_setting(request)}))
        else:
            return render_to_response(book_template_dict.get(bookname), context, context_instance=RequestContext(request,{'bookname': bookname, 'advanced': get_advanced_setting(request)}))


def get_advanced_setting(request):
    advanced = request.GET.get('advanced')    
    if advanced:
        request.session['advanced'] = advanced
    else:
        advanced = request.session.get('advanced','off')     
    return advanced
        


#~ def deleted(request, note_set, delete=False):
    #~ note_list = note_set.filter(delete=delete)
    #~ return note_list   
    

#get notes of any week of the current month
def week(request):
    pass

#get notes of any month of the current year    
def month(request):
    pass
    
def season(request):
    pass     

def year(request):
    pass     


@login_required
def caches(request, cache_id, username, bookname):    
    note_ids = __get_cache(request, cache_id, username, bookname)
    
    if note_ids:
        note_ids_list =note_ids.split(',')
        note_list = __get_notes_by_ids(note_ids_list, username, bookname)
    else:
        note_list = __get_notes_by_ids([], username, bookname)
    
    T = getT(username)
    default_tag_id = T.objects.get(name='untagged').id    
    context = __get_context(request, note_list, default_tag_id, username, bookname)	
    return render_to_response('notes/note_list.html', context, context_instance=RequestContext(request,{'bookname': bookname, 'aspect_name':'notes'}))



def __get_context(request, note_list,default_tag_id, username, bookname, aspect_name='notes'):  
    theme = __get_view_theme(request)
    in_linkage = theme['in_linkage']
    if in_linkage in ['All', 'all']:
        pass
    elif in_linkage in true_words:
        note_list = note_list.filter(linkagenote__isnull=False)
      
    view_mode, sort, delete, private, date_range, order_type, with_attachment, paged_notes,  cl = __get_notes_context(request, note_list)    
   
    addnote_mode = request.session.get('addnote_mode', 'on')
    show_notes_mode = request.session.get('show_notes_mode', 'on')    
    show_caches_mode = request.session.get('show_caches_mode', 'on')    
    
    folders, caches, next_cache_id = __get_menu_context(request, username, bookname)
    
    now = date.today()
    
    tags = __get_ws_tags(request, username, bookname)
    
    W = getW(username)
    #TODO: get private ones
    wss = W.objects.all()
  
    if request.user.username != username:
        print 'get public tags...'
        tags = get_public_tags(tags)          
    
    #AddNForm_notes = create_model_form("AddNForm_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=tags)})
    #addNoteForm = AddNForm_notes(initial={'tags': [default_tag_id]}) #TODO: is this form used at all?
    return  {'note_list': paged_notes, 'tags':tags, 'view_mode':view_mode,
                   'delete':delete, 'private':private, 'day':now.day, 'month':now.month, 'year':now.year,
                   'addnote_mode':addnote_mode,'sort':sort, #'addNoteForm': addNoteForm,
		   'addLinkNoteForm':AddLinkageNoteForm(),'folders':folders, 'caches':caches, 
		   'next_cache_id':next_cache_id, 'show_notes_mode':show_notes_mode, 'show_caches_mode':show_caches_mode,'cl':cl, 
           'profile_username':username, 'date_range':date_range, 'order_type':order_type, 'in_linkage':in_linkage, 
           'with_attachment':with_attachment, 'users':User.objects.all(), 'wss':wss, 'current_ws':request.session.get("current_ws", None)}      
    




def __get_menu_context(request, username, bookname):  
    F = getFolder(username, bookname)    
    folders = F.objects.all()   
    if request.user.username != username:
        log.debug('Not the owner, getting public folders only...')      
        folders = F.objects.filter(private=False)   
       
    caches = __get_caches(request, username, bookname)
    #TODO: for note cache
    if bookname == 'notebook':
        cache_ids = caches.values_list('id', flat=True).order_by('id')
    else:     
        cache_ids = caches.values_list('cache_id', flat=True).order_by('cache_id') 
    if cache_ids.count():
        print 'cache_ids.count()', cache_ids.count()
    #TODO: ValuesListQuerySet cannot use negative index, so last filter in template doesn't work    
        next_cache_id = cache_ids[cache_ids.count()-1]+1 
    else:
        next_cache_id = 1
    return folders, caches, next_cache_id


#TODO: pass number per page
def __get_notes_context(request, note_list):
    theme = __get_view_theme(request)
    view_mode = theme['view_mode']
    order_field = theme['sort']   
    delete =    theme['delete']   
    private =    theme['private']   
    date_range = theme['date_range']
    with_attachment = theme['with_attachment']
#    month =    theme['month']  
#    year =    theme['year']
#    day =    theme['day']
#    week =    theme['week']
    
    
    if delete in true_words:
        note_list = note_list.filter(deleted=True)
    else:
        note_list = note_list.filter(deleted=False)           
    
    
    if private in ['All', 'all']:
        pass
    else:
        if private in true_words:
            note_list = note_list.filter(private=True)
        else:          
            note_list = note_list.filter(private=False)    
        
    now = date.today()
#    if month in ['All', 'all']:
#        pass
#    else:
#        note_list = note_list.filter(init_date__month=month, init_date__year= now.year) 
#    if year in ['All', 'all']:
#        pass
#    else:
#        note_list = note_list.filter(init_date__year= year) 
#    if day in ['All', 'all']:
#        pass
#    else:
#        note_list = note_list.filter(init_date__day= day, init_date__month=now.month, init_date__year= now.year)      
#    if week in ['All', 'all']:
#        pass
#    elif week=='this': #TODO:
#        one_week_ago = now - datetime.timedelta(days=7)
#        note_list = note_list.filter(init_date__gte=one_week_ago.strftime('%Y-%m-%d'),  init_date__lte=now.strftime('%Y-%m-%d 23:59:59')
#                                            )    
    if date_range in ['All', 'all']:
        pass
    elif date_range == 'today':
        note_list = note_list.filter(init_date__day= now.day, init_date__month=now.month, init_date__year= now.year) 
    elif date_range == 'past7days':
        one_week_ago = now - datetime.timedelta(days=7)
        note_list = note_list.filter(init_date__gte=one_week_ago.strftime('%Y-%m-%d'),  init_date__lte=now.strftime('%Y-%m-%d 23:59:59'))     
    elif date_range == 'this_month':
        note_list = note_list.filter(init_date__month=now.month, init_date__year= now.year) 
    elif date_range == 'this_year':  
        note_list = note_list.filter(init_date__year= now.year) 
    
        
    if with_attachment in ['All', 'all']:
        pass
    elif with_attachment in true_words:
        try:
            note_list = note_list.filter(attachment__startswith='noteattachments/') #TODO: hard coded, change
        except FieldError:
            pass  #bookmarks and scraps do not have attachment. TODO: other ways to tell if the field is there  
    
    order_type = request.GET.get('order_type','desc')  
    
    
    
    #sorting by usefulness is only valid for social_notes. TODO: refactor. At least don't mix social notes with others
#    from django.db.models.query import QuerySet
    if order_field == 'usefulness': #and isinstance(note_list, QuerySet):
        order_field = 'init_date'
    
#    sorted_note_list = note_list    
#    if order_field != 'usefulness':  
    sorted_note_list = note_list.order_by('%s%s' % ((order_type == 'desc' and '-' or ''), order_field)) 
#    else:       
#        #Social_Note has usefulness
#        sorted_notes = [(note, note.get_usefulness()) for note in note_list]   
#        sorted_notes.sort(key=lambda r: r[1],reverse = (order_type == 'desc' and True or False))  
#        sorted_note_list = [r[0] for r in sorted_notes]
   
    list_per_page = 30
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

    return view_mode, order_field, delete, private, date_range, order_type, with_attachment, paged_notes, cl
    

class Pl(object):
    def __init__(self, request):
        self.paginator = None
        self.page_num = None
        self.show_all = None
        self.can_show_all = False
        self.multi_page = None
        self.params = dict(request.GET.items())
        #self.opts = None
        self.verbose_name = _('note')
        self.verbose_name_plural = _('notes')
        
        
    def get_query_string(self, new_params=None, remove=None):
        if new_params is None: 
            new_params = {}
        if remove is None: 
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(p)


def __get_folder_context(folders, qstr):
    folder_values = folders.values_list('value', flat=True)
    #TODO: use other ways to make the following implemented more simple, for example, use a custom tag: ifin , 
    #and another custom tag or filter to find the name    
    if qstr in folder_values:
        is_in_folders = True
        current_folder = folders.get(value=qstr)
    else:
        is_in_folders = False
        current_folder = "" 
    return  folder_values, is_in_folders, current_folder   
    

#the hosting site get rid of one / if there are //, so add this method to do the redirect.
@login_required
def folders_index(request, username, bookname):
    return folders(request, username, bookname, '')    


#TODO: get the snippets' folder?
@login_required
def folders(request, username, bookname, folder_name):
    #TODO: don't  query the notes if no folder name. Also get rid of using /notes/folders// in url and use /notes/folders/
    F = getFolder(username, bookname)
    N = getNote(username, bookname)
    T = getT(username)
    note_list = N.objects.all()
    if request.user.username != username:
        log.debug( 'Not the owner of the notes requested, getting public notes only...')
        note_list = get_public_notes(note_list)    
        
    qstr = ""
    if folder_name:        
        folder = F.objects.get(name=folder_name)     
        qstr = folder.value 
        #request_path = '/'+username+'/notes/?q='+django.utils.http.urlquote_plus(qstr)        
        note_list  = getSearchResults(note_list, qstr)     
    #TODO: no need of below in folders aspect
    default_tag_id = T.objects.get(name='untagged').id    
    context = __get_context(request, note_list, default_tag_id, username, bookname)
    
    folders = context.get('folders') #TODO: if folders is empty
    folder_values, is_in_folders, current_folder = __get_folder_context(folders, qstr)
    
    extra_context = {'qstr':qstr,'folder_values':folder_values, 'is_in_folders':is_in_folders, 'current_folder':current_folder, 'aspect_name':'folders'}    
    context.update(extra_context)
    
    book_template_dict = {'notebook':'notes/folders.html', 'snippetbook':'snippetbook/notes/folders.html','bookmarkbook':'bookmarkbook/notes/folders.html', 'scrapbook': 'scrapbook/notes/folders.html'}
       
    
    return render_to_response(book_template_dict.get(bookname), context, context_instance=RequestContext(request,{'bookname': bookname,}))

  
#TODO:add protection
@login_required
def note(request, username, bookname, note_id):
    log.debug('Getting the note:'+note_id)
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    linkages = note.linkagenote_set.all()
    UpdateNForm = create_model_form("UpdateNForm_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=__get_ws_tags(request, username, bookname))})
    note_form = UpdateNForm(instance=note)
    return render_to_response('notes/note.html', {'note':note, 'linkages':linkages,'note_form':note_form, 'profile_username':username}, context_instance=RequestContext(request, {'bookname': bookname,'aspect_name':'notes'}))
    

#below is not used  
#def alltags(request, username):   
#    note_list = Note.objects.filter(delete=False).order_by('-init_date')
#    return render_to_response('notes/note_list_by_tag.html', {'note_list': note_list, 'tags':Tag.objects.all(), 
#                                                'current_tag':'','view_mode':view_mode, 'sort':sort})

@login_required
def update_note(request, note_id, username, bookname): 
    log.debug( 'updating note :'+note_id)
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)  
    #TODO: so far there are something wrong with using form. Together with update linkage, sometimes
    #it succeeds, sometime error saying tags is required field.
    
    #need to create a customized form since the field of the form will be popluated with choices based on the model
#    UpdateNForm = create_model_form("UpdateNForm", N)
#    form = UpdateNForm(request.POST, request.FILES, instance=note)
#    #TODO: validate
#    print "form.fields:", form.fields
#    print "form.errors:",form.errors
#    form.save()

    note.title = request.POST.get('title')
    note.desc = request.POST.get('desc')
    note.event = request.POST.get('event')
    note.private = request.POST.get('private', False)
    note.deleted = request.POST.get('delete', False)
    note.tags = request.POST.getlist('tags')
    #note.init_date = request.POST.get('init_date')
    note.vote = request.POST.get('vote')
    file = request.FILES.get('attachment')
    if file:
        note.attachment = file 
    note.save()    

    log.debug( 'the note %s is updated.' % (note_id))
    full_path =  request.get_full_path()  
    pre_url = full_path[:-11] #remove "addNote/"
    log.debug( 'redirect to the page that add note form is submitted from:'+pre_url)
    messages.success(request, "Note is successfully updated!") #TODO
    return HttpResponseRedirect(pre_url)   


@login_required    
def update_note_inline(request, username, bookname):    
    note_id = request.POST.get('id')
    content =  request.POST.get('content')  
    note_field = request.POST.get('note_field')  
    
    N = getNote(username, bookname)
    print 'access db 1'
    note = N.objects.get(id=note_id)
    if note_field=='note_title':
        note.title = content
    if note_field=='note_desc':
        note.desc = content
    if note_field=='note_event':
        note.event = content.lstrip("{").rstrip("}") #TODO: change Note's event to extra, the same as bookmarks and scraps
    if note_field=='note_tags':
        note.update_tags(content)    
    #note.tags = content	
    if note_field=='note_init_date':
        note.init_date = datetime.datetime.strptime(content,'%Y-%m-%d %H:%M')    
    print 'access db 6'
    note.save()
    log.debug( 'note updated')
    #TODO: if error
    return HttpResponse(content, mimetype="text/plain") 
    

@login_required   
def add_comment(request, username, bookname):  
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    content = request.POST.get('content')
    NC = getNC(username)
    nc = NC(note=note, desc=content)
    nc.save()
    return  HttpResponse(simplejson.dumps({'note_id':note_id, 'content':content}),
                                                                     "application/json")
    
    
@login_required   
def delete_comment(request, username, bookname):
    #note_id = request.POST.get('id')
    comment_id = request.POST.get('comment_id')    
    NC = getNC(username)
    nc = NC.objects.get(id=comment_id)
    nc.delete()
    return HttpResponse('successful', mimetype="text/plain")  


@login_required   
def make_private(request, username, bookname):
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    note.private = True
    note.save()
    return  HttpResponse(simplejson.dumps({'note_id':note_id, 'private':'y'}),
                                                                     "application/json")
    
@login_required   
def make_public(request, username, bookname):
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    note.private = False
    note.save()
    return  HttpResponse(simplejson.dumps({'note_id':note_id, 'private':'n'}),
                                                                     "application/json")



    
@login_required   
def vote_up_note(request, username, bookname):    
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    note.vote += 1
    
    note.save()
    return HttpResponse(note.vote, mimetype="text/plain") 
    

@login_required    
def vote_down_note(request, username, bookname):    
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    note.vote -= 1

    note.save()
    return HttpResponse(note.vote, mimetype="text/plain")    

@login_required    
def delete_note(request, username, bookname):
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    note.deleted = True    
    note.save()
    return HttpResponse(note.deleted, mimetype="text/plain")        
    

@login_required
def add_note(request, username, bookname):
    N = getNote(username, bookname)
    T = getT(username)
    #tags = T.objects.all()
    #have to add tags below specifically. Otherwise, error in db matching.
    #AddNForm = create_model_form("AddNForm_add_note_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=tags)})      
    
    post = request.POST.copy()    
    
    tags = post.getlist('tags')
    if not tags:
        tags = ['untagged']
        #post.setlist('tags', tags)
    
    n = N(desc=post.get('desc'))  
    n.vote = 0
    n.private = post.get('private', False)
    n.save()
    n.add_tags(tags, bookname)
    n.save()
    messages.success(request, "Note is successfully added!") #TODO     
    return HttpResponseRedirect(__get_pre_url(request))    
    

#TODO: other better ways of implementation
#TODO: use HttpRequest.META['HTTP_REFERER']
def __get_pre_url(request):
    full_path =  request.get_full_path() 
    s = full_path[:full_path.rfind('/')]#get rid of the last slash, assuming url always ends with a slash
    pre_url =  s[:s.rfind('/')+1]    
    #log.debug('redirect to the page that add note form is submitted from:'+str(pre_url))
    return pre_url



#TODO: method name seems to overlap with linkagenotes method
@login_required
def  link_notes(request, username, bookname):
    note_ids = request.POST.get('notes')    
    notes = note_ids.split(",")   
    notes = list(set(notes)) 
    N = getNote(username, bookname)
   
    tag_list = []
    for note_id in notes:
        n = N.objects.get(id=note_id)        
        tag_list.extend(n.get_tags_ids())    
    
    tags = list(set(tag_list))  
    
    post = request.POST.copy()   
    post.setlist('notes', notes)
    post.setlist('tags', tags)
    post['vote'] = 0 #TODO: should have the default in the model    

    L = getL(username)
    linkageNote = L()
    linkageNote.title = post.get('title')
    linkageNote.desc = post.get('desc')
    linkageNote.private = post.get('private', False)
    linkageNote.type_of_linkage = post.get('type_of_linkage')
    file = request.FILES.get('attachment')
    if file:
        linkageNote.attachment = file 
    linkageNote.save()
    linkageNote.notes = notes
    linkageNote.tags = tags    
    
#    AddLForm = create_model_form("AddLForm_"+str(username), L, options={'exclude':('tags')})
#    
#    linkageNote = AddLForm(post, request.FILES, instance=L()) 
#    print "linkageNote.is_valid():",linkageNote.is_valid()
#    print "linkageNote.errors:",linkageNote.errors 
    n = linkageNote.save()
    messages.success(request, "A linkage is successfully created!")
    return HttpResponseRedirect(__get_pre_url(request))      
    

@login_required
def linkagenotes(request, username, bookname):
    #TODO: allow filter on delete
    
    #TODO: get linkages according to bookname
    L = getL(username)
    note_list = L.objects.filter(deleted=False)
    if request.user.username != username:
        log.debug('Not the owner of the notes requested, getting public notes only...')
        note_list = get_public_linkages(note_list)        
     
    view_mode, sort,  delete, private, date_range, order_type, with_attachment, paged_notes, cl = __get_notes_context(request, note_list)  
    folders, caches, next_cache_id = __get_menu_context(request, username, bookname)
    qstr = '' #TODO: for now, no query
    now = date.today()    

    tags = __get_ws_tags(request, username, bookname)
    if request.user.username != username:
        tags = get_public_tags(tags)  
    
    return render_to_response('notes/linkages.html', {'note_list': paged_notes, 
                                                 'tags':tags, 'view_mode':view_mode, 
                                                 'sort':sort, 'delete':delete, 'private':private, 'day':now.day, 'month':now.month, 'year':now.year, 'cl':cl,
                                                 'folders':folders,'qstr':qstr, 'profile_username':username, 'aspect_name':'linkagenotes', 'date_range':date_range, 
                                                 'order_type':order_type, 'with_attachment':with_attachment, 'users':User.objects.all(), 
                                                 'current_ws':request.session.get("current_ws", None),'included_aspect_name':'notes'},
                                                  context_instance=RequestContext(request,{'bookname': bookname,}))


@login_required
def linkagenote(request, note_id, username, bookname):    
    L = getL(username)
    note = L.objects.get(id=note_id)
    linkage_form = UpdateLinkageNoteForm(instance=note)
    return render_to_response('notes/linkagenote.html', {'note':note, 'linkage_form':linkage_form, 'profile_username':username}, context_instance=RequestContext(request,{'bookname': bookname,}))


@login_required
def update_linkagenote(request, note_id, username, bookname):
    L = getL(username)
    note = L.objects.get(id=note_id)
    
    #TODO: the same as in update_note, using the form will cuase a wierd error
#    UpdateLForm = create_model_form("UpdateLForm_"+str(username), L, options={'exclude':('tags', 'notes')})
#    linkage_form = UpdateLForm(request.POST, request.FILES, instance=note)
#    print "linkage_form.errors:",linkage_form.errors
#    #TODO: validate
#    print "linkage_form.fields:", linkage_form.fields
#    linkage_form.save()
    
    
    note.type_of_linkage = request.POST.get('type_of_linkage')
    note.title = request.POST.get('title')
    note.desc = request.POST.get('desc')
    #note.notes = request.POST.getlist('notes')
    note.private = request.POST.get('private', False)
    note.deleted = request.POST.get('delete', False)
    #note.tags = request.POST.getlist('tags')    
    note.vote = request.POST.get('vote')
    note.attachment = request.FILES.get('attachment')
    note.save() 
    
    log.debug( 'the linkagenote %s is updated.' % (note_id))   
    messages.success(request, "Linkage is successfully updated!") #TODO     
    return HttpResponseRedirect(__get_pre_url(request))    


@login_required
def update_linkage_note_inline(request, username, bookname):    
    note_id = request.POST.get('note_id')
    content =  request.POST.get('content')  
    note_field = request.POST.get('note_field')  
    
    L = getL(username)
    note = L.objects.get(id=note_id)
    if note_field=='note_title':
        note.title = content
    if note_field=='note_desc':
        note.desc = content
    if note_field=='note_type_of_linkage':
        note.type_of_linkage = content
#    if note_field=='note_tags':
#        note.update_tags(content)   	
    if note_field=='note_init_date':
        note.init_date = datetime.datetime.strptime(content,'%Y-%m-%d %H:%M')    
    if note_field=='note_add_notes':
        note.add_notes(content) 	    
    note.save()
    log.debug('linkagenote updated')
    #TODO: if error
    return HttpResponse(content, mimetype="text/plain") 

#TODO: for all these delete and update things, check the rights first. (might use django's permission management system)
@login_required
def delete_linkage(request, username, bookname):    
    note_id = request.POST.get('linkage_id')
    L = getL(username)
    note = L.objects.get(id=note_id)
    note.deleted = True    
    note.save()
    return HttpResponse(note.deleted, mimetype="text/plain")      

@login_required
def delete_note_from_linkage(request, username, bookname):    
    linkage_id = request.POST.get('linkage_id')
    log.debug( 'linkage is:'+str(linkage_id))
    L = getL(username)
    linkage = L.objects.get(id=linkage_id)
    note_id = request.POST.get('note_id')
    log.debug('note to be deleted from the linkage:'+note_id)
    linkage.remove_note(note_id)    
    linkage.save()
    return HttpResponse('note deleted', mimetype="text/plain")  

@login_required    
def toggle_add_note_mode(request):
    addnote_mode = request.POST.get('addnote_mode')    
    request.session['addnote_mode'] = addnote_mode
    return HttpResponse(addnote_mode, mimetype="text/plain") 

@login_required    
def toggle_show_notes_mode(request):
    show_notes_mode = request.POST.get('show_notes_mode')    
    request.session['show_notes_mode'] = show_notes_mode
    return HttpResponse(show_notes_mode, mimetype="text/plain")   

@login_required
def  toggle_show_caches_mode(request):
    show_caches_mode = request.POST.get('show_caches_mode')    
    request.session['show_caches_mode'] = show_caches_mode
    return HttpResponse(show_caches_mode, mimetype="text/plain")  
   
@login_required    
def add_tags_to_notes(request, username, bookname):
    log.debug('add_tags_to_notes')
    note_ids= request.GET.getlist('note_ids')[0].split(',')    
    log.debug( 'Adding tags to the following notes:'+str(note_ids))
    tags_to_add = request.GET.getlist('tags_to_add')[0].split(',')
    log.debug( 'The following tags are going to added:'+str(tags_to_add))	
    N = getNote(username, bookname)
    T = getT(username)
    for note_id in note_ids:
        note = N.objects.get(id=note_id)
        log.debug('got the note')
        for tag_id in tags_to_add:
            log.debug('adding a tag')
            t = T.objects.get(id=tag_id) 
            log.debug('got the tag')
            note.tags.add(t)
            log.debug('note of '+str(note_id)+' is added with tag id '+str(tag_id))
            note.save()      
    log.debug('tag added') 
    return HttpResponse('success', mimetype="text/plain") 
    


@login_required    
def add_tags_to_notes2(request, username, bookname):
    log.debug('add_tags_to_notes2')
    note_ids= request.GET.getlist('note_ids')[0].split(',')    
    log.debug( 'Adding tags to the following notes:'+str(note_ids))
    tags_to_add = request.GET.getlist('tags_to_add')[0].split(',')
    log.debug( 'The following tags are going to added:'+str(tags_to_add))    
    N = getNote(username, bookname)    
     
    for note_id in note_ids:
        note = N.objects.get(id=note_id)
        note.add_tags(tags_to_add, bookname)
        
        
    log.debug('tag added') 
    return HttpResponse('success', mimetype="text/plain") 


@login_required    
def update_tags(request, username):
    pass
    



#def share_note(note_id, username):
#    N = getN(username)
#    note = N.objects.get(id=note_id)
#    #sendEmail(u'yuanliangliu@gmail.com', [u'buzz@gmail.com'], note.desc.encode('utf8'), u'')
#    send_mail(note.desc.encode('utf8'), u'', u'yuanliangliu@gmail.com', [u'buzz@gmail.com'])
#    

#from email.MIMEText import MIMEText
#import smtplib

#mailserver = smtplib.SMTP('smtp.googlemail.com')
#    
#mailserver.set_debuglevel(1)
#mailserver.ehlo()
#mailserver.starttls()    
#mailserver.login('', '')

#mailserver.close() #TODO: gc



#def sendEmail(fromAddr, toAddrList, subject, content):
#    print 'sending email...'
#    msg = MIMEText(content)
#    msg['Subject'] = subject
#    msg['From'] = fromAddr
#    msg['To'] = toAddrList[0]
#    mailserver.sendmail(fromAddr, toAddrList, msg.as_string())   
#    print 'email sent!'
    

#TODO: private notes cannot be shared. Might implement the permission control at a finer level
@login_required
def share(request, username, bookname): 
    print 'share in note called'   
    note_ids = request.POST.getlist('note_ids')   
    N = getNote(username, bookname)
    msgs = [] 
    for note_id in note_ids:         
        note = N.objects.get(id=note_id)  
        msg = (('From osl '+bookname+': '+note.title +' '+note.desc).encode('utf8'), '', 'yejia2000@gmail.com', ['buzz@gmail.com'])   
        msgs.append(msg)         
        #share_note(note_id, username)
    send_mass_mail(tuple(msgs), fail_silently=False) 
    return HttpResponse('success', mimetype="text/plain")     

    
#TODO: possibly use these below as actions that is used to group update the private field of notes  
@login_required
def set_notes_private(request, username, bookname):     
    note_ids = request.POST.getlist('note_ids')    
    N = getNote(username, bookname)
    notes = N.objects.filter(id__in=note_ids)
    notes.update(private = True)
    return HttpResponse('success', mimetype="text/plain") 

@login_required
def set_notes_public(request, username, bookname): 
    note_ids = request.POST.getlist('note_ids')   
    N = getNote(username, bookname)
    notes = N.objects.filter(id__in=note_ids)
    notes.update(private = False)
    return HttpResponse('success', mimetype="text/plain")

@login_required    
def set_notes_delete(request, username, bookname):
    note_ids = []    
    N = getNote(username, bookname)
    notes = N.objects.filter(id_in=note_ids)
    notes.update(deleted = True)

@login_required
def remove_notes_delete(request, username, bookname):
    note_ids = []    
    N = getNote(username, bookname)
    notes = N.objects.filter(id_in=note_ids)
    notes.update(deleted = False)    

@login_required 
def discard_notes(request, username, bookname):
    note_ids = []    
    N = getNote(username, bookname)
    notes = N.objects.filter(id_in=note_ids)
    notes.delete()

#@login_required    
#def add_extra_to_notes(request, username):
#    note_ids = []    
#    N = getN(username)
#    notes = N.objects.filter(id_in=note_ids)
#    extra = ''    
#    notes.update(event=F('event')+extra)   

@login_required
def update_notes_init_date(request, username, bookname):
    note_ids = []    
    N = getNote(username, bookname)
    notes = N.objects.filter(id_in=note_ids)
    init_date = ''    
    notes.update(init_date=init_date)       

#@login_required    
#def remove_tags_from_notes(request, username, bookname):
#    note_ids= request.GET.getlist('note_ids')[0].split(',')    
#    log.debug( 'Removing tags to the following notes:'+str(note_ids))
#    tags_to_add = request.GET.getlist('tags_to_add')[0].split(',')
#    log.debug( 'The following tags are going to removed:'+str(tags_to_add))	
#    N = getNote(username, bookname)
#    T = getT(username)
#    for note_id in note_ids:
#        note = N.objects.get(id=note_id)
#        for tag_id in tags_to_add:	
#            t = T.objects.get(id=tag_id) 
#            note.tags.remove(t)
#            note.save()    
#    return HttpResponse('success', mimetype="text/plain") 


@login_required    
def remove_tags_from_notes2(request, username, bookname):
    note_ids= request.GET.getlist('note_ids')[0].split(',')    
    log.debug( 'Removing tags to the following notes:'+str(note_ids))
    tags_to_remove = request.GET.getlist('tags_to_add')[0].split(',')
    log.debug( 'The following tags are going to removed:'+str(tags_to_remove))    
    N = getNote(username, bookname)
    T = getT(username)
    for note_id in note_ids:
        note = N.objects.get(id=note_id)
        note.remove_tags(tags_to_remove)   
    return HttpResponse('success', mimetype="text/plain") 
    

#TODO: get the folder of the snippets
@login_required    
def save_search(request, username, bookname):	    
    folder_value = request.POST.get('folder_value')
    log.debug( 'Saving the following query as a folder:'+folder_value)
    folder_name= request.POST.get('folder_name')
    log.debug( 'The folder is going to be named as:'+folder_name)
    F = getFolder(username, bookname)
    folder = F(name=folder_name, value=folder_value) 
    folder.save()
    return HttpResponseRedirect(__get_pre_url(request))      
    



#TODO: code below may have a problem for working for view notes (instead of snippets/bookmarks/scraps) caches, since notes cache has no cache_id
#  because cache's diplaying in html is via cache_id for each book. So this part is different from snippets/bookmarks/scraps and folders. Might think
#  whether to make them the same.
def __get_caches(request, username, bookname):
    C = getCache(username, bookname)
    caches = C.objects.all()    
    return caches

def __get_cache(request,cache_id, username, bookname):    
    log.debug( 'cache id requested is:'+cache_id)
    C = getCache(username, bookname)
    try:
        if bookname == 'notebook':
            cache = C.objects.get(id=cache_id)
        else:    
            cache = C.objects.get(cache_id=cache_id)
    except ObjectDoesNotExist:
        return "" #TODO
    log.debug( 'cache:'+str(cache))
    return cache.note_ids



#TODO: bookname??

#TODO: whether I can use SSI to do this? 
@login_required
def get_cache(request, username, bookname, cache_id):
    return HttpResponse(__get_cache(request, cache_id, username, bookname), mimetype="text/plain") 


#def compute_parent_cache_id(child_cache_id, username, bookname):
#    C = getCache(username, bookname)
#    parent_cache_id = C.objects.all()[child_cache_id].cache_ptr_id
#    return parent_cache_id
    
    

@login_required
def add_notes_to_cache(request,username, bookname, cache_id):
    note_ids= request.POST.getlist('selected_note_ids')
    log.debug( 'selected_note_ids is:'+str(note_ids))    
    cache_id= request.POST.get('cache_id')    
    C = getCache(username, bookname)
#    if cache_id > C.objects.all().count():
#        #create a new cache
#        cache = C() 
#        created = True       
#    else:
#        parent_cache_id = C.objects.all()[cache_id].cache_ptr_id
#        cache = C.objects.get(cache_ptr_id=parent_cache_id)
#        created = False
            
    #parent_cache_id = compute_parent_cache_id(cache_id, username, bookname)
    
    if bookname == 'notebook':
        cache, created = C.objects.get_or_create(id=cache_id)
    else:  
        cache, created = C.objects.get_or_create(cache_id=cache_id)
    
    cached_note_ids = cache.note_ids
    log.debug( 'cached_note_ids:'+str(cached_note_ids))
    if not cached_note_ids:
        cached_note_ids_list = []
    else:	
        cached_note_ids_list = cached_note_ids.split(',')
    cached_note_ids_list.extend(note_ids)	
    cached_note_ids_list = list(set(cached_note_ids_list))
    cached_note_ids_list.sort();
    log.debug( 'updated_cached_note_ids:'+str(cached_note_ids_list))   
    cache.note_ids = ','.join(cached_note_ids_list)
    cache.save()
    return  HttpResponse(simplejson.dumps({'cache_id':cache.cache_id, 'note_ids':cache.note_ids,'created':created}),
                                                                     "application/json")

@login_required
def clear_cache(request, username, bookname, cache_id):
    C = getCache(username, bookname)
    if bookname == 'notebook':
        cache = C.objects.get(id=cache_id)
    else:
        cache = C.objects.get(cache_id=cache_id)
    cache.delete() #TODO: below doesn't delete the entry in the parent Cache
    return  HttpResponse(cache_id, "text/plain")
    
    
def __get_notes_by_ids(id_list, username, bookname):
    N = getNote(username, bookname)
    return N.objects.filter(id__in=id_list)

@login_required
def settings(request):    
    return render_to_response('settings/index.html', {'profileForm':ProfileForm(instance=request.user.member)}, context_instance=RequestContext(request))


@login_required
def settings_update_profile(request):  
    m = request.user.member
    #TODO: display current avatar in the template, and allow user to upload another avatar
    avatar = request.FILES.get('icon')
    if avatar:
        m.icon = avatar
    m.first_name = request.POST.get('first_name')
    m.last_name = request.POST.get('last_name')
    m.email = request.POST.get('email')
    m.nickname = request.POST.get('nickname')
    m.gender = request.POST.get('gender')
    m.save()
    #
    #f = ProfileForm(request.POST, request.FILES, instance=m)          
    #log.debug('ProfileForm form errors:'+str(f.errors))
    #f.save() 
    return HttpResponseRedirect(__get_pre_url(request)) 



@login_required
def settings_tags(request):
    username = request.user.username
    T = getT(username)  
    tags = T.objects.all().order_by('name')
    W = getW(username)
    wss = W.objects.all().order_by('name')
    return render_to_response('tags/index.html', {'wss':wss, 'tags':tags, 'addTagForm':AddTagForm()}, context_instance=RequestContext(request))


@login_required
def update_tag_name(request):
    username = request.user.username
    T = getT(username)
    id = request.POST.get('id')
    name = request.POST.get('name')
    tag = T.objects.get(id=id)  
    tag.name = name 
    tag.save()
    return HttpResponse(name, mimetype="text/plain")

@login_required   
def delete_tag(request):
    username = request.user.username
    T = getT(username)
    id = request.POST.get('id')    
    tag = T.objects.get(id=id)   
    tag.delete()
    return HttpResponse("Tag successfully deleted.", mimetype="text/plain")

@login_required    
def settings_tag(request, tag_name):
    username = request.user.username
    T = getT(username)    
    tag = T.objects.get(name__exact=tag_name) 
    tag_form = UpdateTagForm(instance=tag)
    return render_to_response('tags/tag.html',  {'tag':tag, 'tag_form':tag_form}, context_instance=RequestContext(request)) 

@login_required
def settings_tag_add(request):    
    username = request.user.username
    T = getT(username)    
    post = request.POST.copy()
    f = AddTagForm(post, request.FILES, instance=T())    
    log.debug('form errors:'+str(f.errors))
    f.save() 
    messages.success(request, "Tag is successfully added!") #TODO    
    return HttpResponseRedirect(__get_pre_url(request))       

#TODO: what to do if the new tag name is one existing tag's name? Should we get that existing tag,
#and update all stuff (notes, bookmarks, scraps) using this tag with that tag? Or should the user remove 
#that tag from all stuff first, then add the new tag to the stuff and remove the old tag from tags setting? 
@login_required
def settings_tag_update(request, tag_name): 
    username = request.user.username
    T = getT(username)
    tag = T.objects.get(name__exact=tag_name) 
    tag_form = UpdateTagForm(request.POST, instance=tag)
    tag_form.save()   
    messages.success(request, "Tag is successfully updated!") 
    #TODO: might be better to return to the changed tag page (url changed to the new tag name)
    return HttpResponseRedirect('/'+username+'/settings/tags/')   


#@login_required
#def settings_add_tags_2_wss(request):
#    username = request.user.username
#    tag_ids= request.POST.getlist('tag_ids')
#    
#    log.debug( 'Adding the following tags to wss:'+str(tag_ids))
#    wss = request.POST.getlist('wss')
#    log.debug('The following wss are going to be added to:'+str(wss))    
#    W = getW(username)
#    T = getT(username)
#    for ws_id in wss:
#        ws = W.objects.get(id=ws_id)
#        for tag_id in tag_ids:
#            t = T.objects.get(id=tag_id) 
#            ws.tags.add(t)
#            ws.save()    
#            print t, 'is added to ', ws
#    
#    messages.success(request, "The folloing tags were successfully added to these working sets")     
#    return HttpResponse('success', mimetype="text/plain") 



#TODO: shouldn't be get since it change data
@login_required
def settings_add_tags_2_wss2(request):
    username = request.user.username
    tag_names= request.GET.getlist('tags_to_add')[0].split(',')
    
    log.debug( 'Adding the following tags to wss:'+str(tag_names))
    wss = request.GET.getlist('wss')[0].split(',')
    log.debug('The following wss are going to be added to:'+str(wss))    
    W = getW(username)
    T = getT(username)
    for ws_id in wss:
        ws = W.objects.get(id=ws_id)
        for tag_name in tag_names:
            t = T.objects.get(name=tag_name) 
            ws.tags.add(t)
            ws.save()    
            print t, 'is added to ', ws
    
    messages.success(request, "The folloing tags were successfully added to these working sets")     
    return HttpResponse('success', mimetype="text/plain") 



@login_required
def settings_remove_tags_from_wss2(request):
    username = request.user.username
    tag_names= request.GET.getlist('tags_to_add')[0].split(',')
    
    log.debug( 'Removing the following tags from wss:'+str(tag_names))
    wss = request.GET.getlist('wss')[0].split(',')
    log.debug( 'The following wss are going to be removed from:'+str(wss))   
    W = getW(username)
    T = getT(username)
    for ws_id in wss:
        ws = W.objects.get(id=ws_id)
        for tag_name in tag_names:
            t = T.objects.get(name=tag_name) 
            ws.tags.remove(t)
            ws.save()    
    messages.success(request, "The folloing tags "+str(tag_names)+" were successfully removed from these working sets "+str(wss))    
    return HttpResponse('success', mimetype="text/plain") 

#
#@login_required
#def settings_remove_tags_from_wss(request):
#    username = request.user.username
#    tag_ids= request.POST.getlist('tag_ids')
#    
#    log.debug( 'Removing the following tags from wss:'+str(tag_ids))
#    wss = request.POST.getlist('wss')
#    log.debug( 'The following wss are going to be removed from:'+str(wss))   
#    W = getW(username)
#    T = getT(username)
#    for ws_id in wss:
#        ws = W.objects.get(id=ws_id)
#        for tag_id in tag_ids:
#            t = T.objects.get(id=tag_id) 
#            ws.tags.remove(t)
#            ws.save()    
#    messages.success(request, "The folloing tags "+str(tag_ids)+" were successfully removed from these working sets "+str(wss))    
#    return HttpResponse('success', mimetype="text/plain") 



#TODO: have a link to show deleted folders as well, also make it able to see deleted tags
@login_required
def settings_folders(request, username, bookname):
    F = getFolder(username, bookname)
    folders = F.objects.all().order_by('name')
    return render_to_response('folders/index.html', {'folders':folders, 'addFolderForm':AddFolderForm(), 'profile_username':username}, context_instance=RequestContext(request))


@login_required    
def settings_folder(request, username, folder_name, bookname):  
    F = getFolder(username, bookname)  
    folder = F.objects.get(name__exact=folder_name) 
    folder_form = UpdateFolderForm(instance=folder)
    return render_to_response('folders/folder.html',  {'folder':folder, 'folder_form':folder_form}, context_instance=RequestContext(request)) 


@login_required
def settings_folder_add(request, username, bookname):       
    post = request.POST.copy()
    f = AddFolderForm(post, request.FILES)     
    log.debug('form errors:'+str(f.errors))
    f.save()
    messages.success(request, "folder is successfully added!") #TODO    
    return HttpResponseRedirect(__get_pre_url(request))      


@login_required
def settings_folder_update(request, username, bookname, folder_name): 
    F = getFolder(username, bookname)  
    folder = F.objects.get(name__exact=folder_name)     
    folder_form = UpdateFolderForm(request.POST, instance=folder)
    folder_form.save()
    messages.success(request, "folder is successfully updated!") 
    #TODO: might be better to return to the changed folder page (url changed to the new folder name)
    return HttpResponseRedirect('/'+username+'/snippetbook/settings/folders/')   


@login_required
def settings_workingsets(request): 
    username = request.user.username 
    W = getW(username)
    workingsets = W.objects.all()
    current = request.GET.get("current")
    #print 'current is:', current
    if current:
#        w = W.objects.get(id=current)
#        w.current = True
#        w.save()
        request.session["current_ws"] = current
    try:
        current_workingset = request.session.get("current_ws")#W.objects.get(current=True)
        #print 'current_workingset:', current_workingset
    except ObjectDoesNotExist:
        current_workingset = None
        #print 'no current_workingset'
    #tags = __get_ws_tags(request, username)
    T = getT(username)
    tags = T.objects.all().order_by('name')
    AddWSForm = create_model_form("AddWSForm_"+str(username), W)  
    return render_to_response('workingset/index.html', {'workingsets':workingsets, 'current_workingset':current_workingset, 'tags':tags,
                                                        'addWSForm':AddWSForm(),  'profile_username':username}, context_instance=RequestContext(request))


@login_required
def settings_workingset_add(request):
    username = request.user.username
    W = getW(username)    
    w = W()
    post = request.POST
    w.name = post.get('name')
    w.desc = post.get('desc')
    w.private = post.get('private', False)
    w.save()
    w.tags = post.getlist('tags')
    w.save()
    messages.success(request, "Working set is successfully added!")
    return HttpResponseRedirect(__get_pre_url(request))   


@login_required    
def settings_workingset_update_inline(request):
    ws_name = request.POST.get('ws_name') 
    new_ws_name = request.POST.get('new_ws_name') 
    username = request.user.username
    W = getW(username)
    ws = W.objects.get(name__exact=ws_name) 
    ws.name = new_ws_name  
    ws.save()
    return HttpResponse(new_ws_name, mimetype="text/plain") 


@login_required
def settings_workingset(request, ws_name):
    username = request.user.username
    W = getW(username)    
    w = W.objects.get(name__exact=ws_name)
    ws_form = UpdateWSForm(instance=w)
    return render_to_response('workingset/ws.html',  {'ws':w, 'ws_form':ws_form}, context_instance=RequestContext(request)) 

@login_required    
def settings_workingset_update(request, ws_name):
    username = request.user.username
    W = getW(username)
    ws = W.objects.get(name__exact=ws_name) 
    ws_form = UpdateWSForm(request.POST, instance=ws)
    ws_form.save()    
    messages.success(request, "Working set is successfully updated!") 
    #TODO: might be better to return to the changed tag page (url changed to the new tag name)
    return HttpResponseRedirect('/'+username+'/settings/workingsets/')     


#not really delete, just set delete to True
@login_required    
def settings_workingset_delete(request):
    ws_name = request.POST.get('ws_name')
    W = getW(request.user.username)
    ws = W.objects.get(name__exact=ws_name) 
    ws.deleted = True
    ws.save()
    return HttpResponse('success', mimetype="text/plain")
    
    
    


@login_required  
def settings_set_advanced(request):
    request.session['advanced'] = request.GET.get('advanced')
    #if going back to normal features, custom working set feature is not used anymore
    request.session['current_ws'] = None
    return HttpResponseRedirect('/settings/') 



@login_required
def set_language(request):
    language = request.GET.get('language')
    log.debug( 'language from request is:'+language)
    request.session['django_language'] = language
    log.debug( 'The preferred langauge is set to:'+request.session.get('django_language', 'no language'))     
    return HttpResponseRedirect(__get_pre_url(request))  

def for_new_users(request):
    return render_to_response('doc/for_new_users.html', context_instance=RequestContext(request))


#a test page to try jquery stuff. TODO: might use django's tests
def test(request):    
    return render_to_response('include/test.html')
