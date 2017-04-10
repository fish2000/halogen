
from __future__ import print_function

from unittest2 import TestCase
import sys
from os.path import abspath, dirname, isdir

class BaseCase(TestCase):
    
    whereat = abspath(dirname(dirname(__file__)))
    
    def setUp(self):
        sys.path.append(self.whereat)
        import hal.api
        setattr(self, 'hal', hal)
    
    def tearDown(self):
        from halogen.filesystem import rm_rf
        if isdir('/tmp/yodogg'):
            rm_rf('/tmp/yodogg')

