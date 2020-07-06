from django.contrib import admin

from .models import Continent, Country, Disaster, Forest, Mountain, Region, River



@admin.register(Continent)
class ContinentAdmin(admin.ModelAdmin):
    """Admin interface for Continent."""
    list_display = ('id', 'name')



@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """Admin interface for Region."""
    list_display = ('id', 'name', 'continent')



@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin interface for Country."""
    list_display = ('id', 'name', 'region')



@admin.register(River)
class RiverAdmin(admin.ModelAdmin):
    """Admin interface for River."""
    list_display = ('id', 'name', 'length', 'discharge')



@admin.register(Forest)
class ForestAdmin(admin.ModelAdmin):
    """Admin interface for Forest."""
    list_display = ('id', 'name', 'area')



@admin.register(Mountain)
class MountainAdmin(admin.ModelAdmin):
    """Admin interface for Mountain."""
    
    list_display = ('id', 'name', 'height')



@admin.register(Disaster)
class DisasterAdmin(admin.ModelAdmin):
    """Admin interface for Disaster."""
    
    list_display = ('id', 'event', 'country', 'date')
