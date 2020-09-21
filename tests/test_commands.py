from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.http import QueryDict
from django.test import TestCase

from dgeq import GenericQuery, commands
from dgeq.exceptions import InvalidCommandError
from dgeq.utils import Censor
from django_dummy_app.models import Country, Forest



class AnnotationTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_annotate(self):
        subquery = "field=rivers.length|func=avg|to=rivers_length_avg|filters=rivers.length=<1500|early=0"
        dgeq = GenericQuery(Country, QueryDict())
        commands.Annotate()(dgeq, "c:annotate", [subquery])
        func = models.Avg("rivers__length", filter=models.Q(rivers__length__lt=1500))
        queryset = Country.objects.all().annotate(population_avg=func)
        self.assertEqual(queryset.query, dgeq.queryset.query)



class AggregateTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_aggregate(self):
        subquery = "field=population|func=avg|to=population_avg"
        dgeq = GenericQuery(Country, QueryDict())
        commands.Aggregate()(dgeq, "c:aggregate", [subquery])
        self.assertEqual(["status", "population_avg"], list(dgeq.result.keys()))
        self.assertEqual(
            Country.objects.all().aggregate(
                population_avg=models.Avg("population")
            )["population_avg"],
            dgeq.result["population_avg"]
        )



class CaseTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_case(self):
        values = ["0"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Case()(dgeq, "c:case", values)
        self.assertEqual(False, dgeq.case)
        
        values = ["1"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Case()(dgeq, "c:case", values)
        self.assertEqual(True, dgeq.case)
    
    
    def test_case_invalid_value(self):
        values = ["invalid"]
        dgeq = GenericQuery(Country, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Case()(dgeq, "c:case", values)



class CountTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_count(self):
        values = ["0"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Count()(dgeq, "c:count", values)
        self.assertNotIn("count", dgeq.result)
        
        values = ["1"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Count()(dgeq, "c:count", values)
        self.assertIn("count", dgeq.result)
        self.assertEqual(Country.objects.all().count(), dgeq.result["count"])
    
    
    def test_count_invalid_value(self):
        values = ["invalid"]
        dgeq = GenericQuery(Country, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Count()(dgeq, "c:count", values)



class DistinctTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_distinct_true(self):
        dgeq = GenericQuery(Forest, QueryDict())
        commands.Filtering()(dgeq, "countries.region.name", ["South America"])
        without_distinct = dgeq.queryset.count()
        
        dgeq = GenericQuery(Forest, QueryDict())
        commands.Filtering()(dgeq, "countries.region.name", ["South America"])
        commands.Distinct()(dgeq, "c:distinct", ["1"])
        with_distinct = dgeq.queryset.count()
        
        self.assertEqual(10, without_distinct)
        self.assertEqual(2, with_distinct)
    
    
    def test_distinct_false(self):
        dgeq = GenericQuery(Forest, QueryDict())
        commands.Filtering()(dgeq, "countries.region.name", ["South America"])
        without_distinct = dgeq.queryset.count()
        
        dgeq = GenericQuery(Forest, QueryDict())
        commands.Filtering()(dgeq, "countries.region.name", ["South America"])
        commands.Distinct()(dgeq, "c:distinct", ["0"])
        with_distinct = dgeq.queryset.count()
        
        self.assertEqual(10, without_distinct)
        self.assertEqual(10, with_distinct)
    
    
    def test_distinct_unknown_value(self):
        dgeq = GenericQuery(Forest, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Distinct()(dgeq, "c:distinct", ["unknown"])
    
    
    def test_distinct_sliced(self):
        dgeq = GenericQuery(Forest, QueryDict())
        dgeq.sliced = True
        with self.assertRaises(InvalidCommandError):
            commands.Distinct()(dgeq, "c:distinct", ["1"])



class EvaluateTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(user=cls.user)
    
    
    def test_evaluate(self):
        values = ["1"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Evaluate()(dgeq, "c:evaluate", values)
        self.assertTrue(dgeq.evaluated)
    
    
    def test_not_evaluate(self):
        values = ["0"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Evaluate()(dgeq, "c:evaluate", values)
        self.assertFalse(dgeq.evaluated)
    
    
    def test_evaluate_invalid(self):
        values = ["invalid"]
        dgeq = GenericQuery(Country, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Evaluate()(dgeq, "c:evaluate", values)



class FilteringTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_filtering_ok(self):
        dgeq = GenericQuery(Country, QueryDict())
        commands.Filtering()(dgeq, "population", [">1000000"])
        commands.Filtering()(dgeq, "name", ["*republic"])
        self.assertEqual(
            list(Country.objects.filter(population__gt=1000000, name__contains="republic")),
            list(dgeq.queryset)
        )
    
    
    def test_filtering_sliced(self):
        dgeq = GenericQuery(Country, QueryDict())
        dgeq.sliced = True
        with self.assertRaises(InvalidCommandError):
            commands.Filtering()(dgeq, "population", [">1000000"])



class JoinTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_join_ok(self):
        values = ["field=rivers,field=region", "field=mountains"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Join()(dgeq, "c:join", values)
        
        self.assertIn("rivers", dgeq.joins)
        self.assertIn("mountains", dgeq.joins)
        self.assertIn("region", dgeq.joins)



class ShowTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_no_show(self):
        dgeq = GenericQuery(Country, QueryDict())
        fields = {
            "name", "disasters", "id", "area", "forests", "population", "rivers",
            "region", "mountains"
        }
        self.assertEqual(fields, dgeq.fields)
    
    
    def test_show(self):
        values = ["name"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Show()(dgeq, "c:show", values)
        self.assertEqual({"name"}, dgeq.fields)
    
    
    def test_hide(self):
        values = ["population,rivers,region,mountains"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Show()(dgeq, "c:hide", values)
        fields = {"name", "disasters", "id", "area", "forests"}
        self.assertEqual(fields, dgeq.fields)
    
    
    def test_hide_show(self):
        show = ["name"]
        hide = ["population,rivers,region,mountains,name"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Show()(dgeq, "c:hide", hide)
        commands.Show()(dgeq, "c:show", show)
        self.assertEqual({"name"}, dgeq.fields)
    
    
    def test_show_hide(self):
        show = ["name"]
        hide = ["population,rivers,region,mountains,name"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Show()(dgeq, "c:show", show)
        commands.Show()(dgeq, "c:hide", hide)
        self.assertEqual({"disasters", "id", "area", "forests"}, dgeq.fields)



class SortTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_sort(self):
        values = ["name"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Sort()(dgeq, "c:sort", values)
        rows = dgeq._evaluate()
        
        self.assertEqual(
            Country.objects.order_by("name").first().id,
            rows[0]["id"]
        )
    
    
    def test_no_sort(self):
        dgeq = GenericQuery(Country, QueryDict())
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.first().id,
            rows[0]["id"]
        )
    
    
    def test_sort_desc(self):
        values = ["-population"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Sort()(dgeq, "c:sort", values)
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.order_by("-population").first().id,
            rows[0]["id"]
        )
    
    
    def test_sort_multiple(self):
        values = ["-region.name,population"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Sort()(dgeq, "c:sort", values)
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.order_by("-region__name", "population").first().id,
            rows[0]["id"]
        )
    
    
    def test_sort_after_slicing(self):
        values = ["-region.name,population"]
        dgeq = GenericQuery(Country, QueryDict())
        dgeq.sliced = True
        with self.assertRaises(InvalidCommandError):
            commands.Sort()(dgeq, "c:sort", values)



class SubsetTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_limit_0(self):
        values = ["0"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Subset()(dgeq, "c:limit", values)
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.all().count(),
            len(rows)
        )
    
    
    def test_limit_gt_0(self):
        values = ["89"]
        dgeq = GenericQuery(Country, QueryDict())
        commands.Subset()(dgeq, "c:limit", values)
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.all()[:89].count(),
            len(rows)
        )
    
    
    def test_start(self):
        dgeq = GenericQuery(Country, QueryDict())
        commands.Subset()(dgeq, "c:start", ["4"])
        commands.Subset()(dgeq, "c:limit", ["0"])
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.all()[4:].count(),
            len(rows)
        )
        self.assertEqual(
            Country.objects.all()[4:][0].id,
            rows[0]["id"]
        )
    
    
    def test_start_limit(self):
        dgeq = GenericQuery(Country, QueryDict())
        commands.Subset()(dgeq, "c:start", ["4"])
        commands.Subset()(dgeq, "c:limit", ["52"])
        rows = dgeq._evaluate()
        self.assertEqual(
            Country.objects.all()[4:56].count(),
            len(rows)
        )
        self.assertEqual(
            Country.objects.all()[4:56][0].id,
            rows[0]["id"]
        )
    
    
    def test_invalid_value(self):
        values = ["-1"]
        dgeq = GenericQuery(Country, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Subset()(dgeq, "c:limit", values)
        
        dgeq = GenericQuery(Country, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Subset()(dgeq, "c:start", values)



class TimeTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    def test_time(self):
        values = ["1"]
        dgeq = GenericQuery(Country, QueryDict())
        dgeq._evaluate()
        commands.Time()(dgeq, "c:time", values)
        self.assertIn("time", dgeq.result)
        self.assertLess(dgeq.result["time"], 2)
    
    
    def test_no_time(self):
        values = ["0"]
        dgeq = GenericQuery(Country, QueryDict())
        dgeq._evaluate()
        commands.Time()(dgeq, "c:time", values)
        self.assertNotIn("time", dgeq.result)
    
    
    def test_invalid_value(self):
        values = ["-1"]
        dgeq = GenericQuery(Country, QueryDict())
        with self.assertRaises(InvalidCommandError):
            commands.Time()(dgeq, "c:time", values)
