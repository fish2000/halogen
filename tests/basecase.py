
from __future__ import print_function

from unittest2 import TestCase
import sys
# from os import listdir
# from os.path import join, abspath, expanduser, dirname, basename
# from collections import namedtuple

from os.path import abspath, dirname

class BaseCase(TestCase):
    
    whereat = abspath(dirname(dirname(__file__)))
    
    def setUp(self):
        sys.path.append(self.whereat)
        import hal.api
        setattr(self, 'hal', hal)
    
    def tearDown(self):
        pass

