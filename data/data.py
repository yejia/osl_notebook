# -*- coding: utf-8 -*-

from notebook.social.models import Group as G, Social_Tag as ST, Member
from notebook.notes.models import Tag as T, getW, getT


def create_group(name, tag_names, creator_name, desc='', private=False):
    if not name:
        raise Exception('No group name given!')
    if not tag_names:
        raise Exception('No tags given!')
    if not creator_name:
        raise Exception('No creator given!')
    creator = Member.objects.get(username = creator_name)    
    #should the creator be added to admin automatically? TODO:
    #g.admins.add(creator)
    #g.members.add(creator)
    g, created = G.objects.get_or_create(name = name, creator = creator) 
    if not created:
        raise Exception('Group with that name already exist for this user!') 
    #If tag doesn't exist yet, it will be created.
    tag_ids = [ST.objects.get_or_create(name=tag_name)[0].id for tag_name in tag_names]
    g.private = private
    g.desc = desc
    g.creator = creator
    g.save()            
    g.tags = tag_ids
    gtn = "sharinggroup:"+g.name 
    st, created = ST.objects.get_or_create(name=gtn, private=g.private)        
    g.tags.add(st)
    push_group_tags_back(g, creator_name)



def push_group_tags_back(g, username):
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
        #It is a little messy here. The logic here is that for private
        #group, the tags it pushes back to the use space should be private 
        #as well. Then when user save their notes with that tag, the social
        #note will be private.
        if g.private:
            t.private = True   
        t.save()     
        w1.tags.add(t) 
        w2.tags.add(t) 
        w3.tags.add(t) 
        w.tags.add(t)
    return g


def push_tag_back(tagname, member):
    pass


def add_tags(g, new_tags):    
    #need to push new tags to every group member's database
    all_members = list(g.members.values_list('username', flat=True))
    all_members.extend(list(g.admins.values_list('username', flat=True)))
    all_members.append(g.creator.username)
    all_members = list(set(all_members))
    for tag_name in new_tags:
        if tag_name not in g.get_tag_names():
            t, created = ST.objects.get_or_create(name=tag_name)
            g.tags.add(t)        
            for m in all_members:
                T = getT(m)
                t, created = T.objects.get_or_create(name=t.name)
                W = getW(m)
                w1  = W.objects.get(name='snippetbook')    
                w2  = W.objects.get(name='bookmarkbook')   
                w3  = W.objects.get(name='scrapbook')
                w  = W.objects.get(name="sharinggroup:"+g.name)
                w1.tags.add(t) 
                w2.tags.add(t) 
                w3.tags.add(t) 
                w.tags.add(t)



def remove_tags(g, tags_to_remove):
    for t in tags_to_remove:
       if t in g.get_tag_names():
           tag = ST.objects.get(name=t)
           g.tags.remove(tag)



        

def join_group(groupname, username):
    if not groupname:
        raise Exception('No group name given!')
    if not username:
        raise Exception('No user name given!')    
    m = Member.objects.get(username = username)
    g = G.objects.get(name=groupname)
    g.members.add(m)
    g.save()
    push_group_tags_back(g, username)


def remove_group_member(groupname, adminname, username):
    g = G.objects.get(name=groupname)
    admin = Member.objects.get(username=adminname)
    m = Member.objects.get(username=username)
    if admin in g.admins.all() or admin == g.creator:
        g.members.remove(m)
    else:
        raise Exception('You have no permission!')  


def delete_group(groupname, username):
    if not groupname:
        raise Exception('No group name given!')
    if not username:
        raise Exception('No user name given!')  
    m = Member.objects.get(username=username)
    g = G.objects.get(name=groupname)
    if m in g.admins.all()  or m == g.creator:
        g.delete()
        #TODO:what to return?
        return True
    else:
        raise Exception('You have no permission!')          