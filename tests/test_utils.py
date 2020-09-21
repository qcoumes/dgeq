from functools import reduce

from django.contrib.auth.models import AnonymousUser, Permission, User
from django.http import QueryDict
from django.test import TestCase

from dgeq import GenericQuery, utils
from dgeq.exceptions import FieldDepthError, MAX_FOREIGN_FIELD_DEPTH, NotARelatedFieldError, UnknownFieldError
from dgeq.joins import JoinQuery
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
        cls.censor = Censor(user=cls.user)
    
    
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
        cls.censor = Censor(user=cls.user)
    
    
    def test_field(self):
        field = utils.get_field_recursive("name", Country, self.censor)
        self.assertEqual(utils.get_field("name", Country), field)
    
    
    def test_foreign_field(self):
        field = utils.get_field_recursive("rivers", Country, self.censor)
        self.assertEqual(utils.get_field("rivers", Country), field)
    
    
    def test_field_related(self):
        field = utils.get_field_recursive("rivers.length", Country, self.censor)
        self.assertEqual(utils.get_field("length", River), field)
    
    
    def test_foreign_field_related(self):
        field = utils.get_field_recursive("rivers.countries", Country, self.censor)
        self.assertEqual(utils.get_field("countries", River), field)



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



class SerializeRowTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_serialize_row(self):
        c = Country.objects.get(pk=1)
        row = utils.serialize_row(
            c, ["name", "population"], ["region"], ["rivers", "mountains"],
            {
                "rivers": JoinQuery.from_query_value(
                    "field=rivers", Country, False, Censor(user=AnonymousUser())
                )
            }
        )
        expected = {
            'name':       'Afghanistan',
            'population': 36296100,
            'region':     15,
            'rivers':     [
                {
                    'length':    2620,
                    'discharge': 1400,
                    'id':        37,
                    'name':      'Amu Darya–Panj',
                    'countries': [1, 202, 211, 222]
                },
                {
                    'length':    1130,
                    'discharge': None,
                    'id':        165,
                    'name':      'Helmand',
                    'countries': [1, 100]
                }
            ],
            'mountains':  [
                331, 332, 473, 475, 478, 500, 504, 506, 508, 535, 948, 1043,
                1128, 1130, 1157
            ]
        }
        self.assertEqual(expected, row)
    
    
    def test_serialize_row_no_join(self):
        c = Country.objects.get(pk=1)
        row = utils.serialize_row(
            c, ["name", "population"], ["region"], ["rivers", "mountains"]
        )
        expected = {
            'name':       'Afghanistan',
            'population': 36296100,
            'region':     15,
            'rivers':     [37, 165],
            'mountains':  [
                331, 332, 473, 475, 478, 500, 504, 506, 508, 535, 948, 1043,
                1128, 1130, 1157
            ]
        }
        self.assertEqual(expected, row)



class SerializeTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_serialize(self):
        c = Country.objects.get(pk=1)
        query_dict = QueryDict("id=1")
        user = User.objects.create_user("test")
        user.user_permissions.add(Permission.objects.get(codename='view_country'))
        user.user_permissions.add(Permission.objects.get(codename='view_region'))
        user.user_permissions.add(Permission.objects.get(codename='view_river'))
        dgeq = GenericQuery(Country, query_dict, private_fields={
            Country: ["area", "mountains"]
        }, user=user, use_permissions=True)
        res = dgeq.evaluate()
        row = utils.serialize(c, private_fields={
            Country: ["area", "mountains"]
        }, user=user, use_permissions=True)
        
        self.assertEqual(res["rows"][0], row)
    
    
    def test_serialize_permission_true_user_none(self):
        with self.assertRaises(ValueError):
            utils.serialize(Country.objects.get(pk=1), use_permissions=True)
