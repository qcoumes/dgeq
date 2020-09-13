from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Q
from django.test import TestCase

from dgeq import utils
from dgeq.aggregations import Aggregation, Annotation
from dgeq.exceptions import InvalidCommandError
from dgeq.filter import Filter
from dgeq.utils import Censor
from django_dummy_app.models import Country



class AggregationTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(cls.user)
    
    
    def test_functions(self):
        aggregations = [
            Aggregation("population", "population_max", models.Max),
            Aggregation("population", "population_min", models.Min),
            Aggregation("population", "population_avg", models.Avg),
            Aggregation("population", "population_sum", models.Sum),
            Aggregation("population", "population_stddev", models.StdDev),
            Aggregation("population", "population_var", models.Variance),
            Aggregation("population", "population_cnt", models.Count),
        ]
        aggregations = [a.get() for a in aggregations]
        kwargs = dict(aggregations)
        query = Country.objects.all().aggregate(**kwargs)
        
        expected = Country.objects.all().aggregate(
            population_max=models.Max("population"), population_min=models.Min("population"),
            population_avg=models.Avg("population"), population_sum=models.Sum("population"),
            population_cnt=models.Count("population"), population_var=models.Variance("population"),
            population_stddev=models.StdDev("population")
        )
        self.assertEqual(expected, query)
    
    
    def test_from_query_value(self):
        query_string = (
            "field=population|func=avg|to=population_avg,"
            "field=population|func=max|to=population_max,"
            "field=population|func=min|to=population_min"
        )
        aggregations = utils.split_list_strings([query_string], ",")
        aggregations = [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
        aggregations = [a.get() for a in aggregations]
        kwargs = dict(aggregations)
        query = Country.objects.all().aggregate(**kwargs)
        
        expected = Country.objects.all().aggregate(
            population_max=models.Max("population"), population_min=models.Min("population"),
            population_avg=models.Avg("population"),
        )
        self.assertEqual(expected, query)
    
    
    def test_no_equal_subquery_string(self):
        query_string = "population"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
    
    
    def test_missing_func(self):
        query_string = "field=population|to=population_max"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
    
    
    def test_unknown_func(self):
        query_string = "field=population|to=population_max|func=unknown"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
    
    
    def test_missing_field(self):
        query_string = "to=population_max|func=max"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
    
    
    def test_missing_to(self):
        query_string = "field=population|func=max"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
    
    
    def test_already_use_to(self):
        query_string = "field=population|func=max|to=name"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]
    
    
    def test_invalid_to(self):
        query_string = "field=population|func=max|to=1notvalid"
        aggregations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Aggregation.from_query_value(a, Country, self.censor) for a in aggregations]



class AnnotationTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(cls.user)
    
    
    def test_functions(self):
        attributes = [
            "rivers_length_max", "rivers_length_min", "rivers_length_avg", "rivers_length_sum",
            "rivers_length_dcnt", "rivers_length_cnt", # "rivers_length_stddev", "rivers_length_var"
        ]
        annotations = [
            Annotation("rivers__length", "rivers_length_max", models.Max),
            Annotation("rivers__length", "rivers_length_min", models.Min),
            Annotation("rivers__length", "rivers_length_avg", models.Avg),
            Annotation("rivers__length", "rivers_length_sum", models.Sum),
            Annotation("rivers__length", "rivers_length_cnt", models.Count),
            Annotation("rivers__length", "rivers_length_dcnt", utils.DistinctCount),
            # These function aren't supported by sqlite at the moment
            # Annotation("rivers__length", "rivers_length_stddev", models.StdDev),
            # Annotation("rivers__length", "rivers_length_var", models.Variance),
        ]
        query = Country.objects.all()
        for a in annotations:
            query = a.apply(query)
        query = [
            {a: getattr(c, a) for a in attributes} for c in query
        ]
        
        expected = Country.objects.all().annotate(
            rivers_length_max=models.Max("rivers__length"),
            rivers_length_min=models.Min("rivers__length"),
            rivers_length_avg=models.Avg("rivers__length"),
            rivers_length_sum=models.Sum("rivers__length"),
            rivers_length_cnt=models.Count("rivers__length"),
            rivers_length_dcnt=models.Count("rivers__length", distinct=True),
            # rivers_length_var=models.Variance("rivers__length"),
            # rivers_length_stddev=models.StdDev("rivers__length")
        )
        expected = [
            {a: getattr(c, a) for a in attributes} for c in expected
        ]
        self.assertEqual(expected, query)
    
    
    def test_filters(self):
        filters = [Filter("rivers.length", ">2000", False)]
        annotations = [Annotation("rivers__length", "rivers_length_count", models.Count, filters)]
        query = Country.objects.all()
        for a in annotations:
            query = a.apply(query)
        query = [{"name": c.name, "rivers_length_count": c.rivers_length_count} for c in query]
        
        expected = Country.objects.all().annotate(
            rivers_length_count=models.Count("rivers__length", filter=Q(rivers__length__gt=2000)),
        )
        expected = [
            {"name": c.name, "rivers_length_count": c.rivers_length_count} for c in expected
        ]
        self.assertEqual(expected, query)
    
    
    def test_early(self):
        attributes = [
            "rivers_length_max", "rivers_length_min", "rivers_length_avg", "rivers_length_sum",
            "rivers_length_cnt",
            # "rivers_length_stddev", "rivers_length_var",
            "rivers_length_max_early", "rivers_length_min_early", "rivers_length_avg_early",
            "rivers_length_sum_early", "rivers_length_cnt_early",
            # "rivers_length_stddev_early", "rivers_length_var_early",
        ]
        annotations = [
            Annotation("rivers__length", "rivers_length_max_early", models.Max, early=True),
            Annotation("rivers__length", "rivers_length_min_early", models.Min, early=True),
            Annotation("rivers__length", "rivers_length_avg_early", models.Avg, early=True),
            Annotation("rivers__length", "rivers_length_sum_early", models.Sum, early=True),
            Annotation("rivers__length", "rivers_length_cnt_early", models.Count, early=True),
            # These function aren't supported by sqlite at the moment
            # Annotation("rivers__length", "rivers_length_stddev", models.StdDev, early=True),
            # Annotation("rivers__length", "rivers_length_var", models.Variance, early=True),
            
            # Delayed annotation
            Annotation("rivers__length", "rivers_length_max", models.Max),
            Annotation("rivers__length", "rivers_length_min", models.Min),
            Annotation("rivers__length", "rivers_length_avg", models.Avg),
            Annotation("rivers__length", "rivers_length_sum", models.Sum),
            Annotation("rivers__length", "rivers_length_cnt", models.Count),
            # Annotation("rivers__length", "rivers_length_stddev_delayed", models.StdDev),
            # Annotation("rivers__length", "rivers_length_var_delayed", models.Variance),
        ]
        query = Country.objects.all()
        # Applying early annotation
        for a in annotations:
            if a.early:
                query = a.apply(query)
        query = query.filter(region__continent__name="Europe")
        # Applying late annotation
        for a in annotations:
            if not a.early:
                query = a.apply(query)
        query = [
            {a: getattr(c, a) for a in attributes} for c in query
        ]
        
        expected = Country.objects.all().annotate(
            rivers_length_max_early=models.Max("rivers__length"),
            rivers_length_min_early=models.Min("rivers__length"),
            rivers_length_avg_early=models.Avg("rivers__length"),
            rivers_length_sum_early=models.Sum("rivers__length"),
            rivers_length_cnt_early=models.Count("rivers__length"),
            # rivers_length_var_early=models.Variance("rivers__length"),
            # rivers_length_stddev_early=models.StdDev("rivers__length")
        ).filter(region__continent__name="Europe").annotate(
            rivers_length_max=models.Max("rivers__length"),
            rivers_length_min=models.Min("rivers__length"),
            rivers_length_avg=models.Avg("rivers__length"),
            rivers_length_sum=models.Sum("rivers__length"),
            rivers_length_cnt=models.Count("rivers__length"),
            # rivers_length_var=models.Variance("rivers__length"),
            # rivers_length_stddev=models.StdDev("rivers__length")
        )
        expected = [
            {a: getattr(c, a) for a in attributes} for c in expected
        ]
        self.assertEqual(expected, query)
    
    
    def test_from_query_value(self):
        attributes = [
            "population_max", "population_min", "population_avg",
        ]
        query_string = (
            "field=population|func=avg|to=population_avg|filters=rivers.length=<1500|early=0,"
            "field=population|func=max|to=population_max|filters=rivers.length=<1500|early=0,"
            "field=population|func=min|to=population_min|filters=rivers.length=<1500|early=0"
        )
        annotations = utils.split_list_strings([query_string], ",")
        annotations = [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
        query = Country.objects.all()
        for a in annotations:
            query = a.apply(query)
        query = [
            {a: getattr(c, a) for a in attributes} for c in query
        ]
        
        expected = Country.objects.all().annotate(
            population_max=models.Max("population", filter=Q(rivers__length__lt=1500)),
            population_min=models.Min("population", filter=Q(rivers__length__lt=1500)),
            population_avg=models.Avg("population", filter=Q(rivers__length__lt=1500)),
        )
        expected = [
            {a: getattr(c, a) for a in attributes} for c in expected
        ]
        self.assertEqual(expected, query)
    
    
    def test_no_equal_subquery_string(self):
        query_string = "population"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_missing_func(self):
        query_string = "field=population|to=population_max|filters=rivers.length=<1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_unknown_func(self):
        query_string = "field=population|to=population_max|func=unknown|filters=rivers.length=<1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_missing_field(self):
        query_string = "to=population_max|func=max|filters=rivers.length=<1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_missing_to(self):
        query_string = "field=population|func=max|filters=rivers.length=<1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_already_use_to(self):
        query_string = "field=population|func=max|to=name|filters=rivers.length=<1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_invalid_to(self):
        query_string = "field=population|func=max|to=1notvalid|filters=rivers.length=<1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_invalid_filter(self):
        query_string = "field=population|func=max|to=population_max|filters=1500|early=0"
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
    
    
    def test_invalid_early(self):
        query_string = (
            "field=population|func=max|to=population_max|filters=rivers.length=<1500|early=invalid"
        )
        annotations = utils.split_list_strings([query_string], ",")
        
        with self.assertRaises(InvalidCommandError):
            [Annotation.from_query_value(a, Country, False, self.censor) for a in annotations]
