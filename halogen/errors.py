# -*- coding: utf-8 -*-

from __future__ import print_function


class HalogenError(Exception):
    """ Base class for Halogen errors """
    pass


class GeneratorError(HalogenError):
    """ An error during generation -- as in, running generated code """
    pass