
from __future__ import print_function

from basecase import BaseCase

class ConfigTests(BaseCase):
    
    def setUp(self):
        super(ConfigTests, self).setUp()
    
    def test_pythonconfig(self):
        from halogen.filesystem import back_tick
        from halogen.config import PythonConfig
        conf = PythonConfig()
        
        self.assertEqual('/usr/local/bin',          conf.bin())
        self.assertEqual('/usr/local/include',      conf.include())
        self.assertEqual('/usr/local/lib',          conf.lib())
        self.assertEqual('/usr/local/lib',          conf.libexec())
        self.assertEqual('/usr/local/share',        conf.share())
        
        self.assertEqual('/usr/local/Frameworks',   conf.Frameworks())
        # self.assertEqual('/usr/local/Headers',      conf.Headers())
        # self.assertEqual('/usr/local/Resources',    conf.Resources())
        self.assertEqual(None,                      conf.Headers())
        self.assertEqual(None,                      conf.Resources())
        
        self.assertEqual(back_tick('/usr/local/bin/python-config --includes'),                  conf.get_includes())
        self.assertEqual(back_tick('/usr/local/bin/python-config --libs'),                      conf.get_libs())
        self.assertEqual(back_tick('/usr/local/bin/python-config --cflags'),                    conf.get_cflags())
        self.assertEqual(back_tick('/usr/local/bin/python-config --ldflags'),                   conf.get_ldflags())
    
    def test_brewedpythonconfig(self):
        from sys import version_info
        from halogen.filesystem import back_tick
        from halogen.config import BrewedPythonConfig
        conf = BrewedPythonConfig()
        
        py_v = "%(major)s.%(minor)s" % dict(major=version_info.major,
                                            minor=version_info.minor)
        
        self.assertEqual('/usr/local/bin',                                                              conf.bin())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Headers',                   conf.include())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Versions/%s/lib' % py_v,    conf.lib())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Versions/%s/lib' % py_v,    conf.libexec())
        self.assertEqual('/usr/local/share',                                                            conf.share())
        
        self.assertEqual('/usr/local/Frameworks',   conf.Frameworks())
        # self.assertEqual('/usr/local/Headers',      conf.Headers())
        # self.assertEqual('/usr/local/Resources',    conf.Resources())
        self.assertEqual(None,                      conf.Headers())
        self.assertEqual(None,                      conf.Resources())
        
        self.assertEqual(back_tick('/usr/local/bin/python-config --includes'),                  conf.get_includes())
        self.assertEqual(back_tick('/usr/local/bin/python-config --libs'),                      conf.get_libs())
        self.assertEqual(back_tick('/usr/local/bin/python-config --cflags'),                    conf.get_cflags())
        self.assertEqual(back_tick('/usr/local/bin/python-config --ldflags'),                   conf.get_ldflags())
    
    def test_sysconfig(self):
        from sys import version_info
        from halogen.config import SysConfig, environ_override
        conf = SysConfig()
        
        py_fullv = "%(major)s.%(minor)s.%(micro)s" % dict(major=version_info.major,
                                                          minor=version_info.minor,
                                                          micro=version_info.micro)
        
        py_v = "%(major)s.%(minor)s" % dict(major=version_info.major,
                                            minor=version_info.minor)
        
        self.assertEqual('/usr/local/Cellar/python/%s/Frameworks/Python.framework/Versions/%s/bin' % (py_fullv, py_v),          conf.bin())
        self.assertEqual('/usr/local/Cellar/python/%s/Frameworks/Python.framework/Versions/%s/include/python%s' % (py_fullv,
                                                                                                                   py_v, py_v), conf.include())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Versions/%s/lib' % py_v,                            conf.lib())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Versions/%s/lib' % py_v,                            conf.libexec())
        self.assertEqual('/usr/local/share',                                                                                    conf.share())
        
        self.assertEqual('/usr/local/opt/python/Frameworks',                            conf.Frameworks())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Headers',   conf.Headers())
        self.assertEqual('/usr/local/opt/python/Frameworks/Python.framework/Resources', conf.Resources())
        
        self.assertEqual("-I%s" % conf.include(),                       conf.get_includes())
        self.assertEqual("-l%s %s" % (conf.library_name,
                                      environ_override('LIBS')),        conf.get_libs())
        self.assertEqual("-I%s %s" % (conf.include(),
                                      environ_override('CFLAGS')),      conf.get_cflags())
        self.assertEqual("-L%s -l%s %s" % (environ_override('LIBPL'),
                                           conf.library_name,
                                           environ_override('LIBS')),   conf.get_ldflags())
    
    def test_brewedconfig(self):
        from halogen.config import BrewedConfig
        conf = BrewedConfig(brew_name="python")
        
        self.assertEqual('/usr/local/bin',              conf.bin())
        self.assertEqual('/usr/local/include',          conf.include())
        self.assertEqual('/usr/local/lib',              conf.lib())
        self.assertEqual('/usr/local/lib',              conf.libexec())
        self.assertEqual('/usr/local/share',            conf.share())
        
        self.assertFalse(hasattr(conf, "Frameworks"))
        self.assertFalse(hasattr(conf, "Headers"))
        self.assertFalse(hasattr(conf, "Resources"))
        
        self.assertEqual("-I%s" % conf.include(),       conf.get_includes())
        self.assertEqual("",                            conf.get_libs())
        self.assertEqual("-I%s %s" % (conf.include(),
                             " ".join(conf.cflags)),    conf.get_cflags())
        self.assertEqual("-L%s" % conf.lib(),           conf.get_ldflags())
    
    def test_brewedhalideconfig(self):
        from halogen.config import BrewedHalideConfig
        conf = BrewedHalideConfig()
        
        self.assertEqual('/usr/local/bin',              conf.bin())
        self.assertEqual('/usr/local/include',          conf.include())
        self.assertEqual('/usr/local/lib',              conf.lib())
        self.assertEqual('/usr/local/lib',              conf.libexec())
        self.assertEqual('/usr/local/share',            conf.share())
        
        self.assertFalse(hasattr(conf, "Frameworks"))
        self.assertFalse(hasattr(conf, "Headers"))
        self.assertFalse(hasattr(conf, "Resources"))
        
        self.assertEqual("-I%s" % conf.include(),       conf.get_includes())
        self.assertEqual("-l%s" % conf.library,         conf.get_libs())
        self.assertEqual("-I%s %s" % (conf.include(),
                             " ".join(conf.cflags)),    conf.get_cflags())
        self.assertEqual("-L%s -l%s" % (conf.lib(),
                                        conf.library),  conf.get_ldflags())
    
    def test_highest_optimization_level(self):
        from halogen.config import ConfigUnion
        
        self.assertEqual(ConfigUnion.highest_optimization_level({ "O3", "O4", "Os" }), { "O4" })
        self.assertEqual(ConfigUnion.highest_optimization_level({ "O3", "O2", "O1" }), { "O3" })
        self.assertEqual(ConfigUnion.highest_optimization_level({ "Os", "Og", "O1" }), { "O1" })
        self.assertEqual(ConfigUnion.highest_optimization_level({ "O",  "O1", "Os" }), { "O"  })
        self.assertEqual(ConfigUnion.highest_optimization_level({ "O3", "O4", "O5" }), { "O4" })
        self.assertEqual(ConfigUnion.highest_optimization_level({ "O3", "O4", "O8" }), { "O4" })
    
    def test_highest_cxx_language_level(self):
        from halogen.config import ConfigUnion
        
        self.assertEqual(ConfigUnion.highest_cxx_standard_level({ "std=gnu++98", "std=c++14", "std=gnu++14" }), { "std=gnu++14" })
        self.assertEqual(ConfigUnion.highest_cxx_standard_level({ "std=c++1y",   "std=c++14", "std=gnu++1y" }), { "std=c++14"   })
        # self.assertEqual(ConfigUnion.highest_cxx_standard_level({ "std=gnu++98", "std=c++14", "std=gnu++14" }), { "std=gnu++14" })
        # self.assertEqual(ConfigUnion.highest_cxx_standard_level({ "std=gnu++98", "std=c++14", "std=gnu++14" }), { "std=gnu++14" })
        # self.assertEqual(ConfigUnion.highest_cxx_standard_level({ "std=gnu++98", "std=c++14", "std=gnu++14" }), { "std=gnu++14" })
    
    def test_configunion(self):
        from halogen.config import ConfigUnion, SysConfig, BrewedHalideConfig
        
        TOKEN = ConfigUnion.union_of.TOKEN
        conf = ConfigUnion(SysConfig(), BrewedHalideConfig())
        
        def flags_to_set(flags):
            return { x.rstrip() for x in (" %s" % str(" %s" % flags)).split(TOKEN) }
        
        self.assertFalse(hasattr(conf, "bin"))
        self.assertFalse(hasattr(conf, "include"))
        self.assertFalse(hasattr(conf, "lib"))
        self.assertFalse(hasattr(conf, "libexec"))
        self.assertFalse(hasattr(conf, "share"))
        
        self.assertFalse(hasattr(conf, "Frameworks"))
        self.assertFalse(hasattr(conf, "Headers"))
        self.assertFalse(hasattr(conf, "Resources"))
        
        self.assertTrue(SysConfig().get_includes() in conf.get_includes())
        self.assertTrue(BrewedHalideConfig().get_includes() in conf.get_includes())
        
        self.assertTrue(flags_to_set(SysConfig().get_includes()).issubset(flags_to_set(conf.get_includes())))
        self.assertTrue(flags_to_set(BrewedHalideConfig().get_includes()).issubset(flags_to_set(conf.get_includes())))
        
        # self.assertSetEqual(flags_to_set(SysConfig().get_cflags()), flags_to_set(conf.get_cflags()))
        # self.assertSetEqual(flags_to_set(BrewedHalideConfig().get_cflags()), flags_to_set(conf.get_cflags()))
        
        # self.assertTrue(flags_to_set(SysConfig().get_cflags()).issubset(flags_to_set(conf.get_cflags())))
        self.assertTrue(flags_to_set(BrewedHalideConfig().get_cflags()).issubset(flags_to_set(conf.get_cflags())))
        
        self.assertTrue(flags_to_set(SysConfig().get_ldflags()).issubset(flags_to_set(conf.get_ldflags())))
        self.assertTrue(flags_to_set(BrewedHalideConfig().get_ldflags()).issubset(flags_to_set(conf.get_ldflags())))
    
    def test_config_compiler(self):
        from halogen import config
        from halogen.utils import test_compile
        
        brewedHalideConfig = config.BrewedHalideConfig()
        sysConfig = config.SysConfig()
        brewedPythonConfig = config.BrewedPythonConfig()
        pythonConfig = config.PythonConfig()
        configUnion = config.ConfigUnion(brewedHalideConfig, sysConfig)
        configUnionAll = config.ConfigUnion(brewedHalideConfig, sysConfig,
                                            brewedPythonConfig, pythonConfig)
        
        self.assertTrue(test_compile(brewedHalideConfig, config.test_generator_source))
        self.assertTrue(test_compile(configUnion, config.test_generator_source))
        self.assertTrue(test_compile(configUnionAll, config.test_generator_source))

