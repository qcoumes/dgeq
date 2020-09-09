from functools import reduce

from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.test import TestCase

from dgeq import utils
from dgeq.exceptions import FieldDepthError, MAX_FOREIGN_FIELD_DEPTH, NotARelatedFieldError, UnknownFieldError
from dgeq.utils import Censor
from django_dummy_app.models import Country, River



class DummyCallable:
    
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
    
    
    def __call__(self):
        return self.args, self.kwargs



class CheckFieldTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(cls.user)
    
    
    def test_model(self):
        model, field = utils.check_field("name", Country, self.censor)
        self.assertEqual(Country, model)
        self.assertEqual("name", field)
    
    
    def test_model_related(self):
        model, field = utils.check_field("rivers.length", Country, self.censor)
        self.assertEqual(River, model)
        self.assertEqual("length", field)
    
    
    def test_model_related_loop(self):
        model, field = utils.check_field("rivers.countries.name", Country, self.censor)
        self.assertEqual(Country, model)
        self.assertEqual("name", field)
    
    
    def test_in_arbitrary_field(self):
        model, field = utils.check_field("arbitrary", Country, self.censor, ["arbitrary"])
        self.assertEqual(Country, model)
        self.assertEqual("arbitrary", field)
    
    
    def test_not_in_arbitrary_field(self):
        model, field = utils.check_field("name", Country, self.censor, ["arbitrary"])
        self.assertEqual(Country, model)
        self.assertEqual("name", field)
    
    
    def test_not_a_related_field(self):
        with self.assertRaises(NotARelatedFieldError):
            utils.check_field("name.other", Country, self.censor)
    
    
    def test_max_depth_exceeded(self):
        with self.assertRaises(FieldDepthError):
            field = "rivers.countries" + (".rivers.countries" * (MAX_FOREIGN_FIELD_DEPTH // 2))
            utils.check_field(field, Country, self.censor)
    
    
    def test_unknown_field_model(self):
        with self.assertRaises(UnknownFieldError):
            utils.check_field("unknown", Country, self.censor)
    
    
    def test_unknown_field_model_related(self):
        with self.assertRaises(UnknownFieldError):
            utils.check_field("rivers.unknown", Country, self.censor)
    
    
    def test_unknown_field_model_related_loop(self):
        with self.assertRaises(UnknownFieldError):
            utils.check_field("rivers.countries.unknown", Country, self.censor)



class GetFieldTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(cls.user)
    
    def test_field(self):
        field = utils.get_field("name", Country, self.censor)
        self.assertEqual(Country._meta.get_field("name"), field)
    
    
    def test_foreign_field(self):
        field = utils.get_field("rivers", Country, self.censor)
        self.assertEqual(Country._meta.get_field("rivers"), field)
    
    
    def test_field_related(self):
        field = utils.get_field("rivers.length", Country, self.censor)
        self.assertEqual(River._meta.get_field("length"), field)
    
    
    def test_foreign_field_related(self):
        field = utils.get_field("rivers.countries", Country, self.censor)
        self.assertEqual(River._meta.get_field("countries"), field)



class ImportCallableTestCase(TestCase):
    
    def test_import_function(self):
        self.assertEqual(len, utils.import_callable(len))
    
    
    def test_import_function_path(self):
        self.assertEqual(reduce, utils.import_callable("functools.reduce"))
    
    
    def test_import_callable(self):
        self.assertEqual((tuple(), dict()), utils.import_callable("test_utils.DummyCallable")())
    
    
    def test_import_callable_tuple(self):
        self.assertEqual((tuple(), dict()), utils.import_callable(("test_utils.DummyCallable",))())
    
    
    def test_import_callable_args(self):
        self.assertEqual(
            (("foo", "bar"), dict()),
            utils.import_callable(("test_utils.DummyCallable", ("foo", "bar")))()
        )
    
    
    def test_import_callable_kwargs(self):
        self.assertEqual(
            (tuple(), {"foo": "bar"}),
            utils.import_callable(("test_utils.DummyCallable", {"foo": "bar"}))()
        )
    
    
    def test_import_callable_args_kwargs(self):
        self.assertEqual(
            (("foo", "bar"), {"foo": "bar"}),
            utils.import_callable(("test_utils.DummyCallable", ("foo", "bar"), {"foo": "bar"}))()
        )
    
    
    def test_import_class_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable(int)
    
    
    def test_import_not_callable_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable("string.ascii_letters")
    
    
    def test_import_first_elem_not_class_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable(("functools.reduce", (2,)))
    
    
    def test_import_second_elem_not_iter_or_map_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable(("test_utils.DummyCallable", 1))
    
    
    def test_import_second_elem_not_iter_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable(("test_utils.DummyCallable", 1, {}))
    
    
    def test_import_third_elem_not_map_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable(("test_utils.DummyCallable", [], 1))
    
    
    def test_not_a_callable_str_or_iterable_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable(1)
    
    
    def test_not_a_callable_class_exception(self):
        with self.assertRaises(ValueError):
            utils.import_callable("string.Formatter")



class SubqueryToQuerydictTestCase(TestCase):
    
    def test_ok(self):
        qs = "field=rivers|to=rivers_count|func=count|filters=length=>2000"
        query_dict = utils.subquery_to_querydict(qs, '|', "'")
        
        expected = QueryDict(mutable=True)
        expected.setlist("field", ["rivers"])
        expected.setlist("to", ["rivers_count"])
        expected.setlist("func", ["count"])
        expected.setlist("filters", ["length=>2000"])
        self.assertEqual(expected, query_dict)
    
    
    def test_ok_multiple_values(self):
        qs = "field=rivers|to=rivers_count|func=count|filters=length=>2000'length=<3000"
        query_dict = utils.subquery_to_querydict(qs, '|', "'")
        
        expected = QueryDict(mutable=True)
        expected.setlist("field", ["rivers"])
        expected.setlist("to", ["rivers_count"])
        expected.setlist("func", ["count"])
        expected.setlist("filters", ["length=>2000", "length=<3000"])
        self.assertEqual(expected, query_dict)
    
    
    def test_ok_multiple_same_field(self):
        qs = "field=rivers|to=rivers_count|func=count|filters=length=>2000|filters=length=<3000"
        query_dict = utils.subquery_to_querydict(qs, '|', "'")
        
        expected = QueryDict(mutable=True)
        expected.setlist("field", ["rivers"])
        expected.setlist("to", ["rivers_count"])
        expected.setlist("func", ["count"])
        expected.setlist("filters", ["length=>2000", "length=<3000"])
        self.assertEqual(expected, query_dict)
    
    
    def test_missing_equal(self):
        qs = "field=rivers|rivers_count|func=count|filters=length=>2000"
        with self.assertRaises(ValueError):
            utils.subquery_to_querydict(qs, '|', "'")



class SplitListStringTestCase(TestCase):
    
    def test(self):
        lst = utils.split_list_strings(["one,two", "three", "four,five,six"], ",")
        self.assertEqual(['one', 'two', 'three', 'four', 'five', 'six'], lst)
