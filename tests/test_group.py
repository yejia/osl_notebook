# -*- coding: utf-8 -*-
import os
import unittest

import requests
from nose.tools import nottest, istest, raises, eq_, ok_

from notebook.social.models import Group as G, Social_Tag as ST, Member
from notebook.notes.models import Tag as T, getW, getT 

from notebook.data import *




class TestPrivateGroup(unittest.TestCase):
    pass


class TestGroup(unittest.TestCase):
    def setUp(self):
        print 'test_mode:', os.environ['TEST_MODE']
        
        #create a unittest member first
        m, created = Member.objects.get_or_create(username='unittest')
        g, created = G.objects.get_or_create(name = 'test_maniacs')        
        g.private = False
        g.creator = m
        g.save()
        tag_names = ['testing', 'framework', 'philosophy']
        tag_ids = [ST.objects.get_or_create(name=tag_name)[0].id for tag_name in tag_names]
        g.tags = tag_ids
        gtn = "sharinggroup:"+g.name 
        st, created = ST.objects.get_or_create(name=gtn, private=g.private)        
        g.tags.add(st)
        
    #push_group_tags_back
        username = 'unittest'
        T = getT(username)
        
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
            
            
    def testCreateGroup(self):  
        g = G.objects.get(name='test_maniacs')
        eq_(g.name, 'test_maniacs')
        eq_(g.private, False)
        eq_(g.get_tag_names(), ['framework', 'philosophy', 'sharinggroup:test_maniacs', 'testing'])
        username = 'unittest'
        T = getT('unittest')
        W = getW('unittest')
        w1 = W.objects.get(name='snippetbook') 
        eq_(w1.name, 'snippetbook')
        w2 = W.objects.get(name='bookmarkbook') 
        eq_(w2.name, 'bookmarkbook')
        w3 = W.objects.get(name='scrapbook') 
        eq_(w3.name, 'scrapbook')
        w = W.objects.get(name="sharinggroup:"+g.name) 
        eq_(w.name, "sharinggroup:"+g.name)
        
        for st in ['testing', 'framework', 'philosophy']:
            t = T.objects.get(name=st)
            eq_(t.name, st)
            eq_(t.private, False)
            eq_(t.name in w1.display_tags().split(','), True)
            
    @nottest
    def testUpdateGroup(self):
        g = G.objects.get(name='test_maniacs')
        g.name = 'test_maniacs_changed'
        g.desc = 'A learning group for those crazy about test.'
        
        
    def testJoiningGroup(self):
        pass
    
    
        
    
    @nottest
    def testDeleteGroup(self):
        pass
    
    
    
    def tearDown(self):  
        print "clearing groups..."   
        G.objects.all().delete()
        print "clearning social tags..."
        ST.objects.all().delete()
        #TODO:St seems not cleared
        T = getT('unittest')
        T.objects.all().delete()
        
             
