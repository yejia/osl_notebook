#!/usr/bin/env python


import sys, os


from env_settings import HOME_PATH

sys.path.append(HOME_PATH)

from django.core import management; import notebook; import notebook.settings as settings;management.setup_environ(settings)
from django.contrib.auth.models import User

from notebook.areas.models import Area, getArea
from notebook.social.models import Social_Area




if __name__ == "__main__":
    users = [u for u in User.objects.all()]
    for user in users:
        try:
            print 'Get areas of user:', user.username 
            areas = Area.objects.using(user.username).filter(private=False) 
            for area in areas:                
                area.owner_name = user.username
                sa, created = Social_Area.objects.get_or_create(owner=user.member, name=area.name, owner_area_id = area.id)                
                sa.desc = area.desc
                sa.area_tags = ','.join(area.get_all_tags())
                sa.num_of_notes = area.get_public_notes().count()
                sa.save()              
        except:
            print sys.exc_info()          