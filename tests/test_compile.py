
from __future__ import print_function

import os
from basecase import BaseCase
from halogen.filesystem import cd

class CompileTests(BaseCase):
    
    def setUp(self):
        super(CompileTests, self).setUp()
        from halogen.compile import CONF
        self.CONF = CONF
        with cd("/Users/fish/Dropbox/halogen/tests/generators") as gendir:
            self.gendir = gendir.realpath()
            self.genfiles = gendir.ls_la(suffix="cpp")
    
    def test_generators_compile_link_and_archive_context_manager(self):
        from halogen.generate import generate
        from halogen.compile import Generators
        from halogen.filesystem import TemporaryDirectory
        
        self.assertTrue(len(self.genfiles) > 0)
        
        with TemporaryDirectory(prefix='test-generators-compile-link-and-archive-context-manager-') as td:
            
            # EVERYTHING!
            with Generators(self.CONF,
                            destination=td.name,
                            directory=self.gendir,
                            verbose=False) as gens:
                self.assertTrue(gens.compiled)
                self.assertTrue(gens.linked)
                self.assertTrue(gens.archived)
                gens.preload_all()
                
                registered = self.hal.api.registered_generators()
                self.assertTrue(len(registered) > 0)
                
                target_string = self.hal.api.Target.target_from_environment().to_string()
                self.assertTrue(self.hal.api.Target.validate_target_string(target_string))
                
                with TemporaryDirectory(prefix='test-generate-registered-') as td2:
                    
                    bsepths, outputs, modules = generate(*registered, verbose=False,
                                                                      target=target_string,
                                                                      output_directory=td2.name)
                    self.assertEqual(len(bsepths), len(outputs))
                    self.assertEqual(len(bsepths), len(modules))
                    self.assertEqual(len(outputs), len(modules))
                    
                    for output in outputs:
                        for prop_name in ("object_name", "assembly_name", "bitcode_name",
                                          "llvm_assembly_name", "c_header_name", "c_source_name",
                                          "stmt_name", "stmt_html_name", "static_library_name"):
                            if getattr(output, prop_name, ''):
                                self.assertTrue(os.path.exists(getattr(output, prop_name)))
                            else:
                                self.assertFalse(os.path.exists(getattr(output, prop_name)))
    
    def test_generator_compile_context_manager(self):
        from halogen.compile import Generator
        from halogen.filesystem import TemporaryName, TemporaryDirectory
        
        self.assertTrue(len(self.genfiles) > 0)
        
        with TemporaryDirectory(prefix='test-generator-compile-context-manager-') as td:
            
            # COMPILE!
            for genfile in self.genfiles:
                
                with TemporaryName(suffix="cpp.o", parent=td.name) as adotout:
                    with Generator(self.CONF,
                                   source=genfile,
                                   destination=adotout.name,
                                   verbose=False) as gen:
                        self.assertTrue(gen.compiled)
    
    def test_compile_link_and_archive(self):
        from halogen import config
        from halogen.filesystem import TemporaryName, TemporaryDirectory
        
        self.assertTrue(len(self.genfiles) > 0)
        
        with TemporaryDirectory(prefix='test-compile-link-and-archive-') as td:
            
            # COMPILE!
            prelink = []
            for genfile in self.genfiles:
                
                with TemporaryName(suffix="cpp.o", parent=td.name) as adotout:
                    result = config.CXX(self.CONF,
                                        adotout.name,
                                        genfile, verbose=True)
                    self.assertTrue(len(result) > 0)
                    self.assertFalse(len(result[1]) > 0)
                    self.assertTrue(os.path.exists(str(adotout)))
                    prelink.append(adotout.do_not_destroy())
            
            self.assertEqual(len(prelink), len(self.genfiles))
            
            # LINK!
            with TemporaryName(suffix=config.SHARED_LIBRARY_SUFFIX, parent=td.name) as linkfile:
                link_result = config.LD(self.CONF,
                                        linkfile.name,
                                       *prelink, verbose=True)
                self.assertTrue(len(link_result) > 0)
                self.assertFalse(len(link_result[1]) > 0)
                self.assertTrue(linkfile.exists)
            
            # ARCHIVE!
            with TemporaryName(suffix=config.STATIC_LIBRARY_SUFFIX, parent=td.name) as archfile:
                arch_result = config.LD(self.CONF,
                                        archfile.name,
                                       *prelink, verbose=True)
                self.assertTrue(len(arch_result) > 0)
                self.assertFalse(len(arch_result[1]) > 0)
                self.assertTrue(archfile.exists)
    
