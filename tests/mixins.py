import json
from contextlib import contextmanager

from django.db import connections
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext



class QueryTestMixin(TransactionTestCase):
    
    @contextmanager
    def assertNumQueriesLess(self, value, using='default', verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield context  # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertLess(len(context.captured_queries), value, msg=msg)
    
    
    @contextmanager
    def assertNumQueriesLessEqual(self, value, using='default', verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield context  # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertLessEqual(len(context.captured_queries), value, msg=msg)
    
    
    @contextmanager
    def assertNumQueriesGreater(self, value, using='default', verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield context  # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertGreater(len(context.captured_queries), value, msg=msg)
    
    
    @contextmanager
    def assertNumQueriesGreaterEqual(self, value, using='default', verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield context  # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertGreaterEqual(len(context.captured_queries), value, msg=msg)
