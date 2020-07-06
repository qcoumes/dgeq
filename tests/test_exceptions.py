import inspect

from django.test import TestCase

from dgeq import exceptions



class ExceptionsTestCase(TestCase):
    
    def test_error_code_unique(self):
        codes = ['UNKNOWN']
        for exception in [i for i in vars(exceptions).values()]:
            if inspect.isclass(exception) and issubclass(exception, exceptions.DgeqError):
                self.assertNotIn(exception.code, codes)
                codes.append(exception.code)
