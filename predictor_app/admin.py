from django.contrib import admin
from .models import (
    Town,
    AccessType,
    PaperType,
    Convenience,
    RentalProperty,
    LandForSale
)


class AccessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


class PaperTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


class ConvenienceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


class TownAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)


class RentalPropertyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'town', 'access_type', 'property_type', 'num_rooms', 'price', 'created_at')
    list_filter = ('property_type', 'town', 'access_type', 'conveniences')
    search_fields = ('town__name', 'price')
    filter_horizontal = ('conveniences',)

    fieldsets = (
        (None, {'fields': ('town', 'access_type', 'property_type', 'num_rooms', 'price')}),
        ('Apartment Specific', {
            'classes': ('collapse',),
            'fields': ('apartment_type',)
        }),
        ('House Specific', {
            'classes': ('collapse',),
            'fields': ('house_type', 'has_house_basement')
        }),
        ('Conveniences', {
            'classes': ('collapse',),
            'fields': ('conveniences',)
        }),
    )


class LandForSaleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'town', 'paper_type', 'access_type', 'area_sqm', 'price', 'price_per_sqm', 'is_fenced',
                    'is_ready_to_build', 'created_at')
    list_filter = ('town', 'paper_type', 'access_type', 'is_fenced', 'is_ready_to_build')
    search_fields = ('town__name', 'price', 'area_sqm')
    readonly_fields = ('price_per_sqm',)


admin.site.register(Town, TownAdmin)
admin.site.register(AccessType, AccessTypeAdmin)
admin.site.register(PaperType, PaperTypeAdmin)
admin.site.register(Convenience, ConvenienceAdmin)
admin.site.register(RentalProperty, RentalPropertyAdmin)
admin.site.register(LandForSale, LandForSaleAdmin)