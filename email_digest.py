#!/usr/bin/env python

import sys, os
from email.MIMEText import MIMEText
import smtplib



from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)

import settings

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User






from notebook.social.models import  Group as G, Member
from notebook.notes.constants import books
from settings import EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, SERVER_EMAIL, EMAIL_USE_TLS


books.remove('notebook')


site_name = 'http://www.91biji.com'


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
        content = ''
        print('The current bookname is:'+bookname)
        if pick_lang == 'E':
            desc = note.get_desc_en()
        else:
            desc = note.get_desc_cn()  
        if pick_lang == 'E':
            title = note.get_title_en()
        else:
            title = note.get_title_cn()  
        desc_size = title_size + 20     
        if bookname == 'snippetbook':
            content = _('Sharing snippet:')+desc[0:desc_size]
        if bookname == 'bookmarkbook':
            content = _('Sharing bookmark:')+title[0:title_size]+'   '+note.url
        if bookname == 'scrapbook':
            content = _('Sharing scrap:')+desc[0:desc_size] + '   '+ note.url   
        if bookname == 'framebook':
            content = _('Sharing knowledge package:')+title[0:title_size] + '   ' + desc[0:desc_size] 
        if bookname == 'notebook':
            bookname = note.get_note_bookname()
            print('This note of notebook is actually a note of '+bookname)
            if bookname == 'snippetbook':
                content = _('Sharing snippet:')+desc[0:desc_size]
            if bookname == 'bookmarkbook':
                content = _('Sharing bookmark:')+title[0:title_size]+'   '+note.social_bookmark.url
            if bookname == 'scrapbook':
                content = _('Sharing scrap:')+desc[0:desc_size] + '   '+ note.social_scrap.url   
            if bookname == 'framebook':
                content = _('Sharing knowledge package:')+title[0:title_size] + '   ' + desc[0:desc_size]         
       
        source_str = _('Original Note:')
         

        url =  site_name+  '/social/'+ note.owner.username + '/' + bookname + '/notes/note/' + str(note.id)
        content = content+'    \n'+source_str+'    '+url+'    '+_('from')+' '+\
                   note.owner.username + '\n\n'

        print 'built content for one note of today:', content
        return content  






def send_group_daily_digest(username, groupname):
    print 'Sending digest for', username, 'in', groupname
    group = G.objects.get(name=groupname) 
    
    content = ''
    member = Member.objects.get(username=username)
    #pick_lang = (member.default_lang)?(member.default_lang=='E'? 'E':'C') : 'E' 
    if member.default_lang:
        if member.default_lang == 'E':
            pick_lang = 'E'
        else:
            pick_lang = 'C'
    else:
        pick_lang = 'C'
    
    for bookname in books:        
        notes = group.get_notes_today(bookname)
        if notes:
            #content += _(bookname) + '\n\n'
            for note in notes:
                content +=  build_content(note, bookname, pick_lang, 200)
 
    if content:
        group_url = site_name +  '/groups/' +groupname+'/'
        digest = _('Daily digest from the group:')+groupname+'\n\n\n' + content + _('\n Or you can go to the group page to view the new notes! ')+ \
                  group_url + '\n\n'+_('You can set up how you want to receive group digest in your setting:')+ site_name + '/settings/'
        print 'digest is:', digest
        
        mailserver = get_mail_server()
        sendEmail(mailserver , SERVER_EMAIL, [member.email], (_('Group ')+groupname+_(":today's new notes!")).encode('utf-8'), digest.encode('utf-8'))
        mailserver.close()
        print 'Email digest was sent to '+member.email+' for group '+ groupname 
   
    

def send_daily_digest(username):
    print 'Sending digetst for user:', username
    member = Member.objects.get(username=username)
    #print 'Getting groups for member:', member.username
    groups = member.get_groups()
    #print username, "'s groups:", groups
    for group in groups:
        send_group_daily_digest(username, group.name)
    




if __name__ == "__main__":
    users = User.objects.all()
    for user in users:
        try:
            send_daily_digest(user.username)   
        except:
             pass            
  
