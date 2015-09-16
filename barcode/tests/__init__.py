import unittest
import pkgutil

__author__ = 'rf9'


def suite():
    return unittest.TestLoader().discover("robox.tests", pattern="*.py")


for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    module = loader.find_module(module_name).load_module(module_name)
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            exec('%s = obj' % obj.__name__)
