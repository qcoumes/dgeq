from django.contrib.auth.models import AnonymousUser
from django.db import connections
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from dgeq.exceptions import InvalidCommandError, NotARelatedFieldError
from dgeq.filter import Filter
from dgeq.joins import JoinMixin, JoinQuery
from dgeq.utils import Censor
from django_dummy_app.models import Continent, Country, Mountain, Region, River
from tests.mixins import QueryTestMixin



class JoinMixinTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(user=cls.user)
    
    
    def test_add_join_current_model(self):
        j = JoinMixin()
        other = JoinMixin()
        j.add_join("rivers", other, Country, self.censor)
        
        self.assertEqual(set(), j.fields)
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(set(), j._many_fields)
        self.assertEqual({"rivers": other}, j.joins)
    
    
    def test_add_join_current_model_many_fields(self):
        j = JoinMixin()
        rivers = JoinMixin()
        mountains = JoinMixin()
        disasters = JoinMixin()
        j.add_join("rivers", rivers, Country, self.censor)
        j.add_join("mountains", mountains, Country, self.censor)
        j.add_join("disasters", disasters, Country, self.censor)
        
        self.assertEqual(set(), j.fields)
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(set(), j._many_fields)
        self.assertEqual(
            {"rivers": rivers, "mountains": mountains, "disasters": disasters}, j.joins
        )
    
    
    def test_add_join_related_model(self):
        j = JoinMixin()
        j.add_join("countries__mountains", JoinMixin(), River, self.censor)
        j.add_join("countries__rivers", JoinMixin(), River, self.censor)
        j.add_join("countries__disasters", JoinMixin(), River, self.censor)
        j.add_join("countries__region", JoinMixin(), River, self.censor)
        
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(set(), j._many_fields)
        self.assertIn("countries", j.joins)
        
        self.assertEqual({"region"}, j.joins["countries"]._one_fields)
        self.assertEqual(
            {"rivers", "disasters", "mountains"},
            j.joins["countries"]._many_fields
        )
        self.assertEqual(
            {"rivers", "disasters", "mountains", "region"},
            set(j.joins["countries"].joins.keys())
        )
    
    
    def test_add_join_intermediary(self):
        j = JoinMixin()
        j.add_join("countries__region__continent", JoinMixin(), River, self.censor)
        
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(set(), j._many_fields)
        self.assertIn("countries", j.joins)
        
        current = j.joins["countries"]
        self.assertEqual({"region"}, current._one_fields)
        self.assertEqual(set(), current._many_fields)
        self.assertIn("region", current.joins)
        
        current = current.joins["region"]
        self.assertEqual({"continent"}, current._one_fields)
        self.assertEqual(set(), current._many_fields)
        self.assertIn("continent", current.joins)



class JoinTestCase(TestCase, QueryTestMixin):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
        cls.censor = Censor(user=cls.user)
    
    
    def test_join_from_query_ok(self):
        subquery = (
            "field=mountains|start=1|limit=1|sort=-height|distinct=0|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False, self.censor)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"height", "id", "name"}, j.fields)
        self.assertEqual({"countries"}, j._many_fields)
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False),
                Filter("height", ">1500", False),
            ],
            j.filters
        )
    
    
    def test_join_from_query_show_ok(self):
        subquery = (
            "field=mountains|show=name|start=1|limit=1|sort=-height|distinct=1|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False, self.censor)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"name"}, j.fields)
        self.assertEqual(set(), j._many_fields)
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False),
                Filter("height", ">1500", False),
            ],
            j.filters
        )
    
    
    def test_join_from_query_hide_ok(self):
        subquery = (
            "field=mountains|hide=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False, self.censor)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"height", "id"}, j.fields)
        self.assertEqual({"countries"}, j._many_fields)
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False),
                Filter("height", ">1500", False),
            ],
            j.filters
        )
    
    
    def test_join_from_query_show_prevail_over_hide_ok(self):
        subquery = (
            "field=mountains|show=height|hide=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        j = JoinQuery.from_query_value(subquery, Country, False, self.censor)
        self.assertEqual(Mountain, j.model)
        self.assertEqual("mountains", j.field)
        self.assertEqual({"height"}, j.fields)
        self.assertEqual(set(), j._many_fields)
        self.assertEqual(set(), j._one_fields)
        self.assertEqual(1, j.limit)
        self.assertEqual(1, j.start)
        self.assertEqual(["-height"], j.sort)
        self.assertEqual(
            [
                Filter("height", "<3000", False),
                Filter("height", ">1500", False),
            ],
            j.filters
        )
    
    
    def test_join_from_query_missing_field(self):
        subquery = (
            "show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    
    def test_join_from_query_invalid_query(self):
        subquery = (
            "field=mountains|no_equal_sign|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    
    def test_join_from_query_not_a_related_field(self):
        subquery = (
            "field=population|show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(NotARelatedFieldError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    
    def test_join_from_query_start_invalid(self):
        subquery = (
            "field=mountains|show=name|start=-1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    def test_join_from_query_distinct_invalid(self):
        subquery = (
            "field=mountains|show=name|distinct=-1|limit=1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    
    def test_join_from_query_limit_invalid(self):
        subquery = (
            "field=mountains|show=name|start=1|limit=-1|sort=-height|"
            "filters=height=<3000'height=>1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    
    def test_join_from_query_filter_invalid(self):
        subquery = (
            "field=mountains|show=name|start=1|limit=1|sort=-height|"
            "filters=height=<3000'height1500"
        )
        with self.assertRaises(InvalidCommandError):
            JoinQuery.from_query_value(subquery, Country, False, self.censor)
    
    
    def test_prefetch_many(self):
        j = JoinQuery.from_query_value("field=mountains|sort=-height|distinct=1", Country, False, self.censor)
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.fetch(c))
        self.assertEqual("Noshaq", rows[0][0]["name"])
        
        j = JoinMixin()
        j.add_join(
            "regions__continent",
            JoinQuery.from_query_value("field=regions.continent|sort=name", Continent, False, self.censor),
            Continent, self.censor
        )
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Continent.objects.all():
                rows.append(j.joins["regions"].fetch(c))
        self.assertEqual("Africa", rows[0][0]["continent"]["name"])
    
    
    def test_prefetch_unique(self):
        j = JoinQuery.from_query_value("field=region|sort=name", Country, False, self.censor)
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.fetch(c))
        self.assertEqual("Southern Asia", rows[0]["name"])
        
        j = JoinMixin()
        j.add_join(
            "region__continent",
            JoinQuery.from_query_value("field=region.countries|sort=name", Country, False, self.censor),
            Country, self.censor
        )
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.joins["region"].fetch(c))
        self.assertEqual("Afghanistan", rows[0]["continent"][0]["name"])
        
        j = JoinMixin()
        j.add_join(
            "region__continent__regions__name",
            JoinQuery.from_query_value("field=region.continent.regions|sort=name", Country, False, self.censor),
            Country, self.censor
        )
        rows = list()
        with CaptureQueriesContext(connections['default']):
            for c in Country.objects.all():
                rows.append(j.joins["region"].fetch(c))
        self.assertEqual("Central Asia", rows[0]["continent"]["regions"][0]["name"])  # noqa
    
    
    def test_prefetch_reduce_num_queries_and_time_many(self):
        j = JoinQuery.from_query_value("field=mountains|distinct=0", Country, False, self.censor)
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
        j = JoinQuery.from_query_value("field=region", Country, False, self.censor)
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
        j = JoinQuery.from_query_value("field=region", Country, False, self.censor)
        other = JoinQuery.from_query_value("field=mountains", Country, False, self.censor)
        j.add_join("mountains", other, Country, self.censor)
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
                Region, False, self.censor
            ),
            Region, self.censor
        )
        rows_without_prefetch = list()
        with CaptureQueriesContext(connections['default']) as context:
            for c in Region.objects.all():
                rows_without_prefetch.append(j.joins['countries'].fetch(c))
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Region.objects.all()
        queryset = j.joins['countries'].prefetch(queryset)  # noqa
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
                Continent, False, self.censor
            ),
            Continent, self.censor
        )
        rows_without_prefetch = list()
        with CaptureQueriesContext(connections['default']) as context:
            for c in Continent.objects.all():
                rows_without_prefetch.append(j.joins['regions'].fetch(c))
            num_queries_without_prefetch = len(context.captured_queries)
        
        queryset = Continent.objects.all()
        queryset = j.joins['regions'].prefetch(queryset)  # noqa
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
