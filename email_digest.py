#!/usr/bin/env python

import sys, os
from email.MIMEText import MIMEText
import smtplib
import time

from django.core.mail import EmailMultiAlternatives

from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)

#import settings

from django.utils.translation import ugettext as _ , activate, get_language
#import gettext

#t = gettext.translation('digest', HOME_PATH+'notebook/locale')
#_ = t.ugettext

from django.contrib.auth.models import User
from django.utils.http import urlquote





from notebook.social.models import  Group as G, Member
from notebook.notes.constants import books
from settings import EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, SERVER_EMAIL, EMAIL_USE_TLS


books.remove('notebook')


site_name = 'http://www.91biji.com'


#settings.LANGUAGE_CODE = 'en-us'

#lang1 = gettext.translation('myapplication', languages=['en-us'])
#lang2 = gettext.translation('myapplication', languages=['zh-cn'])


def get_mail_server():
    mailserver = smtplib.SMTP(EMAIL_HOST)    
    mailserver.set_debuglevel(1)
    mailserver.ehlo()
    mailserver.starttls()    
    mailserver.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    return mailserver


def sendEmail(mailserver, fromAddr, toAddrList, subject, content):
    print 'sending email...'
    #msg = MIMEText(content,  _charset='utf-8')
    msg = MIMEText(content)
    msg.set_charset('utf-8')
    msg['Subject'] = subject
    msg['From'] = fromAddr
    msg['To'] = toAddrList[0]
    mailserver.sendmail(fromAddr, toAddrList, msg.as_string())   



def build_content(note, bookname, pick_lang, title_size):
    """build the content for a single note"""
    content = ''
    html_content = ''
    #print('The current bookname is:'+bookname)
    if pick_lang == 'en-us':
        desc = note.get_desc_en()
    else:
        desc = note.get_desc_cn()  
    if pick_lang == 'en-us':
        title = note.get_title_en()
    else:
        title = note.get_title_cn()  
    desc_size = title_size + 200     
    if bookname == 'snippetbook':
        content = _('Sharing snippet:')+desc[0:desc_size]
    if bookname == 'bookmarkbook':
        content = _('Sharing bookmark:')+title[0:title_size]+'   '+note.url
    if bookname == 'scrapbook':
        content = _('Sharing scrap:')+desc[0:desc_size] + '   '+ note.url   
    if bookname == 'framebook':
        content = _('Sharing knowledge package:')+title[0:title_size] + '   ' + desc[0:desc_size] 
#===============================================================================
#    if bookname == 'notebook':
#        bookname = note.get_note_bookname()
#        print('This note of notebook is actually a note of '+bookname)
#        if bookname == 'snippetbook':
#            content = _('Sharing snippet:')+desc[0:desc_size]
#        if bookname == 'bookmarkbook':
#            content = _('Sharing bookmark:')+title[0:title_size]+'   '+note.social_bookmark.url
#        if bookname == 'scrapbook':
#            content = _('Sharing scrap:')+desc[0:desc_size] + '   '+ note.social_scrap.url   
#        if bookname == 'framebook':
#            content = _('Sharing knowledge package:')+title[0:title_size] + '   ' + desc[0:desc_size]         
#===============================================================================
   
    source_str = _('Original Note:')
     
    f = lambda x: x=="zh-cn" and "C" or"E"
    url =  site_name+  '/social/'+ note.owner.username + '/' + bookname + '/notes/note/' + str(note.id) + '/?pick_lang='+ f(pick_lang)
    html_url = '<a href="'+url+'">'+url+'</a>'       
    html_content = content + '<br/>'+source_str+'    '+html_url+'    '+_('from')+' '+\
               note.owner.username 
    content = content+'    \n'+source_str+'    '+url+'    '+_('from')+' '+\
               note.owner.username 
    
    tag_str = ','.join([t.name for t in note.tags.filter(private=False)])                
    t_str = _('tags: ') + tag_str 
    vote_str = _("note importance ranked by the owner: ")+str(note.vote)

    content = content + '\n' + t_str + '\n' + vote_str + '\n\n'
    html_content = html_content + '<br/>' + t_str + '<br/>' + vote_str + '<br/><br/>'
    #print 'built content for one note of today:', content
    return content, html_content  







#TODO: write method to turn text content into html content. Replace '\n' with '<br/>', and parse http:// link (stop when encountering whitespace)
def send_group_digest(username, groupname, freq, pick_lang):
    #print 'Sending '+freq+' digest for', username, 'in', groupname
    group = G.objects.get(name=groupname) 
    
    content = ''
    html_content = ''
    member = Member.objects.get(username=username)
        
    
    for bookname in books:  
        
        if freq == 'daily':      
            notes = group.get_notes_today(bookname)
            #print group, notes
        else:
            notes = group.get_notes_this_week(bookname)  
        if notes:
            
            #content += _(bookname) + '\n\n'
            for note in notes:
                #content +=  build_content(note, bookname, pick_lang, 200)
                note_content,html_note_content = build_content(note, bookname, pick_lang, 200)
                content += note_content 
                html_content += html_note_content
    
    if content:
        group_url = site_name +  '/groups/' +urlquote(groupname)+'/'
        html_group_url = '<a href="'+group_url+'">'+group_url+'</a>' 
        if freq == 'daily':
            digest_heading = _('Daily digest from the group:')+groupname+'\n\n\n'
        if freq == 'weekly':    
            digest_heading = _('Weekly digest from the group:')+groupname+'\n\n\n'
        settings_url = site_name + '/settings/'
        html_settings_url = '<a href="'+settings_url+'">'+settings_url+'</a>' 
        digest = digest_heading + content + '\n'+ _('Or you can go to the group page to view the new notes! ')+ \
                  group_url + '\n\n'+_('You can set up how you want to receive group digest in your setting:')+ settings_url
        html_digest = digest_heading + '<br/><br/><br/>'+ html_content +'<br/>'+ _('Or you can go to the group page to view the new notes! ')+ \
                  html_group_url + '<br/><br/>'+_('You can set up how you want to receive group digest in your setting:')+ html_settings_url
        #print 'digest is:', digest
        
        #mailserver = get_mail_server()
        
        if freq == 'daily':
            subject = (_('Group ')+groupname+_(":today's new notes!")).encode('utf-8')
        if freq == 'weekly':
            subject = (_('Group ')+groupname+_(":this week's new notes!")).encode('utf-8')   
        #sendEmail(mailserver , SERVER_EMAIL, [member.email], subject, digest.encode('utf-8'))
        #mailserver.close()

        msg = EmailMultiAlternatives(subject, digest.encode('utf-8') , SERVER_EMAIL, [member.email])
        msg.attach_alternative(html_digest.encode('utf-8') , "text/html")
        #msg.content_subtype = "html"
        msg.send()
        print 'Email digest was sent to '+member.email+' for group '+ groupname 
        time.sleep(10)
   
    

def send_digest(username, freq):
    print 'Sending ', freq, ' digetst for user:', username
    member = Member.objects.get(username=username)
    #print 'Getting groups for member:', member.username
    #pick_lang = (member.default_lang)?(member.default_lang=='E'? 'E':'C') : 'E' 
    pick_lang = 'zh-cn'
    if member.default_lang:        
         pick_lang = member.default_lang    
         activate(pick_lang)   
    #print 'current preferred language is:', get_language()
     
    #print 'Now current preferred language is:', get_language() 
    groups = member.get_groups()
    #print username, "'s groups:", groups
    for group in groups:
        send_group_digest(username, group.name, freq, pick_lang)
        
    





if __name__ == "__main__":
    command = sys.argv[1]
    members = Member.objects.all()
    if command == 'daily':
        for member in members:        
            if member.digest and member.digest == 'w': 
                pass
            elif member.digest == 'n':
                pass
            else:#if user.digest and user.digest == 'd' or not user.digest
                try:
                    send_digest(member.username, 'daily')   
                except:
                    pass 
    if command == 'weekly':
        for member in members:  
            if member.digest and member.digest == 'w':  
                try:
                    send_digest(member.username, 'weekly')   
                except:
                     pass  
            else:
                pass                
  
