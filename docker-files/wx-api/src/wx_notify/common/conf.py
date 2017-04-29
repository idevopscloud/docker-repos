#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import ConfigParser

CONF = ConfigParser.ConfigParser()

# allow entry in anywhere
files = ["../config/wx_api.conf", "../../config/wx_api.conf",
         "../../../config/wx_api.conf", "./config/wx_api.conf"]
for file_name in files:
    if os.path.isfile(file_name):
        CONF.read(file_name)
        break
else:
    print "Can not find config file, system exit."
    sys.exit()
