#!/usr/bin/env python

import os, sys
from django.core.management import execute_manager

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")



try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)



from django.utils.translation import ugettext_noop as _
from django.db.models import signals



if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("friends_invite", _("Invitation Received"), _("you have received an invitation"))
        notification.create_notice_type("friends_accept", _("Acceptance Received"), _("an invitation you sent has been accepted"))
        notification.create_notice_type("comment_receive", _("Comment Received"), _("you have received a comment"))
        notification.create_notice_type("mentioned", _("Mentioned"), _("You have been mentioned"))
        #so far, people can add friends without being approved
        notification.create_notice_type("friends_add", _("Friend Added"), _("Someone added you as a friend")) 
        

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"




if __name__ == "__main__":
    execute_manager(settings)


