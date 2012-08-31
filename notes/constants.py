# -*- coding: utf-8 -*-

ALL_VAR = 'all'
true_words = [True, 'True', 'true', 'Yes', 'yes', 'Y', 'y']
false_words = [False, 'False', 'false', 'No', 'no', 'N', 'n']
all_words = ['All', 'all']

#TODO: not used
sort_dict = {'vote':'Vote', 'title':'Title', 'desc': 'Desc', 'init_date': 'Creation Date', 
             'last_modi_date':'Last Modification Date'}

books = ['notebook', 'snippetbook','bookmarkbook', 'scrapbook', 'framebook']
book_template_dict = {'notebook':'notebook/', 'snippetbook':'snippetbook/','bookmarkbook':'bookmarkbook/', 'scrapbook': 'scrapbook/','framebook': 'framebook/'}


model_book_dict = {'Note':'notebook', 'Snippet':'snippetbook','Bookmark':'bookmarkbook', 'Scrap':'scrapbook', 'Frame':'framebook'}
search_fields_dict = {'notebook':('title','desc'), 'snippetbook':('title','desc'), 'bookmarkbook':('title','desc', 'url'), \
                      'scrapbook':('title','desc', 'url'),'framebook':('title','desc')}

bookname_note_type_dict = {'notebook':'Note', 'snippetbook':'Snippet','bookmarkbook':'Bookmark', 'scrapbook': 'Scrap','framebook': 'Frame'}

resource_tags = [u'resources', u'movie', u'movies', u'video', u'tutorial', u'reading', u'mag', u'book', u'books', u'news', u'great', u'greatest', u'people',
                u'blog',u'blogs', u'top news reading', u'新闻阅读评论', ]

system_tags = resource_tags + [u'question',                
               u'task', u'errand', u'todo', u'todos', u'toread', u'totry', u'daily', u'weekly', u'monthly', u'plan',
               u'chinese', u'tech']

