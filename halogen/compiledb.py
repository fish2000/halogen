# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import os
import six

from abc import ABC, ABCMeta, abstractmethod
from errors import CDBError
from filesystem import rm_rf, TemporaryName, Directory
from utils import stringify, u8bytes, u8str

__all__ = ('CDBSubBase', 'CDBBase',
                         'CDBJsonFile')

SubBaseAncestor = six.with_metaclass(ABCMeta, ABC)
class CDBSubBase(SubBaseAncestor):
    
    @abstractmethod
    def push(self, filepth, command, directory=None,
                                     destination=None): pass
    
    @abstractmethod
    def __len__(self): pass
    
    @abstractmethod
    def __getitem__(self, key): pass
    
    @abstractmethod
    def to_string(self): pass
    
    @abstractmethod
    def __repr__(self): pass
    
    @abstractmethod
    def __str__(self): pass
    
    @abstractmethod
    def __bytes__(self): pass
    
    @abstractmethod
    def __unicode__(self): pass
    
    @abstractmethod
    def __bool__(self): pass


class CDBBase(CDBSubBase):
    
    fields = ('length',)
    
    def __init__(self):
        self.clear()
    
    def push(self, source, command, directory=None,
                                    destination=None):
        if not source:
            raise CDBError("a file source is required per entry")
        entry = {
            'directory'     : directory or os.getcwd(),
            'command'       : u8str(command),
            'file'          : source
        }
        if destination:
            entry.update({
                'output'    : destination
            })
        self.entries[source] = entry
    
    def rollout(self):
        out = []
        for k, v in self.entries.items():
            out.append(v)
        return out
    
    @property
    def length(self):
        return len(self.entries)
    
    def clear(self):
        self.entries = {}
        return self
    
    def __len__(self):
        return self.length
    
    def __getitem__(self, key):
        try:
            return self.entries[int(key)]
        except (ValueError, KeyError):
            skey = str(key)
            if os.extsep in skey:
                for entry in self.entries:
                    if entry['file'] == skey:
                        return entry
        raise KeyError(f"not found: {key}")
    
    def to_string(self):
        return stringify(self, type(self).fields)
    
    def __repr__(self):
        return stringify(self, type(self).fields)
    
    def __str__(self):
        return u8str(json.dumps(self.rollout()))
    
    def __bytes__(self):
        return u8bytes(json.dumps(self.rollout()))
    
    def __unicode__(self):
        return six.u(str(self))
    
    def __bool__(self):
        return True

CDBSubBase.register(CDBBase)

class CDBJsonFile(CDBBase):
    
    fields = ('filename', 'length', 'exists')
    filename = f'compilation_database{os.extsep}json'
    splitname = os.path.splitext(filename)
    
    @classmethod
    def in_directory(cls, directory):
        return cls.filename in Directory(pth=directory)
    
    def __init__(self, directory=None):
        super(CDBJsonFile, self).__init__()
        if not directory:
            directory = os.getcwd()
        self.directory = Directory(pth=directory)
        self.target = self.directory.subpath(self.filename)
        self.read_from = None
        self.written_to = None
    
    @property
    def name(self):
        return self.target
    
    @property
    def exists(self):
        return os.path.isfile(self.name)
    
    def read(self, pth=None):
        readpth = pth or self.target
        if not readpth:
            raise CDBError("no path value from which to read")
        readpth = os.fspath(readpth)
        if not os.path.exists(readpth):
            raise CDBError("no file from which to read")
        with open(readpth, mode="r") as handle:
            try:
                cdblist = json.load(handle)
            except json.JSONDecodeError as json_error:
                raise CDBError(str(json_error))
            else:
                for cdbentry in cdblist:
                    key = cdbentry.get('file')
                    self.entries[key] = dict(cdbentry)
        self.read_from = readpth
        return self
    
    def write(self, pth=None):
        with TemporaryName(prefix=self.splitname[0],
                           suffix=self.splitname[1][1:]) as tn:
            with open(tn.name, mode='w') as handle:
                handle.write(str(self))
            if pth is None:
                if self.exists:
                    rm_rf(self.name)
                tn.copy(self.name)
                self.written_to = self.name
            else:
                writepth = os.fspath(pth)
                if os.path.isdir(writepth):
                    raise CDBError("can't overwrite a directory")
                if os.path.isfile(writepth) or \
                   os.path.islink(writepth):
                    rm_rf(writepth)
                tn.copy(writepth)
                self.written_to = writepth
        return self
    
    def __enter__(self):
        if os.path.isfile(self.target):
            self.read()
        return self
    
    def __exit__(self, exc_type=None,
                       exc_val=None,
                       exc_tb=None):
        self.write()

CDBSubBase.register(CDBJsonFile)

del SubBaseAncestor

def test():
    pass

if __name__ == '__main__':
    test()