#!/usr/bin/env python

import sys

from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from notebook.social.models import  Member



if __name__ == "__main__":    
    members = Member.objects.all()
    email_list = [m.email for m in members if m.email]
    emails = ','.join(email_list)
    print emails


