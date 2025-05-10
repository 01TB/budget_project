from django.core.management.base import BaseCommand
from predictor_app.models import RentalProperty, LandForSale
from predictor_app.ml_utils import train_rental_model, train_land_model

class Command(BaseCommand):
    help = 'Trains the prediction models for rental properties and land for sale'

    def handle(self, *args, **options):
        self.stdout.write("Starting model training...")

        # Training Rental Model
        self.stdout.write("Fetching rental property data...")
        rental_data = list(RentalProperty.objects.all().values(
            'town_id', 'access_type', 'property_type', 'num_rooms', 'price',
            'apartment_type', 'house_type', 'has_house_basement',
            'has_showers_toilets', 'has_garage', 'has_garden', 'has_parking',
            'has_surveillance_system', 'has_dishwasher', 'has_washing_machine', 'has_internet_access'
        ))
        if rental_data:
            self.stdout.write(f"Training rental model with {len(rental_data)} records...")
            train_rental_model(rental_data)
            self.stdout.write(self.style.SUCCESS('Rental model training complete.'))
        else:
            self.stdout.write(self.style.WARNING('No rental data found to train the model.'))

        # Training Land Model
        self.stdout.write("Fetching land for sale data...")
        land_data = list(LandForSale.objects.all().values(
            'town_id', 'paper_type', 'access_type', 'is_fenced',
            'is_ready_to_build', 'area_sqm', 'price'
        ))
        if land_data:
            self.stdout.write(f"Training land model with {len(land_data)} records...")
            train_land_model(land_data)
            self.stdout.write(self.style.SUCCESS('Land model training complete.'))
        else:
            self.stdout.write(self.style.WARNING('No land data found to train the model.'))

        self.stdout.write(self.style.SUCCESS('All model training processes finished.'))