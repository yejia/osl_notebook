# -*- coding: utf-8 -*-

import notebook

from notebook.notes.models import Note, Tag, Frame, LinkageNote, Folder, WorkingSet, create_model, create_model_form, getNC, getT, getL
from notebook.snippets.models import Snippet
from notebook.bookmarks.models import Bookmark
from notebook.scraps.models import Scrap
from notebook.social.models import Social_Note, Social_Snippet, Social_Bookmark, Social_Scrap, Social_Frame



book_model_dict = {'notebook':Note, 'snippetbook':Snippet,'bookmarkbook':Bookmark, 'scrapbook': Scrap, 'framebook':Frame}
book_folder_dict = {'notebook':Folder, 'snippetbook':notebook.snippets.models.Snippet_Folder,'bookmarkbook':notebook.bookmarks.models.Bookmark_Folder,\
                     'scrapbook': notebook.scraps.models.Scrap_Folder, 'framebook': notebook.notes.models.Frame_Folder}#TODO:implement folders for frame?
book_cache_dict = {'notebook':notebook.notes.models.Cache, 'snippetbook':notebook.snippets.models.Snippet_Cache,'bookmarkbook':notebook.bookmarks.models.Bookmark_Cache, 'scrapbook': notebook.scraps.models.Scrap_Cache, 'framebook': notebook.notes.models.Frame_Cache}
book_entry_dict = {'notebook':'', 'snippetbook':'__snippet','bookmarkbook':'__bookmark', 'scrapbook': '__scrap'}

def getNote(username, bookname):
    return create_model("Note_"+str(bookname)+"_"+str(username), book_model_dict.get(bookname), username) 

def getFolder(username, bookname):
    return create_model("Folder_"+str(bookname)+"_"+str(username), book_folder_dict.get(bookname), username) 

def getCache(username, bookname):
    return create_model("Cache_"+str(bookname)+"_"+str(username), book_cache_dict.get(bookname), username)    





from notebook.bookmarks.models import Linkage_Of_Bookmark
from notebook.scraps.models import Linkage_Of_Scrap
from notebook.snippets.models import Linkage_Of_Snippet
book_linkage_dict = {'notebook': LinkageNote,'snippetbook': Linkage_Of_Snippet, 'bookmarkbook': Linkage_Of_Bookmark, 'scrapbook':Linkage_Of_Scrap}

def getLinkage(username, bookname):
    return create_model("Linkage_"+str(bookname)+"_"+str(username), book_linkage_dict.get(bookname), username) 


from notebook.notes.models import Frame
def getFrame(username):
    return create_model("Frame_"+str(username), Frame, username) 

from notebook.notes.models import Note_Translation
def getNoteTranslation(username):
    return create_model("Note_Trans_"+str(username), Note_Translation, username) 

from notebook.tags.models import Tag_Frame
def getTagFrame(username):
    return create_model("Tag_Frame"+str(username), Tag_Frame, username) 

from notebook.tags.models import Frame_Tags
def getFrameTags(username):
    return create_model("Frame_Tags"+str(username), Frame_Tags, username) 




