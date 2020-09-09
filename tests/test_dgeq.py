from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, Permission, User
from django.http import QueryDict
from django.test import TestCase

from dgeq import GenericQuery, commands
from django_dummy_app.models import Country, Region, River



class DgeqTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = AnonymousUser()
    
    
    @patch("dgeq.dgeq.DGEQ_COMMANDS", [commands.Case(), commands.Related(), commands.Time()])
    def test_step(self):
        query_dict = QueryDict("c:case=0&c:related=0&c:time=1")
        dgeq = GenericQuery(self.user, Country, query_dict)
        self.assertEqual(True, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step()
        self.assertEqual(False, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step()
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step()
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertIn("time", dgeq.result)
    
    
    @patch("dgeq.dgeq.DGEQ_COMMANDS", [commands.Case(), commands.Related(), commands.Time()])
    def test_2_step_1_step(self):
        query_dict = QueryDict("c:case=0&c:related=0&c:time=1")
        dgeq = GenericQuery(self.user, Country, query_dict)
        self.assertEqual(True, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step(2)
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step()
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertIn("time", dgeq.result)
    
    
    @patch("dgeq.dgeq.DGEQ_COMMANDS", [commands.Case(), commands.Related(), commands.Time()])
    def test_1_step_2_step(self):
        query_dict = QueryDict("c:case=0&c:related=0&c:time=1")
        dgeq = GenericQuery(self.user, Country, query_dict)
        self.assertEqual(True, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step()
        self.assertEqual(False, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step(2)
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertIn("time", dgeq.result)
    
    
    @patch("dgeq.dgeq.DGEQ_COMMANDS", [commands.Case(), commands.Related(), commands.Time()])
    def test_step_none(self):
        query_dict = QueryDict("c:case=0&c:related=0&c:time=1")
        dgeq = GenericQuery(self.user, Country, query_dict)
        self.assertEqual(True, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step(None)
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertIn("time", dgeq.result)
    
    
    @patch("dgeq.dgeq.DGEQ_COMMANDS", [commands.Case(), commands.Related(), commands.Time()])
    def test_1_step_none(self):
        query_dict = QueryDict("c:case=0&c:related=0&c:time=1")
        dgeq = GenericQuery(self.user, Country, query_dict)
        self.assertEqual(True, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step()
        self.assertEqual(False, dgeq.case)
        self.assertEqual(True, dgeq.related)
        self.assertNotIn("time", dgeq.result)
        
        dgeq.step(None)
        self.assertEqual(False, dgeq.case)
        self.assertEqual(False, dgeq.related)
        self.assertIn("time", dgeq.result)
    
    
    def test_dgeq_error(self):
        query_dict = QueryDict("c:case=invalid")
        dgeq = GenericQuery(self.user, Country, query_dict)
        res = dgeq.evaluate()
        self.assertEqual(False, res["status"])
        self.assertEqual("INVALID_VALUE_ERROR", res["code"])
        self.assertIn("command", res)
        self.assertEqual("c:case", res["command"])
    
    
    def test_evaluate_simple(self):
        query_dict = QueryDict("name=Germany")
        dgeq = GenericQuery(self.user, Country, query_dict)
        res = dgeq.evaluate()
        self.assertEqual(True, res["status"])
        self.assertEqual(Country.objects.get(name="Germany").id, res["rows"][0]["id"])
        self.assertEqual("Germany", res["rows"][0]["name"])
        self.assertEqual(1, len(res["rows"]))
    
    
    def test_advanced_1(self):
        """List name of rivers crossing more than 3 european country. Also
        display countries' name in the result"""
        query_dict = QueryDict(
            "c:annotate=field=countries|func=count|to=eu_countries_count"
            "|filters=countries.region.continent.name=Europe|early=1"
            "&eu_countries_count=[3&c:show=name,countries&c:limit=0"
            "&c:join=field=countries|show=name"
        )
        dgeq = GenericQuery(self.user, River, query_dict)
        res = dgeq.evaluate()
        expected = {
            'status': True,
            'rows':   [
                {
                    'name':               'Desna',
                    'eu_countries_count': 3,
                    'countries':          [
                        {'name': 'Belarus'},
                        {'name': 'Russia'},
                        {'name': 'Ukraine'}
                    ]
                },
                {
                    'name':               'Oder',
                    'eu_countries_count': 3,
                    'countries':          [
                        {'name': 'Czech Republic'},
                        {'name': 'Germany'},
                        {'name': 'Poland'}
                    ]
                },
                {
                    'name':               'Daugava',
                    'eu_countries_count': 3,
                    'countries':          [
                        {'name': 'Belarus'},
                        {'name': 'Latvia'},
                        {'name': 'Russia'}
                    ]
                },
                {
                    'name':               'Vistula',
                    'eu_countries_count': 3,
                    'countries':          [
                        {'name': 'Belarus'},
                        {'name': 'Poland'},
                        {'name': 'Ukraine'}
                    ]
                },
                {
                    'name':               'Dnieper',
                    'eu_countries_count': 3,
                    'countries':          [
                        {'name': 'Belarus'},
                        {'name': 'Russia'},
                        {'name': 'Ukraine'}
                    ]
                },
                {
                    'name':               'Rhine',
                    'eu_countries_count': 9,
                    'countries':          [
                        {'name': 'Austria'},
                        {'name': 'Belgium'},
                        {'name': 'France'},
                        {'name': 'Germany'},
                        {'name': 'Italy'},
                        {'name': 'Liechtenstein'},
                        {'name': 'Luxembourg'},
                        {'name': 'Netherlands'},
                        {'name': 'Switzerland'}
                    ]
                },
                {
                    'name':               'Danube',
                    'eu_countries_count': 9,
                    'countries':          [
                        {'name': 'Austria'},
                        {'name': 'Bulgaria'},
                        {'name': 'Croatia'},
                        {'name': 'Germany'},
                        {'name': 'Hungary'},
                        {'name': 'Romania'},
                        {'name': 'Serbia'},
                        {'name': 'Slovakia'},
                        {'name': 'Ukraine'}
                    ]
                }
            ]
        }
        self.assertEqual(expected, res)
    
    
    def test_advanced_2(self):
        """Name, ID and area of countries where the sum of mountain's height is
        more than 100000 meters."""
        query_dict = QueryDict(
            "c:annotate=field=mountains.height|func=sum|to=sum_mountains_height|early=1"
            "&sum_mountains_height=>100000&c:show=name,id,area&c:limit=0&c:sort=name"
        )
        dgeq = GenericQuery(self.user, Country, query_dict)
        res = dgeq.evaluate()
        expected = {
            "status": True,
            "rows":   [
                {
                    "sum_mountains_height": 393601,
                    "area":                 9984670,
                    "id":                   37,
                    "name":                 "Canada"
                },
                {
                    "sum_mountains_height": 967435,
                    "area":                 9600000,
                    "id":                   43,
                    "name":                 "China"
                },
                {
                    "sum_mountains_height": 278368,
                    "area":                 3287263,
                    "id":                   98,
                    "name":                 "India"
                },
                {
                    "sum_mountains_height": 229171,
                    "area":                 1910931,
                    "id":                   99,
                    "name":                 "Indonesia"
                },
                {
                    "sum_mountains_height": 193124,
                    "area":                 1628750,
                    "id":                   100,
                    "name":                 "Iran"
                },
                {
                    "sum_mountains_height": 176128,
                    "area":                 147181,
                    "id":                   144,
                    "name":                 "Nepal"
                },
                {
                    "sum_mountains_height": 288991,
                    "area":                 796095,
                    "id":                   156,
                    "name":                 "Pakistan"
                },
                {
                    "sum_mountains_height": 189719,
                    "area":                 17098246,
                    "id":                   171,
                    "name":                 "Russia"
                },
                {
                    "sum_mountains_height": 118762,
                    "area":                 142600,
                    "id":                   202,
                    "name":                 "Tajikistan"
                },
                {
                    "sum_mountains_height": 405245,
                    "area":                 9833516,
                    "id":                   219,
                    "name":                 "United States of America"
                }
            ]
        }
        self.assertEqual(expected, res)
    
    
    def test_advanced_3(self):
        """Name of five regions where the country with the lowest population is
        less than 100000. Also display the name of the corresponding country and
        name of the continent the region belong to.
        
        The five regions are the first when sorted by the value of the lower
        population."""
        query_dict = QueryDict(
            "c:annotate=field=countries.population|func=min|to=pop_min|early=1"
            "&pop_min=<10000&c:show=name,countries,continent&c:limit=5&c:sort=pop_min"
            "&c:join=field=continent|show=name"
            "&c:join=field=countries|show=name|sort=population|limit=1"
        )
        dgeq = GenericQuery(self.user, Region, query_dict)
        res = dgeq.evaluate()
        expected = {
            "status": True,
            "rows":   [
                {
                    "name":      "Southern Europe",
                    "pop_min":   800,
                    "continent": {
                        "name": "Europe"
                    },
                    "countries": [
                        {
                            "name": "Holy See"
                        }
                    ]
                },
                {
                    "name":      "Polynesia",
                    "pop_min":   1300,
                    "continent": {
                        "name": "Oceania"
                    },
                    "countries": [
                        {
                            "name": "Tokelau"
                        }
                    ]
                },
                {
                    "name":      "South America",
                    "pop_min":   2900,
                    "continent": {
                        "name": "Americas"
                    },
                    "countries": [
                        {
                            "name": "Falkland Islands (Malvinas)"
                        }
                    ]
                },
                {
                    "name":      "Western Africa",
                    "pop_min":   4000,
                    "continent": {
                        "name": "Africa"
                    },
                    "countries": [
                        {
                            "name": "Saint Helena"
                        }
                    ]
                },
                {
                    "name":      "Latin America & the Caribbean",
                    "pop_min":   5200,
                    "continent": {
                        "name": "Americas"
                    },
                    "countries": [
                        {
                            "name": "Montserrat"
                        }
                    ]
                }
            ]
        }
        self.assertEqual(expected, res)
    
    
    def test_private(self):
        query_dict = QueryDict("c:join=field=rivers&c:sort=name")
        dgeq = GenericQuery(self.user, Country, query_dict, private_fields={
            River:   ["countries", "discharge"],
            Country: ["forests", "mountains", "disasters"]
        })
        res = dgeq.evaluate()
        expected = {
            "status": True,
            "rows":   [
                {
                    "area":       652864,
                    "id":         1,
                    "population": 36296100,
                    "name":       "Afghanistan",
                    "region":     15,
                    "rivers":     [
                        {
                            "length": 2620,
                            "id":     37,
                            "name":   "Amu Darya–Panj"
                        },
                        {
                            "length": 1130,
                            "id":     165,
                            "name":   "Helmand"
                        }
                    ]
                }
            ]
        }
        self.assertEqual(expected, res)
    
    
    def test_private_cause_unknown_field(self):
        query_dict = QueryDict("population=>100000000")
        dgeq = GenericQuery(self.user, Country, query_dict, private_fields={Country: ["population"]})
        res = dgeq.evaluate()
        self.assertIn("code", res)
        self.assertEqual("UNKNOWN_FIELD", res["code"])
    
    
    def test_public(self):
        query_dict = QueryDict("c:join=field=rivers&c:sort=name")
        dgeq = GenericQuery(self.user, Country, query_dict, public_fields={
            River:   ["length", "id", "name"],
            Country: ["area", "id", "population", "name", "region", "rivers"]
        })
        res = dgeq.evaluate()
        expected = {
            "status": True,
            "rows":   [
                {
                    "area":       652864,
                    "id":         1,
                    "population": 36296100,
                    "name":       "Afghanistan",
                    "region":     15,
                    "rivers":     [
                        {
                            "length": 2620,
                            "id":     37,
                            "name":   "Amu Darya–Panj"
                        },
                        {
                            "length": 1130,
                            "id":     165,
                            "name":   "Helmand"
                        }
                    ]
                }
            ]
        }
        self.assertEqual(expected, res)
    
    
    def test_public_cause_unknown_field(self):
        query_dict = QueryDict("area=>100000000")
        dgeq = GenericQuery(self.user, Country, query_dict, public_fields={Country: ["population"]})
        res = dgeq.evaluate()
        self.assertIn("code", res)
        self.assertEqual("UNKNOWN_FIELD", res["code"])
    
    
    def test_permission_and_private(self):
        query_dict = QueryDict("c:join=field=rivers&c:sort=name")
        user = User.objects.create_user("test")
        user.user_permissions.add(Permission.objects.get(codename='view_country'))
        user.user_permissions.add(Permission.objects.get(codename='view_river'))
        dgeq = GenericQuery(user, Country, query_dict, use_permissions=True, private_fields={
            River: ["discharge", "countries"]
        })
        res = dgeq.evaluate()
        expected = {
            "status": True,
            "rows":   [
                {
                    "area":       652864,
                    "id":         1,
                    "population": 36296100,
                    "name":       "Afghanistan",
                    "rivers":     [
                        {
                            "length": 2620,
                            "id":     37,
                            "name":   "Amu Darya–Panj"
                        },
                        {
                            "length": 1130,
                            "id":     165,
                            "name":   "Helmand"
                        }
                    ]
                }
            ]
        }
        self.assertEqual(expected, res)
    
    
    def test_permission_cause_unknown_field(self):
        query_dict = QueryDict("rivers.length=>1000")
        user = User.objects.create_user("test")
        user.user_permissions.add(Permission.objects.get(codename='view_country'))
        dgeq = GenericQuery(user, Country, query_dict, use_permissions=True)
        res = dgeq.evaluate()
        self.assertIn("code", res)
        self.assertEqual("UNKNOWN_FIELD", res["code"])
