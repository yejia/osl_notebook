#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from email.MIMEText import MIMEText
import smtplib
import time
import datetime
from datetime import date

from django.core.mail import EmailMultiAlternatives


from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)

from settings import EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, SERVER_EMAIL, EMAIL_USE_TLS

from django.utils.translation import ugettext as _ , activate, get_language

from django.contrib.auth.models import User
from django.utils.http import urlquote


from notebook.social.models import   Member
from notebook.notes.util import  getFrame, getNoteTranslation

#later use user time zone to pick the right site name for user
site_name = 'http://www.91biji.com'




def create_weekly_plan(user):
    now = date.today()
    one_week_later = now + datetime.timedelta(days=6)
    f, created =getFrame(user).objects.get_or_create(title='Weekly Plan:'+now.strftime('%Y-%m-%d')+' to ' + one_week_later.strftime('%Y-%m-%d'))
    #if created:
    f.owner_name =  user
    f.desc = 'Make your weekly plan for this week here.'
    f.save()
    f_trans, trans_created = getNoteTranslation(user).objects.get_or_create(note=f)
    f_trans.owner_name = user
    f_trans.lang = 'C'
    f_trans.original_lang = 'E'
    f_trans.title = _('Weekly Plan:')+now.strftime('%Y-%m-%d')+_(' to ') + one_week_later.strftime('%Y-%m-%d')
    f_trans.desc = _('Make your weekly plan for this week here.')
    f_trans.save()
    #to push the translation to the social notebook as well
    f.save()
    return f.id     
   

def create_monthly_plan(user):
    now = date.today()
    f, created =getFrame(user).objects.get_or_create(title='Monthly Plan:'+ now.strftime('%Y-%m'))
    f.owner_name =  user
    f.desc = 'Make your monthly plan for this month here.'
    f.save()
    f_trans, trans_created = getNoteTranslation(user).objects.get_or_create(note=f)
    f_trans.owner_name = user
    f_trans.lang = 'C'
    f_trans.original_lang = 'E'
    f_trans.title = _('Monthly Plan:')+now.strftime('%Y-%m')
    f_trans.desc = _('Make your monthly plan for this month here.')
    f_trans.save()
    #to push the translation to the social notebook as well
    f.save()
    return f.id                                                  
    
 
 

def  email_weekly_plan_notice(user, user_frame_id):
    member = Member.objects.get(username=user)
    pick_lang = 'zh-cn'
    if member.default_lang:        
         pick_lang = member.default_lang    
         activate(pick_lang)
         
    frame_url = site_name + '/' + member.username + '/framebook/notes/note/' + str(user_frame_id) + '/'   
    content = _('It is the beginning of the week again. To start this week right, first make a learning plan for this week. What do you want to learn this week? And how are you going to learn them?')+'\n'+\
               _('A weekly plan has been created for you in your notebook. You just need to fill in the specifics by adding snippets to it:') + '\n' + \
                frame_url
    
    html_content =  _('It is the beginning of the week again. To start this week right, first make a learning plan for this week. What do you want to learn this week? And how are you going to learn them?')+'<br/>'+\
               _('A weekly plan has been created for you in your notebook. You just need to fill in the specifics by adding snippets to it:') + '<br/>' + \
               '<a href="' + frame_url +'">' + frame_url + '</a>'

 
    
    msg = EmailMultiAlternatives(_('Time to make your weekly plan'), content.encode('utf-8') , SERVER_EMAIL, [member.email])
    msg.attach_alternative(html_content.encode('utf-8') , "text/html")
    msg.send()
    print 'email was sent to user',user,' for weekly plan.'
    time.sleep(10)
    


#TODO: refactor and merge
def email_monthly_plan_notice(user, user_frame_id):
    member = Member.objects.get(username=user)
    pick_lang = 'zh-cn'
    if member.default_lang:        
         pick_lang = member.default_lang    
         activate(pick_lang)
         
    frame_url = site_name + '/' + member.username + '/framebook/notes/note/' + str(user_frame_id) + '/' 
    content = _('It is the beginning of the month again. To start this month right, first make a learning plan for this month. What do you want to learn this month? And how are you going to learn them?')+'\n'+\
               _('A monthly plan has been created for you in your notebook. You just need to fill in the specifics by adding snippets to it:') + '\n' + \
                frame_url
    
    html_content =  _('It is the beginning of the month again. To start this month right, first make a learning plan for this month. What do you want to learn this month? And how are you going to learn them?')+'<br/>'+\
               _('A monthly plan has been created for you in your notebook. You just need to fill in the specifics by adding snippets to it:') + '<br/>' + \
               '<a href="' + frame_url +'">' + frame_url + '</a>'

 
    
    msg = EmailMultiAlternatives(_('Time to make your monthly plan'), content.encode('utf-8') , SERVER_EMAIL, [member.email])
    msg.attach_alternative(html_content.encode('utf-8') , "text/html")
    msg.send()
    print 'email was sent to user',user,' for monthly plan.'
    time.sleep(10)
    
    


def make_weekly_plan(users):    
    for user in users:
        try:
            user_frame_id = create_weekly_plan(user)   
            #have to send the email one by one to each member since each member might have different language preference 
            email_weekly_plan_notice(user, user_frame_id) 
        except:
            print sys.exc_info()       


def make_monthly_plan(users):    
    for user in users:
        try:
            user_frame_id = create_monthly_plan(user)
            email_monthly_plan_notice(user, user_frame_id) 
        except:
            print sys.exc_info()      



def remind_weekly_review(users):
    now = date.today()
    #TODO:check if 5 is correct for US time.
    this_monday = now - datetime.timedelta(days=5)
    
    #print 'monday_this_week','Weekly Plan:'+this_monday.strftime('%Y-%m-%d')+' to '
    
    for user in users:
        try:
            f =getFrame(user).objects.get(title__startswith='Weekly Plan:'+this_monday.strftime('%Y-%m-%d')+' to ')
            member = Member.objects.get(username=user)
            pick_lang = 'zh-cn'
            if member.default_lang:        
                 pick_lang = member.default_lang    
                 activate(pick_lang) 
            
            frame_url = site_name + '/' + member.username + '/framebook/notes/note/' + str(f.id) + '/'   
            content = _("It is the weekend again. Now is your time to review your weekly plan. Have you accomplished your plan this week? What have you done well? What you haven't done very well? What can you improve on? ")+'\n'+\
                    _("Remember to find time on the weekend to review your weekly plan:") + '\n' + \
                    frame_url + '\n\n' + \
                    _("If your weekly plan is empty this week, it will be removed for you automatically the beginning of next week:") 
            html_content =  _("It is the weekend again. Now is your time to review your weekly plan. Have you accomplished your plan this week? What have you done well? What you haven't done very well? What can you improve on? ")+'<br/>'+\
                    _("Remember to find time on the weekend to review your weekly plan:") + '<br/>' + \
                    '<a href="' + frame_url +'">' + frame_url + '</a>' + '<br/><br/>' + \
                    _("If your weekly plan is empty this week, it will be removed for you automatically the beginning of next week:")
            msg = EmailMultiAlternatives(_('Time to review your weekly plan'), content.encode('utf-8') , SERVER_EMAIL, [member.email])
            msg.attach_alternative(html_content.encode('utf-8') , "text/html")
            msg.send()
            print 'email was sent to user',user,' for weekly plan review.'
            time.sleep(10)       
        except:
            print sys.exc_info()  
            #print type(inst)
            #print inst.args
            #print inst    
             
                
 
def remind_monthly_review(users):
    now = date.today()
      
    for user in users:
        try:
            f =getFrame(user).objects.get(title__startswith='Monthly Plan:'+now.strftime('%Y-%m'))
            member = Member.objects.get(username=user)
            pick_lang = 'zh-cn'
            if member.default_lang:        
                 pick_lang = member.default_lang    
                 activate(pick_lang) 
            
            frame_url = site_name + '/' + member.username + '/framebook/notes/note/' + str(f.id) + '/'   
            content = _("It is the end of the month again. Now is your time to review your monthly plan. Have you accomplished your plan this month? What have you done well? What you haven't done very well? What can you improve on? ")+'\n'+\
                    _("Remember to find time to review your monthly plan:") + '\n' + \
                    frame_url+ '\n\n'+\
                    _("If your monthly plan is empty this month, it will be removed for you automatically the beginning of next month:") 
            html_content =  _("It is the end of the month again. Now is your time to review your monthly plan. Have you accomplished your plan this month? What have you done well? What you haven't done very well? What can you improve on? ")+'<br/>'+\
                    _("Remember to find time to review your monthly plan:") + '<br/>' + \
                    '<a href="' + frame_url +'">' + frame_url + '</a>' + '<br/>br/>' + \
                    _("If your monthly plan is empty this month, it will be removed for you automatically the beginning of next month:") 
            msg = EmailMultiAlternatives(_('Time to review your monthly plan'), content.encode('utf-8') , SERVER_EMAIL, [member.email])
            msg.attach_alternative(html_content.encode('utf-8') , "text/html")
            msg.send()
            print 'email was sent to user',user,' for monthly plan review.'
            time.sleep(10)       
        except Exception as inst:
            print sys.exc_info()  
   

#TODO:clean up empty weekly plans and monthly plans at the end of the week/month
def clean_up_weekly_plans(users):       
    now = date.today()
    last_monday = now - datetime.timedelta(days=7)
    for user in users:
        print 'Cleanup weekly plans for user', user 
        try:
            #get weekly plans of this month
            #assume that no one will change the init_date of the plan, or disallow changing of that for plans TODO:
            #also assume that no one will change the plan title or disallow that  TODO:
          
            #update(deleted=True) will remove it from the social space first            
            empty_plans = getFrame(user).objects.filter(title__startswith='Weekly Plan:', init_date__lte=last_monday.strftime('%Y-%m-%d'), notes=None)
            empty_plans.update(deleted=True)
            #call save to remove from social space
            for p in empty_plans:
                p.save()
            empty_plans.delete()
            #print fs
            print 'Empty weekly plans are removed for user', user            
        except:
            print sys.exc_info()      
                 
                 
                 
def clean_up_monthly_plans(users):       
    now = date.today()
    #at least 28 should be enough
    last_month_date = now - datetime.timedelta(days=28)
    for user in users:
        print 'Cleanup monthly plans for user', user 
        try:
            #get weekly plans of this month
            #assume that no one will change the init_date of the plan, or disallow changing of that for plans TODO:
            #also assume that no one will change the plan title or disallow that  TODO:
            empty_plans = getFrame(user).objects.filter(title__startswith='Monthly Plan:', init_date__lte=last_month_date.strftime('%Y-%m-%d'), notes=None)
            empty_plans.update(deleted=True)
            for p in empty_plans:
                p.save()
            
            empty_plans.delete()
            print 'Empty monthly plans are removed for user', user            
        except:
            print sys.exc_info()   

    

if __name__ == "__main__":
    command = sys.argv[1]
    users = sys.argv[2:]
    if not users:
        users = [u.username for u in User.objects.all()]
    if command == 'weekly':
        make_weekly_plan(users)
    if command == 'monthly':
        make_monthly_plan(users) 
    if command == 'weekly_review':
        remind_weekly_review(users)   
    if command == 'monthly_review':
        remind_monthly_review(users) 
    if command == 'cleanup_weekly':
        clean_up_weekly_plans(users)   
    if command == 'cleanup_monthly':
        clean_up_monthly_plans(users)         
