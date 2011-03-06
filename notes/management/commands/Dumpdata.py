#!/usr/bin/env python
from optparse import make_option

from django.core.management.commands.dumpdata import Command as Dumpdata

class Command(Dumpdata):
    option_list = Dumpdata.option_list + (
        make_option('--pretty', default=False, action='store_true', 
            dest='pretty', help='Avoid unicode escape symbols'
        ),
    )
    
    def handle(self, *args, **kwargs):
        data = super(Command, self).handle(*args, **kwargs)
        if kwargs.get('pretty'):
            data = data.decode("unicode_escape").encode("utf8")
        return data
