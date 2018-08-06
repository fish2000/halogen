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


class ConfigurationError(HalogenError):
    """ An error that occurred in the course of self-configuring """
    pass


class ConfigCommandError(HalogenError, IOError):
    """ An error that occurred during configuring, while running a command """
    pass


class GeneratorError(HalogenError):
    """ Base class for Halogen generator errors """
    pass


class GeneratorLoaderError(GeneratorError):
    """ An error during generator loading """
    pass


class GenerationError(GeneratorError):
    """ An error during generation -- as in, the running of a compiled generator """
    pass


class CDBError(HalogenError):
    """ A problem with a compilation database """
    pass