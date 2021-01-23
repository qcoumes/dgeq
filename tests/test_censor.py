from unittest import mock

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings

from dgeq.censor import Censor
from dgeq.exceptions import UnknownFieldError
from django_dummy_app.models import Country, Mountain, River



class CensorTestCase(TestCase):
    fixtures = ["tests/django_dummy_app/geography_data.json"]
    
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("test")
        cls.user.user_permissions.add(Permission.objects.get(codename='view_country'))
        cls.user.user_permissions.add(Permission.objects.get(codename='view_river'))

    
    @mock.patch("dgeq.censor.DGEQ_PRIVATE_FIELDS", {Mountain: 'height'})
    @mock.patch("dgeq.censor.DGEQ_PUBLIC_FIELDS", {River: "name"})
    def test_is_private_settings(self):
        censor = Censor()
        self.assertTrue(censor.is_private(Mountain, 'height'))
        self.assertFalse(censor.is_private(Mountain, 'name'))
        self.assertTrue(censor.is_private(River, 'length'))
        self.assertFalse(censor.is_private(River, 'name'))
    
    
    def test_is_private_permission(self):
        censor = Censor(user=self.user, use_permissions=True)
        self.assertTrue(censor.is_private(Country, "mountains"))
        self.assertFalse(censor.is_private(Country, "rivers"))
    
    
    def test_permission_true_user_none(self):
        with self.assertRaises(ValueError):
            Censor(use_permissions=True)
    
    
    def test_is_private_permission_unknown_field(self):
        censor = Censor(user=self.user, use_permissions=True)
        with self.assertRaises(UnknownFieldError):
            self.assertTrue(censor.is_private(Country, "unknown"))
    
    
    def test_is_private_public(self):
        censor = Censor(public={Country: ["population"]})
        self.assertTrue(censor.is_private(Country, "mountains"))
        self.assertFalse(censor.is_private(Country, "population"))
    
    
    def test_is_private(self):
        censor = Censor(private={Country: ["population"]})
        self.assertTrue(censor.is_private(Country, "population"))
        self.assertFalse(censor.is_private(Country, "rivers"))
    
    
    def test_is_public(self):
        censor = Censor(private={Country: ["population"]})
        self.assertTrue(censor.is_public(Country, "rivers"))
        self.assertFalse(censor.is_public(Country, "population"))
    
    
    def test_censor(self):
        censor = Censor(private={Country: ["population", "rivers"]})
        self.assertEqual(
            {"name", "id", "area"},
            censor.censor(Country, {"name", "population", "id", "area", "rivers"})
        )
