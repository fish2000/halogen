# -*- coding: utf-8 -*-

from __future__ import print_function


class HalogenError(Exception):
    """ Base class for Halogen errors """
    pass


class ExecutionError(HalogenError):
    """ An error during the execution of a shell command """
    pass


class FilesystemError(HalogenError):
    """ An error that occurred while mucking about with the filesystem """
    pass


class GeneratorError(HalogenError):
    """ An error during generation -- as in, running generated code """
    pass