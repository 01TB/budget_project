from django.contrib import admin
from .models import Town, RentalProperty, LandForSale

class TownAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

class RentalPropertyAdmin(admin.ModelAdmin):
    list_display = ('property_type', 'town', 'access_type', 'num_rooms', 'price', 'created_at')
    list_filter = ('property_type', 'town', 'access_type')
    search_fields = ('town__name',)
    fieldsets = (
        (None, {'fields': ('town', 'access_type', 'property_type', 'num_rooms', 'price')}),
        ('Apartment Specific', {'classes': ('collapse',), 'fields': ('apartment_type',)}),
        ('House Specific', {'classes': ('collapse',), 'fields': ('house_type', 'has_house_basement')}),
        ('Conveniences', {'classes': ('collapse',), 'fields': (
            'has_showers_toilets', 'has_garage', 'has_garden', 'has_parking',
            'has_surveillance_system', 'has_dishwasher', 'has_washing_machine', 'has_internet_access'
        )}),
    )

class LandForSaleAdmin(admin.ModelAdmin):
    list_display = ('town', 'paper_type', 'access_type', 'area_sqm', 'is_fenced', 'is_ready_to_build', 'price', 'created_at')
    list_filter = ('town', 'paper_type', 'access_type', 'is_fenced', 'is_ready_to_build')
    search_fields = ('town__name',)

admin.site.register(Town, TownAdmin)
admin.site.register(RentalProperty, RentalPropertyAdmin)
admin.site.register(LandForSale, LandForSaleAdmin)