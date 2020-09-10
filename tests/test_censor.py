from django.contrib.auth.models import Permission, User
from django.test import TestCase

from dgeq.censor import Censor
from dgeq.exceptions import UnknownFieldError
from django_dummy_app.models import Country



class CensorTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("test")
        cls.user.user_permissions.add(Permission.objects.get(codename='view_country'))
        cls.user.user_permissions.add(Permission.objects.get(codename='view_river'))
    
    
    def test_is_private_permission(self):
        censor = Censor(self.user, use_permissions=True)
        self.assertTrue(censor.is_private(Country, "mountains"))
        self.assertFalse(censor.is_private(Country, "rivers"))
    
    
    def test_is_private_permission_unknown_field(self):
        censor = Censor(self.user, use_permissions=True)
        with self.assertRaises(UnknownFieldError):
            self.assertTrue(censor.is_private(Country, "unknown"))
    
    
    def test_is_private_public(self):
        censor = Censor(self.user, public={Country: ["population"]})
        self.assertTrue(censor.is_private(Country, "mountains"))
        self.assertFalse(censor.is_private(Country, "population"))
    
    
    def test_is_private(self):
        censor = Censor(self.user, private={Country: ["population"]})
        self.assertTrue(censor.is_private(Country, "population"))
        self.assertFalse(censor.is_private(Country, "rivers"))
    
    
    def test_is_public(self):
        censor = Censor(self.user, private={Country: ["population"]})
        self.assertTrue(censor.is_public(Country, "rivers"))
        self.assertFalse(censor.is_public(Country, "population"))
    
    
    def test_censor(self):
        censor = Censor(self.user, private={Country: ["population", "rivers"]})
        self.assertEqual(
            {"name", "id", "area"},
            censor.censor(Country, {"name", "population", "id", "area", "rivers"})
        )
