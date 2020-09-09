import random

from django.test import TestCase
from django_dummy_app.models import Country, Disaster, River

from dgeq.exceptions import SearchModifierError
from dgeq.filter import Filter



class TypeModifierFilterTestCase(TestCase):
    """Test known type + modifier combination in DEFAULT_FILTERS_TABLE."""
    
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    def test_equal_int(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        f = Filter("population", str(c.population), False)
        queryset = f.apply(queryset)
        
        self.assertEqual([c], list(queryset))
    
    
    def test_equal_str_case_insensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        f = Filter("name", c.name.lower(), False)
        queryset = f.apply(queryset)
        
        self.assertEqual([c], list(queryset))
    
    
    def test_equal_str_case_sensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        f = Filter("name", c.name, True)
        queryset = f.apply(queryset)
        
        self.assertEqual([c], list(queryset))
    
    
    def test_equal_float(self):
        queryset = Country.objects.all()
        f = Filter("population", str(float()), True)
        
        with self.assertRaises(SearchModifierError):
            f.apply(queryset)
    
    
    def test_equal_datetime(self):
        queryset = Disaster.objects.all()
        d = queryset[random.randint(0, queryset.count() - 1)]
        f = Filter("date", d.date.isoformat(), False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(Disaster.objects.filter(date=d.date)), list(queryset))
    
    
    def test_equal_none(self):
        queryset = River.objects.all()
        expected = queryset.filter(discharge=None)
        f = Filter("discharge", "", False)
        queryset = f.apply(queryset)
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_different_int(self):
        queryset = Country.objects.all()
        expected = queryset.exclude(population=600000)
        f = Filter("population", f"!600000", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_different_str_case_insensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.exclude(name__iexact=c.name)
        f = Filter("name", f"!{c.name.lower()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_different_str_case_sensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.exclude(name__exact=c.name)
        f = Filter("name", f"!{c.name}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_different_float(self):
        queryset = Country.objects.all()
        f = Filter("population", f"!{str(float())}", True)
        
        with self.assertRaises(SearchModifierError):
            f.apply(queryset)
    
    
    def test_different_datetime(self):
        queryset = Disaster.objects.all()
        d = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.exclude(date=d.date)
        f = Filter("date", f"!{d.date.isoformat()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_different_none(self):
        queryset = River.objects.all()
        expected = queryset.exclude(discharge=None)
        f = Filter("discharge", "!", False)
        queryset = f.apply(queryset)
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gt_int(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__gt=600000)
        f = Filter("population", f">600000", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gt_str(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__gt=c.name)
        f = Filter("name", f">{c.name}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gt_float(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__gt=600000.0)
        f = Filter("population", f">600000.0", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gt_datetime(self):
        queryset = Disaster.objects.all()
        d = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(date__gt=d.date)
        f = Filter("date", f">{d.date.isoformat()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gt_none(self):
        queryset = River.objects.all()
        f = Filter("discharge", ">", True)
        
        with self.assertRaises(SearchModifierError):
            f.apply(queryset)
    
    
    def test_gte_int(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__gte=600000)
        f = Filter("population", f"[600000", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gte_str(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__gte=c.name)
        f = Filter("name", f"[{c.name}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gte_float(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__gte=600000.0)
        f = Filter("population", f"[600000.0", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gte_datetime(self):
        queryset = Disaster.objects.all()
        d = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(date__gte=d.date)
        f = Filter("date", f"[{d.date.isoformat()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_gte_none(self):
        queryset = River.objects.all()
        f = Filter("discharge", "[", True)
        
        with self.assertRaises(SearchModifierError):
            f.apply(queryset)
    
    
    def test_lt_int(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__lt=600000)
        f = Filter("population", f"<600000", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lt_str(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__lt=c.name)
        f = Filter("name", f"<{c.name}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lt_float(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__lt=600000.0)
        f = Filter("population", f"<600000.0", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lt_datetime(self):
        queryset = Disaster.objects.all()
        d = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(date__lt=d.date)
        f = Filter("date", f"<{d.date.isoformat()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lt_none(self):
        queryset = River.objects.all()
        f = Filter("discharge", "<", True)
        
        with self.assertRaises(SearchModifierError):
            f.apply(queryset)
    
    
    def test_lte_int(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__lte=600000)
        f = Filter("population", f"]600000", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lte_str(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__lte=c.name)
        f = Filter("name", f"]{c.name}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lte_float(self):
        queryset = Country.objects.all()
        expected = queryset.filter(population__lte=600000.0)
        f = Filter("population", f"]600000.0", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lte_datetime(self):
        queryset = Disaster.objects.all()
        d = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(date__lte=d.date)
        f = Filter("date", f"]{d.date.isoformat()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_lte_none(self):
        queryset = River.objects.all()
        f = Filter("discharge", "]", True)
        
        with self.assertRaises(SearchModifierError):
            f.apply(queryset)
    
    
    def test_startswith_str_case_insensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__istartswith=c.name[:3])
        f = Filter("name", f"^{c.name[:3].lower()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_startswith_str_case_sensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__startswith=c.name[0])
        f = Filter("name", f"^{c.name[0]}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_endswith_str_case_insensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__iendswith=c.name[-1])
        f = Filter("name", f"${c.name[-1].lower()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_endswith_str_case_sensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__endswith=c.name[-1])
        f = Filter("name", f"${c.name[-1]}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_contains_str_case_insensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__icontains=c.name[-1])
        f = Filter("name", f"*{c.name[-1].lower()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_contains_str_case_sensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.filter(name__contains=c.name[-1])
        f = Filter("name", f"*{c.name[-1]}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_doesnt_contains_str_case_insensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.exclude(name__icontains=c.name[-1])
        f = Filter("name", f"~{c.name[-1].lower()}", False)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
    
    
    def test_doesnt_contains_str_case_sensitive(self):
        queryset = Country.objects.all()
        c = queryset[random.randint(0, queryset.count() - 1)]
        expected = queryset.exclude(name__contains=c.name[-1])
        f = Filter("name", f"~{c.name[-1]}", True)
        queryset = f.apply(queryset)
        
        self.assertEqual(list(expected), list(queryset))
