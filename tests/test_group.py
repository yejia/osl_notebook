# -*- coding: utf-8 -*-
import os
import unittest

import requests
from nose.tools import nottest, istest, raises, eq_, ok_, assert_in, assert_not_in, assert_raises

import django

from notebook.social.models import Group as G, Social_Tag as ST, Member
from notebook.notes.models import Tag as T, getW, getT 

from notebook.data.data import *




class TestPrivateGroup(unittest.TestCase):
    pass


class TestGroup(unittest.TestCase):
    def setUp(self):
        self.tearDown()
        print 'test_mode:', os.environ['TEST_MODE']    
        self.name = 'unittest'    
        #create a unittest member first
        creator_name = self.name
        m, created = Member.objects.get_or_create(username=self.name)
        groupname = 'test_maniacs'          
        tag_names = ['testing', 'framework', 'philosophy']
        tag_ids = [ST.objects.get_or_create(name=tag_name)[0].id for tag_name in tag_names]
        self.group = create_group(groupname, tag_ids, creator_name, private=False)

            
    def testCreateGroup(self):  
        g = G.objects.get(name='test_maniacs')
        eq_(g.name, 'test_maniacs')
        eq_(g.private, False)
        eq_(g.get_tag_names(), ['framework', 'philosophy', 'sharinggroup:test_maniacs', 'testing'])        
        T = getT(self.name)
        W = getW(self.name)
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
            
    
    def testUpdateGroup(self):
        g1 = G.objects.get(name='test_maniacs')
        g1.name = 'test_maniacs_changed'
        g1.desc = 'A learning group for those crazy about test.'
        #TODO:test add tags
        g1.save()
        g2 = G.objects.get(name='test_maniacs_changed')        
        eq_(g2.desc, 'A learning group for those crazy about test.')


    def testAddGroupTags(self):
        g1 = G.objects.get(name='test_maniacs')
        self.testJoinGroup()
        add_tags(g1, ['functional test', 'performance test'])
        assert_in('functional test', g1.get_tag_names())
        assert_in('performance test', g1.get_tag_names())
        T1 = getT('unittest')
        T2 = getT('unittest2')
        for T in [T1, T2]:            
            T.objects.get(name='functional test')
            T.objects.get(name='performance test')


    def testRemoveGroupTags(self):
        g1 = G.objects.get(name='test_maniacs')
        self.testJoinGroup()
        self.testAddGroupTags()
        remove_tags(g1, ['functional test', 'performance test'])
        assert_not_in('functional test', g1.get_tag_names())
        assert_not_in('performance test', g1.get_tag_names())
        
            

        
    def testJoinGroup(self):
        username2 = 'unittest2'
        m, created = Member.objects.get_or_create(username=username2)
        join_group('test_maniacs', username2)
        g = G.objects.get(name='test_maniacs')        
        assert_in(m, g.members.all())
        sts = g.tags.all()
        T = getT('unittest2')        
        for st in sts:
            T.objects.get(name=st.name)

        
    @raises(django.core.exceptions.ObjectDoesNotExist)
    def testDeleteGroup(self):
        g1 = G.objects.get(name='test_maniacs')
        username2 = 'unittest2'
        m, created = Member.objects.get_or_create(username=username2)        
        #TODO: how to check the error msg?
        assert_raises(Exception, delete_group, g1, 'unittest2')
        #delete a group as the creator
        result = delete_group(g1, 'unittest')
        eq_(result, True) 
        #add a user as admin
        self.setUp()
        self.testAddAdmin()
        result = delete_group(g1, 'unittest3')
        eq_(result, True)
        g1 = G.objects.get(name='test_maniacs')
        

    def testAddAdmin(self):
        g1 = G.objects.get(name='test_maniacs')
        m, created = Member.objects.get_or_create(username='unittest3')
        g1.admins.add(m)
        g1.save()        
        assert_in(m, g1.admins.all())
    
    
    def testRemoveMember(self):
        self.testJoinGroup()        
        remove_group_member('test_maniacs', 'unittest', 'unittest2')
        g = G.objects.get(name='test_maniacs')
        assert_not_in('unittest2', g.members.all())     
    
    
    
    def tearDown(self):  
        print "clearing groups..."   
        G.objects.all().delete()
        print "clearning social tags..."
        ST.objects.all().delete()
        #TODO:St seems not cleared
        T = getT('unittest')
        T.objects.all().delete()
        T2 = getT('unittest2')
        T2.objects.all().delete()
        
             
