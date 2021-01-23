from django.urls import path

from . import views


app_name = 'ask'

urlpatterns = [
    path(r'continent/', views.continent, name='continent'),
    path(r'continent_no_user/', views.continent_no_user, name='continent_no_user'),
    path(r'region/', views.region, name='region'),
    path(r'country/', views.country, name='country'),
    path(r'river/', views.river, name='river'),
    path(r'mountain/', views.mountain, name='mountain'),
    path(r'forest/', views.forest, name='forest'),
    path(r'disaster/', views.disaster, name='disaster'),
]
