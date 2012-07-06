ALL_VAR = 'all'
true_words = [True, 'True', 'true', 'Yes', 'yes', 'Y', 'y']
false_words = [False, 'False', 'false', 'No', 'no', 'N', 'n']
#TODO: not used
sort_dict = {'vote':'Vote', 'title':'Title', 'desc': 'Desc', 'init_date': 'Creation Date', 
             'last_modi_date':'Last Modification Date'}

books = ['notebook', 'snippetbook','bookmarkbook', 'scrapbook', 'framebook']
book_template_dict = {'notebook':'notebook/', 'snippetbook':'snippetbook/','bookmarkbook':'bookmarkbook/', 'scrapbook': 'scrapbook/','framebook': 'framebook/'}


model_book_dict = {'Note':'notebook', 'Snippet':'snippetbook','Bookmark':'bookmarkbook', 'Scrap':'scrapbook', 'Frame':'framebook'}
search_fields_dict = {'notebook':('title','desc'), 'snippetbook':('title','desc'), 'bookmarkbook':('title','desc', 'url'), \
                      'scrapbook':('title','desc', 'url'),'framebook':('title','desc')}

