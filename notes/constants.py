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

resource_tags = ['resources', 'movie', 'movies', 'video', 'tutorial', 'reading', 'mag', 'book', 'books', 'news', 'great', 'greatest', 'people', 'examples',
                'blog','blogs', 'top news reading', u'新闻阅读评论', ]

system_tags = resource_tags + ['question',                
               'task', 'errand', 'todo', 'todos', 'toread', 'totry', 'daily', 'weekly', 'monthly', 'plan',
               'chinese', 'tech']

notebook_host_names = ['www.91biji.com', '91biji.com', 'opensourcelearning.org', 'www.opensourcelearning.org', '3exps.org', '3exps.com', 'www.3exps.org', 'www.3exps.com']
