# -*- coding: utf-8 -*-

import io
import base64
import tempfile
import filelike

# try:
#     from cStringIO import StringIO
# except ImportError:
#     from StringIO import StringIO

class Basic(object):
    DEFAULT_MODE = "r+b"
    
    @property
    def content(self):
        out = ""
        wat = 0
        try:
            wat = self.tell()
            out = self.read()
        except:
            pass
        finally:
            self.seek(wat, 0)
        return out
    
    def getvalue(self):
        return self.content

# def classproperty(f):
#     return property(classmethod(f))
#
# mu = lambda tau: tau
#
# class SubDescriptor(object):
#
#     @classproperty
#     def FileClass(cls):
#         return filelike.wrappers.FileWrapper
#
#     def __init__(self, gamma=None):
#         """ Gamma (γ) is the opposite of lambda (λ),
#             q.v. a recently published 2016 discursive analysis
#             of typography and semiotic etymology, released
#             by the University of my Eyeballs [§] –– hence
#             this name for a variable holding a callable:
#         """
#         self.gamma = gamma or mu
#
#     def __get__(self, instance=None, owner=None):
#         if instance is None:
#             raise AttributeError("access descriptors via instances")
#         # return self.FileClass(self.gamma(),
#         #                       mode=Basic.DEFAULT_MODE)
#         return filelike.to_filelike(self.gamma(instance))
#
#     def __set__(self, instance, value):
#         pass


class Base64(filelike.wrappers.Translate, Basic):
    
    def __init__(self, fileobj, mode=None):
        supermode = mode or self.DEFAULT_MODE
        super(Base64, self).__init__(fileobj, rfunc=base64.b64decode,
                                              wfunc=base64.b64encode,
                                              mode=supermode)


class BZip64(Base64):
    Compressor = filelike.wrappers.UnBZip2
    
    def __init__(self, fileobj, mode=None):
        supermode = mode or self.DEFAULT_MODE
        super(BZip64, self).__init__(self.Compressor(fileobj),
                                     mode=supermode)


class ContentFile(filelike.wrappers.Buffer, Basic):
    
    def __init__(self, content=None):
        if not content:
            content = ""
        self._content = bytearray(content)
        self._contentIO = io.BytesIO(self._content)
        self._contentIO.seek(0, 2) # END OF LINE.
        super(ContentFile, self).__init__(self._contentIO)
    
    @property
    def content(self):
        return self._contentIO.getvalue()


class File(filelike.wrappers.FileWrapper, Basic):
    
    def __init__(self, path):
        super(File, self).__init__(io.open(path, self.DEFAULT_MODE),
                                            mode=self.DEFAULT_MODE)


class BasicTemporaryFile(tempfile.SpooledTemporaryFile, Basic):
    pass

class GeneratorLibrary(object):
    
    # None       : filelike.wrappers.UnNullZip, <---- NOT FOUND, WAT
    
    COMPRESSORS = {  
                    "bz2"       : filelike.wrappers.UnBZip2,
                    "bz64"      : BZip64,
                    "base64"    : Base64 }
    
    def __init__(self, path):
        self.path = path
        self.fileobj = File(path)
        self.tmpfile = BasicTemporaryFile(mode=File.DEFAULT_MODE,
                                          prefix=path,
                                          suffix=".bz2")
        self.compressor = BZip64(self.tmpfile)
        self.compress(self.fileobj.content)
    
    def compress(self, uncompressed=None):
        if uncompressed:
            self.compressor.write(bytes(uncompressed))
        return self.tmpfile.content
    
    def decompress(self, compressed=None):
        if compressed:
            self.tmpfile.write(bytes(compressed))
        return self.compressor.content
    
    def __getstate__(self):
        return { 'path'         :  self.path,
                 'data'         :  self.compress(),
                 'compressor'   : "bz64" }
    
    def __setstate__(self, state):
        self.path = state.get('path')
        self.fileobj = File(self.path)
        self.tmpfile = BasicTemporaryFile(mode=File.DEFAULT_MODE,
                                          prefix=self.path,
                                          suffix=".bz2")
        
        compressor_name = state.get('compressor', 'bz64')
        CompressorClass = self.COMPRESSORS[compressor_name]
        self.compressor = CompressorClass(self.tmpfile)
        self.tmpfile.write(state.get('data'))
    
    


if __name__ == '__main__':
    pass

# § apologies/thanks/credit to Seth Meyers