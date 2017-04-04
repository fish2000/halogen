
from __future__ import print_function

import os, sys
from basecase import BaseCase

HORIZONTAL_RULE_WIDTH = 120
    
def print_config(conf):
    print("INCLUDES:")
    print("")
    print(conf.get_includes())
    print("")
    print("-" * HORIZONTAL_RULE_WIDTH)
    
    print("LIBS:")
    print("")
    print(conf.get_libs())
    print("")
    print("-" * HORIZONTAL_RULE_WIDTH)
    
    print("CFLAGS:")
    print("")
    print(conf.get_cflags())
    print("")
    print("-" * HORIZONTAL_RULE_WIDTH)
    
    print("LDFLAGS:")
    print("")
    print(conf.get_ldflags())
    print("")
    # print("-" * HORIZONTAL_RULE_WIDTH)

class ConfigTesticles(BaseCase):
    
    def setUp(self):
        super(ConfigTesticles, self).setUp()
        from halogen.compile import CONF
        self.conf = CONF
    
    def test_compile(self):
        # import shutil
        from tempfile import mktemp
        from halogen.filesystem import NamedTemporaryFile
        from halogen.config import test_generator_source, CXX
        output = tuple()
        px = "yodogg-"
        with NamedTemporaryFile(suffix="cpp", prefix=px) as tf:
            tf.file.write(test_generator_source)
            tf.file.flush()
            adotout = mktemp(suffix=".cpp.o", prefix=px)
            
            # print("C++ SOURCE: %s" % tf.name)
            # print("C++ TARGET: %s" % adotout)
            
            output += CXX(self.conf, adotout, tf.name, verbose=True)
            
            # print("-" * HORIZONTAL_RULE_WIDTH)
            
            self.assertTrue(len(output[1]) <= 0)
            
            if len(output[1]) > 0:
                # failure
                print("COMPILATION FAILED:")
                print(output[0], file=sys.stdout)
                print(output[1], file=sys.stderr)
                if os.path.exists(adotout):
                    os.unlink(adotout)
                return
            
            # success!
            # print("COMPILATION TOTALLY WORKED!")
            # print(output[0], file=sys.stdout)
            # print(output[1], file=sys.stderr)
            if os.path.exists(adotout):
                # another = os.path.basename(mktemp(suffix=".cpp.o", prefix=px))
                # shutil.copy2(adotout, "/tmp/%s" % another)
                os.unlink(adotout)
                self.assertFalse(os.path.exists(adotout))
            else:
                print("... BUT THEN WHERE THE FUCK IS MY SHIT?!?!")
    
    