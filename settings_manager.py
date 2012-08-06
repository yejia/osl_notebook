#!/usr/bin/env python

import os

from settings import DATABASES
from env_settings import path_to_store_settings




for fname in os.listdir(path_to_store_settings):
    full_path = os.path.join(path_to_store_settings, fname)
    f = open(full_path)
    content = f.read()
    f.close()
    exec(content) #watch out for what content is put there
