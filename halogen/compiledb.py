# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import os
import six

from abc import ABC, ABCMeta, abstractmethod
from utils import stringify, u8bytes, u8str

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
    
    def __init__(self):
        self.entries = []
    
    def push(self, source, command, directory=None,
                                    destination=None):
        entry = {
            'directory' : directory or os.getcwd(),
            'command'   : u8str(command)
        }
        entry.update({
            'file'      : source
        })
        self.entries.append(entry)
        print(f"entries: {self.entries}")
    
    def __len__(self):
        return len(self.entries)
    
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
        return stringify(self, ('entries',))
    
    def __repr__(self):
        return stringify(self, ('entries',))
    
    def __str__(self):
        return u8str(json.dumps(self.entries))
    
    def __bytes__(self):
        return u8bytes(json.dumps(self.entries))
    
    def __unicode__(self):
        return six.u(str(self))
    
    def __bool__(self):
        return True

CDBSubBase.register(CDBBase)

del SubBaseAncestor

def test():
    pass

if __name__ == '__main__':
    test()