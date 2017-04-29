import logging
import logging.handlers
import logging.config
import os

#print os.path._getfullpathname('.')

logging.config.fileConfig("../config/logger.conf")

LOG = logging.getLogger('default')
