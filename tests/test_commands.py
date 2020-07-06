from django.db import models
from django.http import QueryDict
from django.test import TestCase

from dgeq import GenericQuery, commands
from dgeq.aggregations import Annotation
from dgeq.exceptions import InvalidCommandError
from dgeq.filter import Filter
from dgeq.joins import JoinQuery
from django_dummy_app.models import Country



class AnnotationTestCase(TestCase):
    
    def test_compute_annotation(self):
        subquery = "field=rivers.length|func=avg|to=rivers_length_avg|filters=rivers.length=<1500|early=0"
        query_dict = QueryDict(f"c:annotate={subquery}")
        dgeq = GenericQuery(Country, query_dict)
        commands.ComputeAnnotation()(dgeq, query_dict)
        annotation = Annotation(
            "rivers__length", "rivers_length_avg", models.Avg,
            [Filter("rivers.length", "<1500", False, Country)], False
        )
        self.assertIn("rivers_length_avg", dgeq.arbitrary_fields)
        self.assertEqual([annotation], dgeq.annotations)
    
    
    def test_annotate(self):
        dgeq = GenericQuery(Country, QueryDict())
        annotation = Annotation(
            "rivers__length", "rivers_length_avg", models.Avg,
            [Filter("rivers.length", "<1500", False, Country)], False
        )
        dgeq.annotations = [annotation]
        commands.Annotate(False)(dgeq, QueryDict())
        func = models.Avg("rivers__length", filter=models.Q(rivers__length__lt=1500))
        queryset = Country.objects.all().annotate(population_avg=func)
        self.assertEqual(queryset.query, dgeq.queryset.query)



class AggregateTestCase(TestCase):
    
    def test_aggregate(self):
        subquery = "field=population|func=avg|to=population_avg"
        query_dict = QueryDict(f"c:aggregate={subquery}")
        dgeq = GenericQuery(Country, query_dict)
        commands.Aggregate()(dgeq, query_dict)
        self.assertEqual(["status", "population_avg"], list(dgeq.result.keys()))
        self.assertEqual(
            Country.objects.all().aggregate(
                population_avg=models.Avg("population")
            )["population_avg"],
            dgeq.result["population_avg"]
        )
    
    
    def test_aggregate_no_aggregation(self):
        query_dict = QueryDict()
        dgeq = GenericQuery(Country, query_dict)
        commands.Aggregate()(dgeq, query_dict)
        self.assertEqual(["status"], list(dgeq.result.keys()))



class CaseTestCase(TestCase):
    
    def test_case(self):
        query_dict = QueryDict("c:case=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Case()(dgeq, query_dict)
        self.assertEqual(False, dgeq.case)
        
        query_dict = QueryDict("c:case=1")
        dgeq = GenericQuery(Country, query_dict)
        commands.Case()(dgeq, query_dict)
        self.assertEqual(True, dgeq.case)
    
    
    def test_case_invalid_value(self):
        query_dict = QueryDict("c:case=invalid")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Case()(dgeq, query_dict)



class RelatedTestCase(TestCase):
    
    def test_related(self):
        query_dict = QueryDict("c:related=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Related()(dgeq, query_dict)
        self.assertEqual(False, dgeq.related)
        
        query_dict = QueryDict("c:related=1")
        dgeq = GenericQuery(Country, query_dict)
        commands.Related()(dgeq, query_dict)
        self.assertEqual(True, dgeq.related)
    
    
    def test_related_invalid_value(self):
        query_dict = QueryDict("c:related=invalid")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Related()(dgeq, query_dict)



class CountTestCase(TestCase):
    
    def test_count(self):
        query_dict = QueryDict("c:count=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Count()(dgeq, query_dict)
        self.assertNotIn("count", dgeq.result)
        
        query_dict = QueryDict("c:count=1")
        dgeq = GenericQuery(Country, query_dict)
        commands.Count()(dgeq, query_dict)
        self.assertIn("count", dgeq.result)
        self.assertEqual(Country.objects.all().count(), dgeq.result["count"])
    
    
    def test_count_invalid_value(self):
        query_dict = QueryDict("c:count=invalid")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Count()(dgeq, query_dict)



class EvaluateTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_not_evaluate(self):
        query_dict = QueryDict("c:evaluate=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertNotIn("rows", dgeq.result)
    
    
    def test_evaluate_invalid(self):
        query_dict = QueryDict("c:evaluate=invalid")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Evaluate()(dgeq, query_dict)
    
    
    def test_evaluate_each_field_type(self):
        dgeq = GenericQuery(Country, QueryDict())
        dgeq.fields = {"name", "population", "rivers", "region", "rivers_length_avg"}
        dgeq.arbitrary_fields = {"rivers_length_avg"}
        dgeq.queryset = Country.objects.all().annotate(rivers_length_avg=models.Avg("rivers__length"))
        
        commands.Evaluate()(dgeq, QueryDict())
        self.assertEqual(Country.objects.all().count(), len(dgeq.result["rows"]))
    
    
    def test_evaluate_no_related(self):
        dgeq = GenericQuery(Country, QueryDict())
        dgeq.fields = {"name", "population", "rivers", "region"}
        dgeq.arbitrary_fields = set()
        dgeq.queryset = Country.objects.all()
        dgeq.related = False
        
        commands.Evaluate()(dgeq, QueryDict())
        self.assertEqual(Country.objects.all().count(), len(dgeq.result["rows"]))
    
    
    def test_evaluate_joins(self):
        dgeq = GenericQuery(Country, QueryDict())
        dgeq.fields = {"name", "population", "rivers", "region"}
        dgeq.arbitrary_fields = set()
        dgeq.queryset = Country.objects.all()
        
        j_rivers = JoinQuery.from_query_value("field=rivers", Country, False)
        j_region = JoinQuery.from_query_value("field=region", Country, False)
        dgeq.add_join("rivers", j_rivers, Country)
        dgeq.add_join("region", j_region, Country)
        
        commands.Evaluate()(dgeq, QueryDict())
        self.assertEqual(Country.objects.all().count(), len(dgeq.result["rows"]))



class FilteringTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_filtering_ok(self):
        query_dict = QueryDict("population=>1000000&name=*republic")
        dgeq = GenericQuery(Country, query_dict)
        commands.Filtering()(dgeq, query_dict)
        self.assertEqual(
            list(Country.objects.filter(population__gt=1000000, name__contains="republic")),
            list(dgeq.queryset)
        )



class JoinTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_join_ok(self):
        query_dict = QueryDict("c:join=field=rivers,field=region&c:join=field=mountains")
        dgeq = GenericQuery(Country, query_dict)
        commands.Join()(dgeq, query_dict)
        
        self.assertIn("rivers", dgeq.joins)
        self.assertIn("mountains", dgeq.joins)
        self.assertIn("region", dgeq.joins)



class ShowTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_no_show(self):
        query_dict = QueryDict()
        dgeq = GenericQuery(Country, query_dict)
        commands.Show()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        fields = {
            "name", "disasters", "id", "area", "forests", "population", "rivers",
            "region", "mountains"
        }
        self.assertEqual(fields, dgeq.fields)
        self.assertEqual(fields, set(dgeq.result["rows"][0].keys()))
    
    
    def test_show(self):
        query_dict = QueryDict("c:show=name")
        dgeq = GenericQuery(Country, query_dict)
        commands.Show()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual({"name"}, dgeq.fields)
        self.assertEqual({"name"}, set(dgeq.result["rows"][0].keys()))
    
    
    def test_hide(self):
        query_dict = QueryDict("c:hide=population,rivers,region,mountains")
        dgeq = GenericQuery(Country, query_dict)
        commands.Show()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        fields = {"name", "disasters", "id", "area", "forests"}
        self.assertEqual(fields, dgeq.fields)
        self.assertEqual(fields, set(dgeq.result["rows"][0].keys()))
    
    
    def test_show_and_hide(self):
        query_dict = QueryDict("c:show=name&c:hide=population,rivers,region,mountains,name")
        dgeq = GenericQuery(Country, query_dict)
        commands.Show()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual({"name"}, dgeq.fields)
        self.assertEqual({"name"}, set(dgeq.result["rows"][0].keys()))



class SortTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_sort(self):
        query_dict = QueryDict("c:sort=name")
        dgeq = GenericQuery(Country, query_dict)
        commands.Sort()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        
        self.assertEqual(
            Country.objects.order_by("name").first().id,
            dgeq.result["rows"][0]["id"]
        )
    
    
    def test_no_sort(self):
        query_dict = QueryDict()
        dgeq = GenericQuery(Country, query_dict)
        commands.Sort()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        
        self.assertEqual(
            Country.objects.first().id,
            dgeq.result["rows"][0]["id"]
        )
    
    
    def test_sort_desc(self):
        query_dict = QueryDict("c:sort=-population")
        dgeq = GenericQuery(Country, query_dict)
        commands.Sort()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual(
            Country.objects.order_by("-population").first().id,
            dgeq.result["rows"][0]["id"]
        )
    
    
    def test_sort_multiple(self):
        query_dict = QueryDict("c:sort=-region.name,population")
        dgeq = GenericQuery(Country, query_dict)
        commands.Sort()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual(
            Country.objects.order_by("-region__name", "population").first().id,
            dgeq.result["rows"][0]["id"]
        )



class SubsetTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_limit_0(self):
        query_dict = QueryDict("c:limit=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Subset()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual(
            Country.objects.all().count(),
            len(dgeq.result["rows"])
        )
    
    
    def test_limit_gt_0(self):
        query_dict = QueryDict("c:limit=89")
        dgeq = GenericQuery(Country, query_dict)
        commands.Subset()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual(
            Country.objects.all()[:89].count(),
            len(dgeq.result["rows"])
        )
    
    
    def test_start(self):
        query_dict = QueryDict("c:start=4&c:limit=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Subset()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual(
            Country.objects.all()[4:].count(),
            len(dgeq.result["rows"])
        )
        self.assertEqual(
            Country.objects.all()[4:][0].id,
            dgeq.result["rows"][0]["id"]
        )
    
    
    def test_start_limit(self):
        query_dict = QueryDict("c:start=4&c:limit=52")
        dgeq = GenericQuery(Country, query_dict)
        commands.Subset()(dgeq, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        self.assertEqual(
            Country.objects.all()[4:56].count(),
            len(dgeq.result["rows"])
        )
        self.assertEqual(
            Country.objects.all()[4:56][0].id,
            dgeq.result["rows"][0]["id"]
        )
    
    
    def test_invalid_value(self):
        query_dict = QueryDict("c:start=-1")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Subset()(dgeq, query_dict)
        
        query_dict = QueryDict("c:limit=-1")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Subset()(dgeq, query_dict)



class TimeTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_time(self):
        query_dict = QueryDict("c:time=1")
        dgeq = GenericQuery(Country, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        commands.Time()(dgeq, query_dict)
        self.assertIn("time", dgeq.result)
        self.assertLess(dgeq.result["time"], 2)
    
    
    def test_no_time(self):
        query_dict = QueryDict("c:time=0")
        dgeq = GenericQuery(Country, query_dict)
        commands.Evaluate()(dgeq, query_dict)
        commands.Time()(dgeq, query_dict)
        self.assertNotIn("time", dgeq.result)
    
    
    def test_invalid_value(self):
        query_dict = QueryDict("c:time=-1")
        dgeq = GenericQuery(Country, query_dict)
        with self.assertRaises(InvalidCommandError):
            commands.Time()(dgeq, query_dict)
