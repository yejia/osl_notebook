# -*- coding: utf-8 -*-

from notebook.social.models import Group as G, Social_Tag as ST, Member
from notebook.notes.models import Tag as T, getW, getT


def create_group(name, tag_ids, creator_name, desc='', private=False):
    if not name:
        raise Exception('No name given!')
    if not tag_ids:
        raise Exception('No tags given!')
    if not creator_name:
        raise Exception('No creator given!')
    creator = Member.objects.get(username = creator_name)    
    g, created = G.objects.get_or_create(name = 'test_maniacs', creator = creator) 
    if not created:
        raise Exception('Group with that name already exist for this user!') 
    g.private = private
    g.desc = desc
    g.creator = creator
    g.save()            
    g.tags = tag_ids
    gtn = "sharinggroup:"+g.name 
    st, created = ST.objects.get_or_create(name=gtn, private=g.private)        
    g.tags.add(st)
    #push_group_tags_back
    T = getT(creator_name)    
    sts = g.tags.all()
    W = getW(creator_name)
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
        

     