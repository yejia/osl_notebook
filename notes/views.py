# -*- coding: utf-8 -*-

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
from django.contrib.sites.models import Site
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.core.mail import send_mass_mail




from notebook.notes.models import *
from notebook.snippets.models import Snippet
from notebook.bookmarks.models import Bookmark
from notebook.scraps.models import Scrap
from notebook.social.models import Member, Friend_Rel
from notebook.notes.constants import *
from notebook.notes.util import *


import notebook

import datetime
from datetime import date
import re
import operator

import time

import logging


        
#dbs = doubansay.douban()
#dbs.first_run()

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
                    'id', 'user_permissions', 'groups', 'role', 'last_login', 'date_joined', 'viewing_private')  
        

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
                if next.find('anonymous') != -1:
                    next = next.replace('anonymous', username)
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
        log.info('Registering a new user...')       
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
            messages.error(request, _("Username is already used by someone else. Please pick another one.")) 
            log.info('Registration failed. Username is already used by someone else.')  
            return HttpResponseRedirect('/registre/')          
        if password1 == password2:        
            m, created = create_member(username, email, password1)
            if created:
                log.info('A new user is created!')  
                create_db(username)
                log.info('DB is created for the new user!') 
                #automatically add the invited person to the inviter's friends        
                #notebook.social.views.add_friend(request, username)
                m1 = request.user.member
                m2 = Member.objects.get(username=username)         
                fr = Friend_Rel(friend1=m1, friend2=m2)
                #So far, make it confirmed automcatically. TODO:
                fr.comfirmed = True
                fr.save()
                log.info('New member created and added as a friend of the inviter!') 
                messages.success(request, _("New member created and added as your friend!"))  
                return HttpResponseRedirect('/registre/') 
            else:
                log.error('Error creating a member!')
                messages.error(request, _("Error creating a member!"))                 
                return HttpResponseRedirect('/registre/')   
        messages.error(request, _("Passwords don't match!"))
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


from notification.models import Notice

def get_notices(request):
    if request.user.is_anonymous():
        return HttpResponse(simplejson.dumps([]), "application/json")
    notice_url_dict={'postman_message':'/messages/', 'postman_reply':'/messages/', 'comment_receive':'/social/'+request.user.username+'/commentsfor/'}
    notices = Notice.objects.filter(recipient=request.user, unseen=True)    
    #TODO:get count of each type of notice
    ns = [(n.notice_type.label, n.notice_type.display, notice_url_dict.get(n.notice_type.label)) for n in notices]    
    return HttpResponse(simplejson.dumps(list(set(ns))), "application/json")


from notebook.notes.models import getAccessKey, UserAuth, getBoundSites

import weibopy
from weibopy import OAuthHandler, WeibopError
from weibopy.api import API

consumer_key = '2247080609' #appkey
consumer_secret = '41478741052a891677d95dedac979643' # appkey secret

class WebOAuthHandler(OAuthHandler):
    
    def get_authorization_url_with_callback(self, callback, signin_with_twitter=False):
        """Get the authorization URL to redirect the user"""
        try:
            # get the request token
            self.request_token = self._get_request_token()

            # build auth request and return as url
            if signin_with_twitter:
                url = self._get_oauth_url('authenticate')
            else:
                url = self._get_oauth_url('authorize')
            request = weibopy.oauth.OAuthRequest.from_token_and_callback(
                token=self.request_token, callback=callback, http_url=url
            )
            return request.to_url()
        except Exception, e:
            raise WeibopError(e)

def _get_referer_url(request):
    referer_url = request.META.get('HTTP_REFERER', '/')
    host = request.META['HTTP_HOST']
    if referer_url.startswith('http') and host not in referer_url:
        referer_url = '/' 
    return referer_url

def _oauth():
    """"""
    return WebOAuthHandler(consumer_key, consumer_secret)



import douban
from douban.service import DoubanService

douban_consumer_key =  '06b7d5f0d1251e30142781d2736f5a90'#'06d34ae0f60028101479e0a2e2007830' #'019564eabe5172ac04c02ec03af45804' #appkey
douban_consumer_secret = 'fdb75b2f20bff4a6'#'8e19a57b11ceb4f4' #'5d20de5ba479a333' #appkey secret




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
def get_public_frames(frame_list):
    frame_list = frame_list.filter(private=False)
    b_list = remove_private_tag_notes(frame_list)
    return b_list 



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




    
    



#TODO: add date range search, votes search
@login_required
def index(request, username, bookname):   
    #if 'framebook' == bookname:
    #    return frames(request, username, 'notebook')      
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
    #TODO: see if I don't have to write book_uri_prifix everywhere
    return render_to_response(book_template_dict.get(bookname)+'notes/notes.html', context, \
                              context_instance=RequestContext(request,{'bookname': bookname,'book_uri_prefix':'/'+username}))


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
    ws = request.GET.get('ws')    
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
    
    if not request.session.get("current_ws") or request.session.get("current_ws") in books:
        request.session["current_ws"] = bookname                 
    current_ws = request.session.get("current_ws")      
    if current_ws == 'all tags' or current_ws == 'notebook':
        #this annotate get all the note's count instead of just the bookname's 
        tags_qs = Tag.objects.using(username).all().order_by('name')#.annotate(Count('note'+book_entry_dict.get(bookname))).order_by('name') 
    else:        
        w = WorkingSet.objects.using(username).get(name__exact = current_ws)        
        #tags_qs = w.tags.using(username).all().order_by('name')
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
     
    if not request.session.get("current_ws") or request.session.get("current_ws") in books:
        request.session["current_ws"] = bookname                 
    current_ws = request.session.get("current_ws")       
    if current_ws == 'all tags' or current_ws == 'notebook':
        #this annotate get all the note's count instead of just the bookname's 
        tags_qs = Tag.objects.using(username).all().order_by('name')#.annotate(Count('note'+book_entry_dict.get(bookname))).order_by('name') 
    else:        
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
    if request.user.is_anonymous():        
        private = 'n'
    else:         	
        if private:
            #request.session['private'] = private
            #TODO:check length of input to prevent injection (database model field already has maximum length)            
            request.user.member.viewing_private = private
            request.user.member.save()
        else:
            #private = request.session.get('private', 'All')
            private = request.user.member.viewing_private	   

    #TODO: make it possible to pick any date by giving something like /2010/8/8 in the url  
    #or pick any period of time 

    date_range = request.GET.get('date_range')
    if date_range:
        request.session['date_range'] = date_range
    else:
        date_range = request.session.get('date_range', 'All')     
    
    #print 'date_range is now:', date_range
    
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
        
        
    #  TODO: make month RESTFUL
    month = request.GET.get('month')    
    if month:
        request.session['month'] = month
    else:
        month = request.session.get('month', 'All')    
       
    year = request.GET.get('year')    
    if year:
        request.session['year'] = year
    else:
        year = request.session.get('year', 'All')    

    day = request.GET.get('day')    
    if day:
        request.session['day'] = day
    else:
        day = request.session.get('day', 'All')    
        
    week = request.GET.get('week')    
    if week:
        request.session['week'] = week
    else:
        week = request.session.get('week', 'All')            
    
    #return dict(view_mode=view_mode, sort=sort, delete=delete, private=private, month=month, year=year, day=day, week=week)	   
    return dict(view_mode=view_mode, sort=sort, delete=delete, private=private, date_range=date_range, in_linkage=in_linkage, with_attachment=with_attachment,
                day=day, week=week, month=month, year=year)


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
    
        if aspect_name=='notes':
            return render_to_response(book_template_dict.get(bookname)+'notes/notes.html', context, \
                                      context_instance=RequestContext(request,{'bookname': bookname, 'advanced': get_advanced_setting(request),\
                                                                               'book_uri_prefix':'/'+username}))
        else:
            return render_to_response(book_template_dict.get(bookname)+'notes/linkages.html', context,\
                                       context_instance=RequestContext(request,{'bookname': bookname, 'advanced': get_advanced_setting(request),\
                                                                                'book_uri_prefix':'/'+username}))


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
    return render_to_response(book_template_dict.get(bookname)+'notes/note_list.html', context, context_instance=RequestContext(request,{'bookname': bookname, 'aspect_name':'notes',\
                                                                                                        'book_uri_prefix':'/'+username}))



#view included notes in a frame 
@login_required
def included_notes_in_frame(request, frame_id, username, bookname):    
    F = getFrame(username)
    f = F.objects.get(id=frame_id)
    f.owner_name = username
    notes = f.get_notes_in_order()
    note_ids_list = [n.id for n in notes]
    if note_ids_list:        
        note_list = __get_notes_by_ids(note_ids_list, username, bookname)
    else:
        note_list = __get_notes_by_ids([], username, bookname)
    qstr = __getQStr(request)
    note_list = getSearchResults(note_list, qstr, search_fields_dict.get(bookname))
    T = getT(username)
    default_tag_id = T.objects.get(name='untagged').id    
    context = __get_context(request, note_list, default_tag_id, username, bookname)    
    return render_to_response(book_template_dict.get(bookname)+'notes/note_list.html', context, context_instance=RequestContext(request,{'bookname': bookname, 'aspect_name':'notes',\
                                                                                                        'book_uri_prefix':'/'+username}))


#view included notes in a linkage 
@login_required
def included_notes_in_linkage(request, linkage_id, username, bookname):      
    l = LinkageNote.objects.using(username).get(id=linkage_id)
    l.owner_name = username
    notes = l.notes.using(username).all()
    note_ids_list = [n.id for n in notes]
    if note_ids_list:        
        note_list = __get_notes_by_ids(note_ids_list, username, bookname)
    else:
        note_list = __get_notes_by_ids([], username, bookname)
    
    
    qstr = __getQStr(request)
    note_list = getSearchResults(note_list, qstr, search_fields_dict.get(bookname))
    T = getT(username)
    default_tag_id = T.objects.get(name='untagged').id    
    context = __get_context(request, note_list, default_tag_id, username, bookname)    
    return render_to_response(book_template_dict.get(bookname)+'notes/note_list.html', context, context_instance=RequestContext(request,{'bookname': bookname, 'aspect_name':'notes',\
                                                                                                        'book_uri_prefix':'/'+username}))


def __get_context(request, note_list,default_tag_id, username, bookname, aspect_name='notes'):  
    theme = __get_view_theme(request)
    in_linkage = theme['in_linkage'] #TODO:get rid of
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
    
    if bookname == 'framebook':
        tags = None
        wss = None
    else:    
        tags = __get_ws_tags(request, username, bookname)
        
        W = getW(username)
        #TODO: get private ones
        wss = W.objects.all().order_by('name')
  
        if request.user.username != username:        
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
    folders = F.objects.filter(deleted=False)   
    if request.user.username != username:
        log.debug('Not the owner, getting public folders only...')      
        folders = F.objects.filter(private=False, deleted=False)   
       
    caches = __get_caches(request, username, bookname)
    #TODO: for note cache
    if bookname == 'notebook':
        cache_ids = caches.values_list('id', flat=True).order_by('id')
    else:     
        cache_ids = caches.values_list('cache_id', flat=True).order_by('cache_id') 
    if cache_ids.count():        
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
    month =    theme['month']  
    year =    theme['year']
    day =    theme['day']
    week =    theme['week']
    
    #print 'month:',month, ' year:',year
    #print 'day:',day, ' week:',week
    
    if delete in true_words:
        note_list = note_list.filter(deleted=True)
    else:
        note_list = note_list.filter(deleted=False)           
        
    
    if private in true_words:
            note_list = note_list.filter(private=True)
    elif private in false_words:          
            note_list = note_list.filter(private=False) 
    elif private in ['All', 'all']:
        pass
    else:
        pass           
        
    now = date.today()
    if month in ['All', 'all']:
        pass
    else:
        note_list = note_list.filter(init_date__month=month, init_date__year= now.year) 
    #print   'after month, note_list:',len(note_list)  
    if year in ['All', 'all']:
        pass
    else:
        note_list = note_list.filter(init_date__year= year) 
    #print   'after year, note_list:',len(note_list)
    if day in ['All', 'all']:
        pass
    else:
        note_list = note_list.filter(init_date__day= day, init_date__month=now.month, init_date__year= now.year)      
    if week in ['All', 'all']:
        pass
    elif week=='this': #TODO:
        one_week_ago = now - datetime.timedelta(days=7)
        note_list = note_list.filter(init_date__gte=one_week_ago.strftime('%Y-%m-%d'),  init_date__lte=now.strftime('%Y-%m-%d 23:59:59')
                                            )    
    #print 'date_range:', date_range
    #print 'before date_range:', len(note_list)
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
    
    #print 'after date_range:', len(note_list)
        
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
    sorted_note_list = note_list.order_by('%s%s' % ((order_type == 'desc' and '-' or ''), order_field),'-init_date','desc') 
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
    
    return render_to_response(book_template_dict.get(bookname)+'folders.html', context, context_instance=RequestContext(request,{'bookname': bookname,'book_uri_prefix':'/'+username}))



#TODO:add protection
#below is copied from note_raw except using a different template page
def note(request, username, bookname, note_id):
    log.debug('Getting the note:'+note_id)
    if 'framebook' == bookname:
        return frame(request, username, note_id)
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)    
    #linkages = note.linkagenote_set.all()
    
    notes_included = None
    if note.get_note_type() == 'Frame':
        notes_included = note.frame.notes.using(username).all()       
    
    UpdateNForm = create_model_form("UpdateNForm_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=__get_ws_tags(request, username, bookname))})
    note_form = UpdateNForm(instance=note)
    
    N_T = getNoteTranslation(username)
    UpdateNoteTransForm = create_model_form("UpdateNoteTransForm_"+str(username), N_T)          
    if not note.get_lang():
        note_trans_form = UpdateNoteTransForm()
    else:    
        note_trans = Note_Translation.objects.using(username).get(note=note)            
        note_trans_form = UpdateNoteTransForm(instance=note_trans)
    
    pick_lang =  request.GET.get('pick_lang')  
    return render_to_response(book_template_dict.get(bookname)+'notes/note/note.html', {'note':note, 'notes_included':notes_included, \
                                                                                   'note_form':note_form, 'profile_username':username, \
                                                                                   'note_trans_form':note_trans_form,\
                                                                                   'pick_lang':pick_lang
                                                                                   },
                                                                                    context_instance=RequestContext(request, {'bookname': bookname,\
                                                                                                                              'aspect_name':'notes',\
                                                                                                                              'book_uri_prefix':'/'+username }))
    


  
#TODO:add protection
@login_required
def note_raw(request, username, bookname, note_id):
    log.debug('Getting the note:'+note_id)
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    linkages = note.linkagenote_set.all()
    UpdateNForm = create_model_form("UpdateNForm_"+str(username), N, fields={'tags':forms.ModelMultipleChoiceField(queryset=__get_ws_tags(request, username, bookname))})
    note_form = UpdateNForm(instance=note)
    return render_to_response(book_template_dict.get(bookname)+'notes/note_raw.html', {'note':note, 'linkages':linkages,'note_form':note_form, 'profile_username':username}, context_instance=RequestContext(request, {'bookname': bookname,'aspect_name':'notes'}))
    

#below is not used  
#def alltags(request, username):   
#    note_list = Note.objects.filter(delete=False).order_by('-init_date')
#    return render_to_response('notes/note_list_by_tag.html', {'note_list': note_list, 'tags':Tag.objects.all(), 
#                                                'current_tag':'','view_mode':view_mode, 'sort':sort})

@login_required
def update_note(request, note_id, username, bookname): 
    log.debug( 'updating note :'+note_id)
    #N = getNote(username, bookname)
#    note = N.objects.get(id=note_id)  
    note = Note.objects.using(username).get(id=note_id)  
    #TODO: probably there is no need with the complicated dynamic class generation anymore. Just use the way below
    note.owner_name = username
 

    note.title = request.POST.get('title')
    note.desc = request.POST.get('desc')
    note.event = request.POST.get('event')
    note.private = request.POST.get('private', False)
    note.deleted = request.POST.get('delete', False)
    
    #note.init_date = request.POST.get('init_date')
    if note.get_note_type() == 'Frame':
        note.frame.owner_name = username
        note.vote = note.frame.get_vote()
        note.tags = note.frame.get_sum_of_note_tag_ids()
    else:    
        note.vote = request.POST.get('vote')
        note.tags = request.POST.getlist('tags')
    url = request.POST.get('url')
    if url:
        #TODO: if note type is note
        note.url = url
    file = request.FILES.get('attachment')
    if file:
        note.attachment = file 
    note.save()    

    log.debug( 'the note %s is updated.' % (note_id))
    full_path =  request.get_full_path()  
    pre_url = full_path[:-11] #remove "addNote/"
    log.debug( 'redirect to the page that add note form is submitted from:'+pre_url)
    messages.success(request, _("Note is successfully updated!")) #TODO
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))    


@login_required
def update_note_trans(request, note_id, username, bookname): 
    #note_id is the id of the original note
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id) 
    #trans, created =  Note_Translation.objects.using(username).get_or_create(note=note)
 
    title = request.POST.get('title')
    desc = request.POST.get('desc')   
    lang = request.POST.get('lang')   
    original_lang = request.POST.get('original_lang')  
    note.set_translation(original_lang, lang, title, desc) 
    note.save()
    #trans.owner_name = username
    #trans.save() 
    #TODO: use below to replace all return HttpResponseRedirect(__get_pre_url(request))  
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))  


#set the order for the notes in a frame. So this only is supposed to be for framebook
@login_required
def set_notes_order_in_frame(request, note_id, username, bookname): 
    log.debug( 'setting the order of the notes in a frame:'+note_id)
    ordered_notes = request.GET.get('ordered_notes').split(',')   
    #print 'ordered_notes:',ordered_notes
    N = getNote(username, bookname)
    f = N.objects.get(id=note_id)  
    f.set_notes_order(ordered_notes)
    return HttpResponse('successful', mimetype="text/plain")  
    



@login_required    
def update_note_inline(request, username, bookname):    
    note_id = request.POST.get('id')
    content =  request.POST.get('content')  
    note_field = request.POST.get('note_field')  
    
    N = getNote(username, bookname)    
    note = N.objects.get(id=note_id)
    if note_field=='note_title':
        note.title = content
    if note_field=='note_desc':
        note.desc = content
    if note_field=='note_event':
        note.event = content.lstrip("{").rstrip("}") #TODO: change Note's event to extra, the same as bookmarks and scraps
    #below is not used anymore. Instead, update_note_tags_inline is used.
    if note_field=='note_tags':
        note.update_tags(content)    
    #note.tags = content	
    
    if note_field=='note_init_date':
        note.init_date = datetime.datetime.strptime(content,'%Y-%m-%d %H:%M')   
        
    #below is not used anymore. update_note_included_notes_inline is used to add notes instead
    if note_field=='note_add_notes':
        note.add_notes(content)
    
    note.save()
    log.debug( 'note updated')
    #TODO: if error
    return HttpResponse(content, mimetype="text/plain") 
    


@login_required    
def update_note_tags_inline(request, username, bookname): 
    note_id = request.POST.get('id')
    tags =  request.POST.get('tags')  
    N = getNote(username, bookname)    
    note = N.objects.get(id=note_id)
    note.update_tags(tags) 
    note.save() 
    return HttpResponse(simplejson.dumps({'note_id':note.id, 'display_tags':note.display_tags(),\
                                          'note_tags':note.get_tags()}),
                                                                     "application/json")


@login_required  
def add_notes_to_frame(request, username, bookname): 
    note_id = request.POST.get('id')
    included_notes_added =  request.POST.get('included_notes_added')  
    N = getNote(username, bookname)    
    note = N.objects.get(id=note_id)
    note.add_notes(included_notes_added) 
    note.owner_name = username
    note.vote = note.get_vote()
    note.tags = note.get_sum_of_note_tag_ids()    
    note.save() 
    added_notes = __get_notes_by_ids(included_notes_added.split(','), username, 'notebook')
     #TODO: find or write function that mimic truncatewords in template
    notes_added = [[n.id, n.title, n.desc[0:200], n.vote, n.get_note_bookname(), n.get_note_type()]  for n in added_notes]
    return HttpResponse(simplejson.dumps({'note_id':note.id, 'notes_added':notes_added}),
                                                                     "application/json")


@login_required
def delete_note_from_frame(request, username, bookname):    
    frame_id = request.POST.get('linkage_id')
    log.debug( 'frame is:'+str(frame_id))
    F = getFrame(username)
    frame = F.objects.get(id=frame_id)
    note_id = request.POST.get('note_id')
    log.debug('note to be deleted from the frame:'+note_id)
    frame.remove_note(note_id)  
    frame.owner_name = username
    frame.vote = frame.get_vote()
    frame.tags = frame.get_sum_of_note_tag_ids()   
    frame.save()
    return HttpResponse('note deleted', mimetype="text/plain")  




@login_required   
def add_comment(request, username, bookname):  
    note_id = request.POST.get('id')
    N = getNote(username, bookname)
    note = N.objects.get(id=note_id)
    content = request.POST.get('content')
    NC = getNC(username)
    nc = NC(note=note, desc=content)
    nc.save()
    return  HttpResponse(simplejson.dumps({'note_id':note_id, 'comment_id':nc.id, 'comment_desc':nc.desc}),
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
    log.info('making private')
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
    
    #post = request.POST.copy()    
    
    #tags = request.GET.getlist('tags')[0].split(',')  
    tags = request.GET.get('tags').split(',')  
    
    if not tags or (len(tags) == 1 and tags[0] == u''):
        tags = ['untagged']
        #post.setlist('tags', tags)
    
    n = N(desc=request.GET.get('desc'))  
    n.vote = 0
    private = request.GET.get('private', False)
    if private == 'true':
        n.private = True
    else:
        n.private = False     
    n.save()
    n.add_tags(tags, bookname)
    n.save()
    #messages.success(request, "Note is successfully added!") #TODO    
    
    
    #'init_date':n.init_date
    return  HttpResponse(simplejson.dumps({'note_id':n.id, 'private':n.private, 'tags':n.get_tags(),'display_tags':n.display_tags(),
                                           'title':n.title,'desc':n.desc, 'vote':n.vote, 'init_date':n.init_date.strftime("%Y-%m-%d %H:%M"),
                                            'last_modi_date':n.last_modi_date.strftime("%Y-%m-%d %H:%M"),'comments':n.display_comments()}),  "application/json")

    #return HttpResponseRedirect(__get_pre_url(request))    
    

#TODO: other better ways of implementation
#TODO: use HttpRequest.META['HTTP_REFERER'] such as return request.META.get('HTTP_REFERER','/')
def __get_pre_url(request):
    full_path =  request.get_full_path() 
    s = full_path[:full_path.rfind('/')]#get rid of the last slash, assuming url always ends with a slash
    pre_url =  s[:s.rfind('/')+1]    
    #log.debug('redirect to the page that add note form is submitted from:'+str(pre_url))
    return pre_url


def __get_parent_note_id(noteid, username, bookname):    
    N = getNote(username, bookname)
    n = N.objects.get(id=noteid)
    return n.note_ptr_id
    
def __get_parent_note_ids(noteids, username, bookname):
    return  [__get_parent_note_id(id, username, bookname) for id in noteids]
        



#TODO: method name seems to overlap with linkagenotes method
@login_required
def  frame_notes(request, username, bookname):
    
    #if making frames in notes viewing page, need to get passed the bookname of each note as well. 
    if 'notebook' == bookname:
        pass #TODO
    
    
    note_ids = request.POST.get('notes')    
    notes = note_ids.split(",")   
    notes = list(set(notes)) 
    
    #ptr_notes = __get_parent_note_ids(notes, username, bookname)
    #print 'ptr_notes is:', ptr_notes #TODO:should be the same as notes
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

    F = getFrame(username)
    frameNote = F()
    frameNote.title = post.get('title')
    frameNote.desc = post.get('desc')
    frameNote.private = post.get('private', False)
    
    file = request.FILES.get('attachment')
    if file:
        frameNote.attachment = file 
    frameNote.save()
    #TODO: below is not correct since note_ids correspond to those snippet/bookmark/scrap ids instead of notes ids
    frameNote.add_notes(','.join(notes)) 
    frameNote.tags = tags    
    
#    AddLForm = create_model_form("AddLForm_"+str(username), L, options={'exclude':('tags')})
#    
#    linkageNote = AddLForm(post, request.FILES, instance=L()) 
#    #print "linkageNote.is_valid():",linkageNote.is_valid()
#    print "linkageNote.errors:",linkageNote.errors 
    frameNote.vote = frameNote.get_vote()
    frameNote.save()
    messages.success(request, "A frame is successfully created!")
    return HttpResponseRedirect(__get_pre_url(request))  




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
    



#===============================================================================
# @login_required
# def frames(request, username, bookname):
#    #TODO: allow filter on delete
#    
#    #TODO: get linkages according to bookname
#    
#    F = getFrame(username)
#    note_list = F.objects.filter(deleted=False)
#    if request.user.username != username:
#        log.debug('Not the owner of the notes requested, getting public notes only...')
#        note_list = get_public_frames(note_list)        
#     
#    view_mode, sort,  delete, private, date_range, order_type, with_attachment, paged_notes, cl = __get_notes_context(request, note_list)  
#    folders, caches, next_cache_id = __get_menu_context(request, username, bookname)
#    qstr = '' #TODO: for now, no query
#    now = date.today()        
#    return render_to_response('framebook/notes/notes.html', {'note_list': paged_notes, 
#                                                 #'tags':tags,
#                                                  'view_mode':view_mode, 
#                                                 'sort':sort, 'delete':delete, 'private':private, 'day':now.day, 'month':now.month, 'year':now.year, 'cl':cl,
#                                                 'folders':folders,'qstr':qstr, 'profile_username':username, 'aspect_name':'linkagenotes', 'date_range':date_range, 
#                                                 'order_type':order_type, 'with_attachment':with_attachment, 'users':User.objects.all(), 
#                                                 'current_ws':request.session.get("current_ws", None),'included_aspect_name':'notes'},
#                                                  context_instance=RequestContext(request,{'bookname': bookname,}))
#===============================================================================




@login_required
def linkagenotes(request, username, bookname):
    #TODO: allow filter on delete
    
    #TODO: get linkages according to bookname
    
    #L = getLinkage(username, bookname)
    L = getL(username)
    note_list = L.objects.using(username).all()
    
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
    
    return render_to_response(book_template_dict.get(bookname)+'notes/linkages.html', {'note_list': paged_notes, 
                                                 'tags':tags, 'view_mode':view_mode, 
                                                 'sort':sort, 'delete':delete, 'private':private, 'day':now.day, 'month':now.month, 'year':now.year, 'cl':cl,
                                                 'folders':folders,'qstr':qstr, 'profile_username':username, 'aspect_name':'linkagenotes', 'date_range':date_range, 
                                                 'order_type':order_type, 'with_attachment':with_attachment, 'users':User.objects.all(), 
                                                 'current_ws':request.session.get("current_ws", None),'included_aspect_name':'notes'},
                                                  context_instance=RequestContext(request,{'bookname': bookname,}))




@login_required
def frame(request, username, frame_id):    
    F = getFrame(username)    
    frame = F.objects.get(id=frame_id)
   
#===============================================================================
#    if request.user.username == username:
#        frame_notes_display = frame.display_notes()
#    else:
#        frame_notes_display = frame.display_public_notes()    
#    #tags of each note has to be added as below since it again needs to know which user database to use. 
#    #The same for note type    
#    for n in frame_notes_display:
#        note_id = n[0]        
#        N = getNote(username, 'notebook')
#        note = N.objects.get(id=note_id)  
#        type = note.get_note_type()
#        n.insert(4, type)
#        note_bookname = note.get_note_bookname()
#        n.insert(5, note_bookname)
#        n.insert(6, note.get_tags())
#        if type == 'Bookmark': 
#            n.insert(7, note.bookmark.url)
#        elif type == 'Scrap':   
#            n.insert(7, note.scrap.url) 
#        else:
#            n.insert(7, '')     
#===============================================================================
    N = getNote(username, 'notebook')    
    UpdateNForm = create_model_form("UpdateNForm_"+str(username), N, options={'exclude':('tags','vote')})
    note_form = UpdateNForm(instance=frame)
    sort =  request.GET.get('sort')  
    if request.user.username == username:
        notes_in_frame = frame.get_notes_in_order(sort) 
    else:
        notes_in_frame = frame.get_public_notes_in_order(sort)     
   
    #add_owner_name(frame, 0)  
    
    N_T = getNoteTranslation(username)
    UpdateNoteTransForm = create_model_form("UpdateNoteTransForm_"+str(username), N_T)          
    if not frame.get_lang():
        note_trans_form = UpdateNoteTransForm()
    else:    
        note_trans = Note_Translation.objects.using(username).get(note=frame)            
        note_trans_form = UpdateNoteTransForm(instance=note_trans)
    
    pick_lang =  request.GET.get('pick_lang')  
    
    
    return render_to_response('framebook/notes/note/note.html', {'note':frame, 'notes_in_frame':notes_in_frame, 'sort':sort, \
                                                             'profile_username':username, 'note_form':note_form,\
                                                             'note_trans_form':note_trans_form,'pick_lang':pick_lang\
                                                              }, \
                                                             context_instance=RequestContext(request,{'bookname': 'framebook','book_uri_prefix':'/'+username}))



#Trasveral of the tree and and owner_name to each one. Not used anymore, 
#since the tag get owner_name from context directly  
#===============================================================================
# def add_owner_name(parent_note, level):
#    prefix = '    '
#    for i in range(level):
#        prefix = prefix + '    '
#    level = level + 1    
#    print prefix +    parent_note.desc + ' :'+ parent_note.owner_name
#    if parent_note.get_note_type() == 'Frame':        
#        parent_note.frame.owner_name = parent_note.owner_name
#        for n in parent_note.frame.get_notes_in_order(): 
#            n.owner_name = parent_note.owner_name                     
#            add_owner_name(n, level)
#    return None     
#===============================================================================



@login_required
def linkagenote(request, note_id, username, bookname):    
    L = getL(username)
    note = L.objects.get(id=note_id)
    linkage_form = UpdateLinkageNoteForm(instance=note)
    return render_to_response(book_template_dict.get(bookname)+'notes/note/linkagenote.html', {'note':note, 'linkage_form':linkage_form, 'profile_username':username}, context_instance=RequestContext(request,{'bookname': bookname,}))


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




#  


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
    #TODO:use POST
    note_ids= request.GET.getlist('note_ids')[0].split(',')        
    tags_to_add = request.GET.getlist('tags_to_add')[0].split(',')    	
    N = getNote(username, bookname)
    T = getT(username)
    for note_id in note_ids:
        note = N.objects.get(id=note_id)    
        for tag_id in tags_to_add:
            log.debug('adding a tag')
            t = T.objects.get(id=tag_id)     
            note.tags.add(t)    
            note.save()      
    log.info('tag added') 
    return HttpResponse('success', mimetype="text/plain") 
    


@login_required    
def add_tags_to_notes2(request, username, bookname):    
    note_ids= request.GET.getlist('note_ids')[0].split(',')      
    tags_to_add = request.GET.getlist('tags_to_add')[0].split(',')      
    N = getNote(username, bookname)    
    result = [] 
    for note_id in note_ids:
        note = N.objects.get(id=note_id)
        note.add_tags(tags_to_add, bookname)
        result.append([note_id, note.get_tags(), note.display_tags()])        
    log.info('tag added') 
    return  HttpResponse(simplejson.dumps(result), "application/json")
    #return HttpResponse('success', mimetype="text/plain") 


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
    

import douban
from douban import service

@login_required
def share_todelete(request, username, bookname): 
    d_service = douban.service.DoubanService(api_key=douban_consumer_key, secret=douban_consumer_secret)
    access_key, access_secret = getAccessKey(username, 'douban')
    d_service.client.token = douban.oauth.OAuthToken(str(access_key), str(access_secret))    
    #status = d_service.GetPeople('/people/yejia')
    #print 'status:', status.ToString()
    status = d_service.AddBroadcasting('/miniblog/saying', """<?xml version='1.0' encoding='UTF-8'?><entry xmlns:ns0="http://www.w3.org/2005/Atom" xmlns:db="http://www.douban.com/xmlns/"><content>we got milk</content></entry>""") 
    
    return HttpResponse('success', mimetype="text/plain")   




#TODO: private notes cannot be shared. Might implement the permission control at a finer level
@login_required
def share(request, bookname):     
    note_ids = request.POST.getlist('note_ids')   
    N = getSN(bookname)
    msgs = [] 
    
    bound_sites = getBoundSites(request.user.username)   
    if not bound_sites:
        return HttpResponse(simplejson.dumps({'count_of_notes':len(note_ids), 'count_of_sites':len(bound_sites)}),
                                                                     "application/json")
            
    #weibo
    if 'sina' in bound_sites:
        auth_client = _oauth()
        access_key, access_secret = getAccessKey(request.user.username, 'sina')        
        auth_client.set_access_token(access_key, access_secret)
        api = API(auth_client)
    
    #douban
    if 'douban' in bound_sites:
        d_service = DoubanService(api_key=douban_consumer_key, secret=douban_consumer_secret)
        d_access_key, d_access_secret = getAccessKey(request.user.username, 'douban')        
        d_service.client.token = douban.oauth.OAuthToken(str(d_access_key), str(d_access_secret))
    if 'tencent' in bound_sites: 
             #TODO: 
             pass  
    if 'twitter' in bound_sites:  
             #TODO: 
             pass   
    if 'facebook' in bound_sites:  
             #TODO: 
             pass  
        
    #print 'douban_service.client.token:', douban_service.client.token
    
    current_site = Site.objects.get_current()   
    #print 'current_site.domain:',current_site.domain
    for note_id in note_ids:         
        note = N.objects.get(id=note_id)
        content = ''
        log.info('The current bookname is:'+bookname)
        
        if bookname == 'snippetbook':
            content = _('Sharing snippet:')+note.desc[0:100]
        if bookname == 'bookmarkbook':
            content = _('Sharing bookmark:')+note.title+'   '+note.url
        if bookname == 'scrapbook':
            content = _('Sharing scrap:')+note.desc[0:100] + '   '+ note.url   
        if bookname == 'framebook':
            content = _('Sharing knowledge package:')+note.title + '   ' + note.desc[0:100] 
        if bookname == 'notebook':
            bookname = note.get_note_bookname()
            log.info('This note of notebook is actually a note of '+bookname)
            if bookname == 'snippetbook':
                content = _('Sharing snippet:')+note.desc[0:100]
            if bookname == 'bookmarkbook':
                content = _('Sharing bookmark:')+note.title+'   '+note.bookmark.url
            if bookname == 'scrapbook':
                content = _('Sharing scrap:')+note.desc[0:100] + '   '+ note.scrap.url   
            if bookname == 'framebook':
                content = _('Sharing knowledge package:')+note.title + '   ' + note.desc[0:100]         
        if request.user.username == note.owner.username:
            source_str = _('Original Note:')
        else:
            source_str = _('Forwarded Note:')    
        #TODO:if on a single note display page, share in js can pass the current url directly.
        #TODO: think whether still allow bulk sharing.
        pick_lang = request.GET.get('pick_lang')
        if not pick_lang:
            pick_lang = 'E'
           
        content = content +'    '+ source_str +'  http://'+current_site.domain+'/social/'+\
                  note.owner.username+'/'+bookname+'/notes/note/'+str(note.id)+'/?pick_lang='+pick_lang+'    '+_('from')+' '+\
                   note.owner.username
        
#        #send to weibo        
        if 'sina' in bound_sites:
            status = api.update_status(status=content)
            #can only send one weibo at one time? Have to wait a while to send another one?TODO:
            time.sleep(0.5) #     
        if 'douban' in bound_sites:
            saying = u"""<?xml version='1.0' encoding='UTF-8'?><entry xmlns:ns0="http://www.w3.org/2005/Atom" xmlns:db="http://www.douban.com/xmlns/"><content>"""+content+u"""</content></entry>"""    
            status = d_service.AddBroadcasting('/miniblog/saying', saying.encode('utf8')) 
            #print 'status:', status.ToString()
        if 'tencent' in bound_sites: 
             #TODO: 
             pass  
        if 'twitter' in bound_sites:  
             #TODO: 
             pass   
        if 'facebook' in bound_sites:  
             #TODO: 
             pass       
        #buzz
#===============================================================================
#        msg = (('From osl '+bookname+': '+note.title +' '+note.desc).encode('utf8'), '', 'yuanliangliu@gmail.com', ['buzz@gmail.com'])   
#        msgs.append(msg) 
#        
#===============================================================================
               
        #share_note(note_id, username)
    #send_mass_mail(tuple(msgs), fail_silently=False)   
    

    return HttpResponse(simplejson.dumps({'count_of_notes':len(note_ids), 'count_of_sites':len(bound_sites)}),
                                                                     "application/json")    

    
#TODO: possibly use these below as actions that is used to group update the private field of notes  
@login_required
def set_notes_private(request, username, bookname):     
    note_ids = request.POST.getlist('note_ids')    
    N = getNote(username, bookname)
    notes = N.objects.filter(id__in=note_ids)
    #below doesn't call note.save9)? It seems that it doesn't withdrawn notes made private from public. why? TODO:
    #notes.update(private = True)
    for note in notes:
        note.private = True
        note.save()
    return HttpResponse(simplejson.dumps(note_ids), "application/json")   
    #return HttpResponse('success', mimetype="text/plain") 

@login_required
def set_notes_public(request, username, bookname): 
    note_ids = request.POST.getlist('note_ids')   
    N = getNote(username, bookname)
    notes = N.objects.filter(id__in=note_ids)    
    #notes.update(private = False)
    for note in notes:
        note.private = False
        note.save()
    return HttpResponse(simplejson.dumps(note_ids), "application/json")  
    #return HttpResponse('success', mimetype="text/plain")

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
    result = []
    for note_id in note_ids:
        note = N.objects.get(id=note_id)
        note.remove_tags(tags_to_remove)   
        result.append([note_id, note.get_tags(), note.display_tags()])
    
    return  HttpResponse(simplejson.dumps(result), "application/json")
    #return HttpResponse('success', mimetype="text/plain") 
    

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
    note_ids= request.POST.getlist('selected_note_ids[]')#TODO:why need to add []?
    #print  'selected_note_ids is:'+str(note_ids)   
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



#TODO: delete...
@login_required
def clear_cache(request, username, bookname, cache_id):
    C = getCache(username, bookname)
    #It seems that dynamic class had a problem to find the parent or child in the right user db to delete
    #So the following code used. Might think of a better solution TODO:
    N_C = getCache(username, 'notebook')
    Sn_C = getCache(username, 'snippetbook')
    B_C = getCache(username, 'bookmarkbook')
    Sc_C = getCache(username, 'scrapbook')
    F_C = getCache(username, 'framebook')
    if bookname == 'notebook':        
        cache = C.objects.get(id=cache_id)        
        try:
            cache.snippet_cache            
            #cache.snippet_cache.delete()   
            snc = Sn_C.objects.get(id=cache_id)            
            snc.delete()         
        except ObjectDoesNotExist:
            try:
                cache.bookmark_cache                
                #cache.bookmark_cache.delete()
                bc = B_C.objects.get(id=cache_id)            
                bc.delete()      
            except ObjectDoesNotExist:
                try:
                    cache.scrap_cache                    
                    #cache.scrap_cache.delete()  
                    scc = Sc_C.objects.get(id=cache_id)            
                    scc.delete()                     
                except ObjectDoesNotExist:
                    try:
                        cache.frame_cache                        
                        #cache.frame_cache.delete() 
                        fc = F_C.objects.get(id=cache_id)            
                        fc.delete()                           
                    except ObjectDoesNotExist:                         
                        log.error('No cache type found!')
                        
        cache.delete()
    else:
        cache = C.objects.get(cache_id=cache_id)        
        cache.delete() 
        #deleting the parent
        nc = N_C.objects.get(id=cache.id)            
        nc.delete()          
        
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
    
    wss = request.GET.getlist('wss')[0].split(',')
    #print   'wss:',wss 
    W = getW(username)
    T = getT(username)
    for ws_id in wss:
        ws = W.objects.get(id=ws_id)
        for tag_name in tag_names:
            t = T.objects.get(name=tag_name) 
            ws.tags.add(t)
            ws.save()        
    messages.success(request, "The tags were successfully added to these working sets")     
    return HttpResponse('success', mimetype="text/plain") 



@login_required
def settings_remove_tags_from_wss2(request):
    username = request.user.username
    tag_names= request.GET.getlist('tags_to_add')[0].split(',')    
    wss = request.GET.getlist('wss')[0].split(',')    
    W = getW(username)
    T = getT(username)
    for ws_id in wss:
        ws = W.objects.get(id=ws_id)
        for tag_name in tag_names:
            t = T.objects.get(name=tag_name) 
            ws.tags.remove(t)
            ws.save()    
    messages.success(request, "The tags were successfully removed from the working sets.")  
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
    folders = F.objects.filter(deleted=False).order_by('name')
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
    return HttpResponseRedirect('/'+username+'/'+bookname+'/settings/folders/')   


@login_required
def settings_workingsets(request): 
    username = request.user.username 
    W = getW(username)
    workingsets = W.objects.all().order_by('name')
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




def set_language(request):
    language = request.GET.get('language')
    log.debug( 'language from request is:'+language)
    request.session['django_language'] = language
    log.debug( 'The preferred langauge is set to:'+request.session.get('django_language', 'no language'))     
    #return HttpResponseRedirect(__get_pre_url(request))  
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

def for_new_users(request):
    return render_to_response('doc/for_new_users.html', context_instance=RequestContext(request))


def about(request):
    topic = request.GET.get('topic')
    if not topic:
        return render_to_response('doc/about.html', context_instance=RequestContext(request))
    elif topic == 'contact':
        return render_to_response('doc/contact.html', context_instance=RequestContext(request))


allbindingsites = ['sina', 'douban', 'tencent', 'facebook', 'twitter']

def bind(request): 
    back_to_url = _get_referer_url(request)
    bound_sites = getBoundSites(request.user.username)   
    if not bound_sites:
        messages.info(request, 'You have not bound any site for sharing yet. Choose sites below for binding.')
    unbound_sites = set(allbindingsites) - set(bound_sites)    
    return render_to_response('settings/binding.html', {'bound_sites':bound_sites, 'unbound_sites': unbound_sites, 'back_to_url':back_to_url}, context_instance=RequestContext(request))


def bind_remove_auth(request):
    site = request.GET.get('site')
    back_to_url = _get_referer_url(request)
    if site:
        sa = UserAuth.objects.get(user=request.user, site=site)
        sa.delete()
    return HttpResponseRedirect(back_to_url)     
        

def bind_request_auth(request):
    site = request.GET.get('site')
    back_to_url = _get_referer_url(request)
    request.session['login_back_to_url'] = back_to_url
    login_backurl = request.build_absolute_uri('/settings/bindCheck?site='+site)    
    if site:        
        if 'sina' == site:
            log.info('sina authorizing...')              
            auth_client = _oauth()
            auth_url = auth_client.get_authorization_url_with_callback(login_backurl)            
            request.session['sina_oauth_request_token'] = auth_client.request_token             
            return HttpResponseRedirect(auth_url)
       
        if 'douban' == site:
            log.info('douban authorizing...')           
            douban_service = DoubanService(api_key=douban_consumer_key, secret=douban_consumer_secret)
            request_token = douban_service.client.get_request_token()
            auth_url = douban_service.GetAuthorizationURL(request_token[0], request_token[1], callback=login_backurl)            
            request.session['douban_oauth_request_token_key'] = request_token[0]
            request.session['douban_oauth_request_token_secret'] = request_token[1]            
            return HttpResponseRedirect(auth_url)
        if 'tencent' == site:  
             #TODO: 
             pass  
        if 'twitter' == site:  
             #TODO: 
             pass   
        if 'facebook' == site:  
             #TODO: 
             pass      
            
      
def bind_check(request):
    """"""

    log.info('bind checking...')    
    site = request.GET.get('site')
    if site:        
        if 'sina' == site:           
            verifier = request.GET.get('oauth_verifier', None)
            auth_client = _oauth()            
            request_token = request.session['sina_oauth_request_token']
            del request.session['sina_oauth_request_token']            
            auth_client.set_request_token(request_token.key, request_token.secret)
            access_token = auth_client.get_access_token(verifier)
            #print 'access_token is:', access_token
            if access_token: 
                ua, created = UserAuth.objects.get_or_create(user=request.user, site='sina')
                ua.access_token_key = access_token.key
                ua.access_token_secret = access_token.secret
                ua.save()
            else:
                log.error('no access token obtained for the site sina.')    
        if 'douban' == site:
            douban_service = DoubanService(api_key=douban_consumer_key, secret=douban_consumer_secret)
            access_token = douban_service.client.get_access_token(request.session['douban_oauth_request_token_key'], request.session['douban_oauth_request_token_secret'])
            if access_token:                
                uid = access_token[2]
                ua, created = UserAuth.objects.get_or_create(user=request.user, site='douban')
                ua.access_token_key = access_token[0]
                ua.access_token_secret = access_token[1]
                ua.save()
            else:
                log.error('no access token obtained for the site douban.')    
        if 'tencent' == site:  
             #TODO: 
             pass  
        if 'twitter' == site:  
             #TODO: 
             pass   
        if 'facebook' == site:  
             #TODO: 
             pass        
    # 
    back_to_url = request.session.get('login_back_to_url', '/')
    return HttpResponseRedirect(back_to_url)





#a test page to try jquery stuff. TODO: might use django's tests
def test(request):    
    return render_to_response('include/test.html')
