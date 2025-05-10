from django.urls import path
from .views import (
    HomePageView, PredictRentalView, PredictLandView,
    RentalPropertyListView, RentalPropertyCreateView, RentalPropertyUpdateView, RentalPropertyDeleteView,
    LandForSaleListView, LandForSaleCreateView, LandForSaleUpdateView, LandForSaleDeleteView,
    ImportCSVView, get_towns_for_map
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
]