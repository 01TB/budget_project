from django.urls import path
from .views import (
    HomePageView, PredictRentalView, PredictLandView,
    RentalPropertyListView, RentalPropertyCreateView, RentalPropertyUpdateView, RentalPropertyDeleteView,
    LandForSaleListView, LandForSaleCreateView, LandForSaleUpdateView, LandForSaleDeleteView,
    ImportCSVView, get_towns_for_map,
    # CRUD for Lookup Tables
    AccessTypeListView, AccessTypeCreateView, AccessTypeUpdateView, AccessTypeDeleteView,
    PaperTypeListView, PaperTypeCreateView, PaperTypeUpdateView, PaperTypeDeleteView,
    ConvenienceListView, ConvenienceCreateView, ConvenienceUpdateView, ConvenienceDeleteView,
)

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('predict/rental/', PredictRentalView.as_view(), name='predict_rental'),
    path('predict/land/', PredictLandView.as_view(), name='predict_land'),

    path('crud/rentals/', RentalPropertyListView.as_view(), name='rentalproperty_list'),
    path('crud/rentals/new/', RentalPropertyCreateView.as_view(), name='rentalproperty_new'),
    path('crud/rentals/<int:pk>/edit/', RentalPropertyUpdateView.as_view(), name='rentalproperty_edit'),
    path('crud/rentals/<int:pk>/delete/', RentalPropertyDeleteView.as_view(), name='rentalproperty_delete'),

    path('crud/lands/', LandForSaleListView.as_view(), name='landforsale_list'),
    path('crud/lands/new/', LandForSaleCreateView.as_view(), name='landforsale_new'),
    path('crud/lands/<int:pk>/edit/', LandForSaleUpdateView.as_view(), name='landforsale_edit'),
    path('crud/lands/<int:pk>/delete/', LandForSaleDeleteView.as_view(), name='landforsale_delete'),

    path('import-csv/', ImportCSVView.as_view(), name='import_csv'),
    path('api/get-towns-for-map/', get_towns_for_map, name='get_towns_for_map'),

    # CRUD URLs for AccessType
    path('crud/access-types/', AccessTypeListView.as_view(), name='accesstype_list'),
    path('crud/access-types/new/', AccessTypeCreateView.as_view(), name='accesstype_new'),
    path('crud/access-types/<int:pk>/edit/', AccessTypeUpdateView.as_view(), name='accesstype_edit'),
    path('crud/access-types/<int:pk>/delete/', AccessTypeDeleteView.as_view(), name='accesstype_delete'),

    # CRUD URLs for PaperType
    path('crud/paper-types/', PaperTypeListView.as_view(), name='papertype_list'),
    path('crud/paper-types/new/', PaperTypeCreateView.as_view(), name='papertype_new'),
    path('crud/paper-types/<int:pk>/edit/', PaperTypeUpdateView.as_view(), name='papertype_edit'),
    path('crud/paper-types/<int:pk>/delete/', PaperTypeDeleteView.as_view(), name='papertype_delete'),

    # CRUD URLs for Convenience
    path('crud/conveniences/', ConvenienceListView.as_view(), name='convenience_list'),
    path('crud/conveniences/new/', ConvenienceCreateView.as_view(), name='convenience_new'),
    path('crud/conveniences/<int:pk>/edit/', ConvenienceUpdateView.as_view(), name='convenience_edit'),
    path('crud/conveniences/<int:pk>/delete/', ConvenienceDeleteView.as_view(), name='convenience_delete'),
]