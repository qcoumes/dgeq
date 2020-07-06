from django.db import connections
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django_dummy_app.models import Continent, Country, Mountain, Region, River

from dgeq.exceptions import InvalidCommandError, NotARelatedFieldError
from dgeq.filter import Filter
from dgeq.joins import JoinMixin, JoinQuery
from tests.mixins import QueryTestMixin



class JoinMixinTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_add_join_current_model(self):
        j = JoinMixin()
        other = JoinMixin()
        j.add_join("rivers", other, Country)
        
        self.assertEqual(set(), j.fields)
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(set(), j.many_foreign_fields)
        self.assertEqual({"rivers": other}, j.joins)
    
    
    def test_add_join_current_model_many_fields(self):
        j = JoinMixin()
        rivers = JoinMixin()
        mountains = JoinMixin()
        disasters = JoinMixin()
        j.add_join("rivers", rivers, Country)
        j.add_join("mountains", mountains, Country)
        j.add_join("disasters", disasters, Country)
        
        self.assertEqual(set(), j.fields)
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(set(), j.many_foreign_fields)
        self.assertEqual(
            {"rivers": rivers, "mountains": mountains, "disasters": disasters}, j.joins
        )
    
    
    def test_add_join_related_model(self):
        j = JoinMixin()
        j.add_join("countries__mountains", JoinMixin(), River)
        j.add_join("countries__rivers", JoinMixin(), River)
        j.add_join("countries__disasters", JoinMixin(), River)
        j.add_join("countries__region", JoinMixin(), River)
        
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(set(), j.many_foreign_fields)
        self.assertIn("countries", j.joins)
        
        self.assertEqual({"region"}, j.joins["countries"].unique_foreign_field)
        self.assertEqual(
            {"rivers", "disasters", "mountains"},
            j.joins["countries"].many_foreign_fields
        )
        self.assertEqual(
            {"rivers", "disasters", "mountains", "region"},
            set(j.joins["countries"].joins.keys())
        )
    
    
    def test_add_join_intermediary(self):
        j = JoinMixin()
        j.add_join("countries__region__continent", JoinMixin(), River)
        
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(set(), j.many_foreign_fields)
        self.assertIn("countries", j.joins)
        
        current = j.joins["countries"]
        self.assertEqual({"region"}, current.unique_foreign_field)
        self.assertEqual(set(), current.many_foreign_fields)
        self.assertIn("region", current.joins)
        
        current = current.joins["region"]
        self.assertEqual({"continent"}, current.unique_foreign_field)
        self.assertEqual(set(), current.many_foreign_fields)
        self.assertIn("continent", current.joins)



class JoinTestCase(TestCase, QueryTestMixin):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_join_from_query_ok(self):
        subquery = (
            "field=mountains|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"height", "id", "name"}, j.fields)
        self.assertEqual({"countries"}, j.many_foreign_fields)
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False, Mountain),
                Filter("height", ">1500", False, Mountain),
            ],
            j.filters
        )
    
    
    def test_join_from_query_show_ok(self):
        subquery = (
            "field=mountains|show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"name"}, j.fields)
        self.assertEqual(set(), j.many_foreign_fields)
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False, Mountain),
                Filter("height", ">1500", False, Mountain),
            ],
            j.filters
        )
    
    
    def test_join_from_query_hide_ok(self):
        subquery = (
            "field=mountains|hide=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"height", "id"}, j.fields)
        self.assertEqual({"countries"}, j.many_foreign_fields)
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False, Mountain),
                Filter("height", ">1500", False, Mountain),
            ],
            j.filters
        )
    
    
    def test_join_from_query_show_prevail_over_hide_ok(self):
        subquery = (
            "field=mountains|show=height|hide=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"height"}, j.fields)
        self.assertEqual(set(), j.many_foreign_fields)
        self.assertEqual(set(), j.unique_foreign_field)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False, Mountain),
                Filter("height", ">1500", False, Mountain),
            ],
            j.filters
        )
    
    
    def test_join_from_query_missing_field(self):
        subquery = (
            "show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False)
    
    
    def test_join_from_query_invalid_query(self):
        subquery = (
            "field=mountains|no_equal_sign|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False)
    
    
    def test_join_from_query_not_a_related_field(self):
        subquery = (
            "field=population|show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(NotARelatedFieldError):
            JoinQuery.from_query_value(subquery, Country, False)
    
    
    def test_join_from_query_start_invalid(self):
        subquery = (
            "field=mountains|show=name|start=-1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False)
    
    
    def test_join_from_query_limit_invalid(self):
        subquery = (
            "field=mountains|show=name|start=1|limit=-1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False)
    
    
    def test_join_from_query_filter_invalid(self):
        subquery = (
            "field=mountains|show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False)
    
    
    def test_prefetch_many(self):
        j = JoinQuery.from_query_value("field=mountains|sort=-height", Country, False)
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.fetch(c))
        self.assertEqual("Noshaq", rows[0][0]["name"])
        
        j = JoinMixin()
        j.add_join(
            "regions__continent",
            JoinQuery.from_query_value("field=regions.continent|sort=name", Continent, False),
            Continent
        )
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Continent.objects.all():
                rows.append(j.joins["regions"].fetch(c))
        self.assertEqual("Africa", rows[0][0]["continent"]["name"])
    
    
    def test_prefetch_unique(self):
        j = JoinQuery.from_query_value("field=region|sort=name", Country, False)
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.fetch(c))
        self.assertEqual("Southern Asia", rows[0]["name"])
        
        j = JoinMixin()
        j.add_join(
            "region__continent",
            JoinQuery.from_query_value("field=region.countries|sort=name", Country, False),
            Country
        )
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.joins["region"].fetch(c))
        self.assertEqual("Afghanistan", rows[0]["continent"][0]["name"])
        
        j = JoinMixin()
        j.add_join(
            "region__continent__regions",
            JoinQuery.from_query_value("field=region.continent.regions|sort=name", Country, False),
            Country
        )
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.joins["region"].fetch(c))
        self.assertEqual("Central Asia", rows[0]["continent"]["regions"][0]["name"])
    
    
    def test_prefetch_reduce_num_queries_and_time_many(self):
        j = JoinQuery.from_query_value("field=mountains", Country, False)
        with CaptureQueriesContext(connections['default']) as context:
            for c in Country.objects.all():
                j.fetch(c)
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Country.objects.all()
        queryset = j.prefetch(queryset)
        with CaptureQueriesContext(connections['default']) as context:
            for c in queryset:
                j.fetch(c)
            num_queries_with_prefetch = len(context.captured_queries)
        
        self.assertLess(num_queries_with_prefetch, num_queries_without_prefetch)
    
    
    def test_prefetch_reduce_num_queries_and_time_unique(self):
        j = JoinQuery.from_query_value("field=region", Country, False)
        with CaptureQueriesContext(connections['default']) as context:
            for c in Country.objects.all():
                j.fetch(c)
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Country.objects.all()
        queryset = j.prefetch(queryset)
        with CaptureQueriesContext(connections['default']) as context:
            for c in queryset:
                j.fetch(c)
            num_queries_with_prefetch = len(context.captured_queries)
        
        self.assertLess(num_queries_with_prefetch, num_queries_without_prefetch)
    
    
    def test_prefetch_reduce_num_queries_and_time_unique_and_many(self):
        j = JoinQuery.from_query_value("field=region", Country, False)
        other = JoinQuery.from_query_value("field=mountains", Country, False)
        j.add_join("mountains", other, Country)
        with CaptureQueriesContext(connections['default']) as context:
            for c in Country.objects.all():
                j.fetch(c)
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Country.objects.all()
        queryset = j.prefetch(queryset)
        with CaptureQueriesContext(connections['default']) as context:
            for c in queryset:
                j.fetch(c)
            num_queries_with_prefetch = len(context.captured_queries)
        
        self.assertLess(num_queries_with_prefetch, num_queries_without_prefetch)
    
    
    def test_prefetch_depth_2(self):
        j = JoinMixin()
        j.add_join(
            "countries__mountains",
            JoinQuery.from_query_value(
                "field=countries.mountains|filters=height=>1500|sort=-height|limit=0",
                Region, False
            ),
            Region
        )
        rows_without_prefetch = list()
        with CaptureQueriesContext(connections['default']) as context:
            for c in Region.objects.all():
                rows_without_prefetch.append(j.joins['countries'].fetch(c))
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Region.objects.all()
        queryset = j.joins['countries'].prefetch(queryset)
        rows_with_prefetch = list()
        with CaptureQueriesContext(connections['default']) as context:
            for c in queryset:
                rows_with_prefetch.append(j.joins['countries'].fetch(c))
            num_queries_with_prefetch = len(context.captured_queries)
        
        self.assertLess(num_queries_with_prefetch, num_queries_without_prefetch)
        self.assertEqual(rows_without_prefetch, rows_with_prefetch)
        self.assertEqual("Mount Tahat", rows_with_prefetch[0][0]["mountains"][0]["name"])
    
    
    def test_prefetch_depth_3(self):
        j = JoinMixin()
        j.add_join(
            "regions__countries__mountains",
            JoinQuery.from_query_value(
                "field=regions.countries.mountains|filters=height=>1500|sort=-height|limit=1",
                Continent, False
            ),
            Continent
        )
        rows_without_prefetch = list()
        with CaptureQueriesContext(connections['default']) as context:
            for c in Continent.objects.all():
                rows_without_prefetch.append(j.joins['regions'].fetch(c))
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Continent.objects.all()
        queryset = j.joins['regions'].prefetch(queryset)
        rows_with_prefetch = list()
        with CaptureQueriesContext(connections['default']) as context:
            for c in queryset:
                rows_with_prefetch.append(j.joins['regions'].fetch(c))
            num_queries_with_prefetch = len(context.captured_queries)
        
        self.assertLess(num_queries_with_prefetch, num_queries_without_prefetch)
        self.assertEqual(rows_without_prefetch, rows_with_prefetch)
        self.assertEqual(
            "Mount Tahat",
            rows_with_prefetch[0][0]["countries"][0]["mountains"][0]["name"]
        )
