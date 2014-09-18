#! /bin/sh

#assume executing this script from the current directory (scripts/). For now, not accepting params. TODO
#TODO: remove backup files as well (those end with ~)

find ../ -name '.?*'  -exec rm -rf {} \;

