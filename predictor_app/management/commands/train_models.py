from django.core.management.base import BaseCommand
from predictor_app.models import RentalProperty, LandForSale  # Assuming models are in the same app
from predictor_app.ml_utils import train_rental_model, train_land_model  # Updated land model name


class Command(BaseCommand):
    help = 'Trains the prediction models for rental properties and land price per sqm'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting model training..."))

        # Training Rental Model
        self.stdout.write(self.style.NOTICE("Fetching rental property data..."))

        rental_properties_qs = RentalProperty.objects.all().prefetch_related(
            'town', 'access_type', 'conveniences'
        )
        rental_data_for_training = []
        for prop in rental_properties_qs:
            if prop.price is None:  # Skip if price is not set
                continue
            rental_data_for_training.append({
                'town_id': prop.town_id,
                'access_type_id': prop.access_type_id,
                'property_type': prop.property_type,
                'num_rooms': prop.num_rooms,
                'price': prop.price,  # Target variable
                'apartment_type': prop.apartment_type if prop.apartment_type else 'None',  # String 'None' for ml_utils
                'house_type': prop.house_type if prop.house_type else 'None',  # String 'None' for ml_utils
                'has_house_basement': prop.has_house_basement,
                'convenience_ids': list(prop.conveniences.values_list('id', flat=True))
            })

        if rental_data_for_training:
            self.stdout.write(f"Training rental model with {len(rental_data_for_training)} records...")
            train_rental_model(rental_data_for_training)
            self.stdout.write(self.style.SUCCESS('Rental model training complete.'))
        else:
            self.stdout.write(self.style.WARNING('No rental data with price found to train the model.'))

        # Training Land Model (Price Per SqM - Option C)
        self.stdout.write(self.style.NOTICE("Fetching land for sale data..."))
        land_properties_qs = LandForSale.objects.filter(
            price__isnull=False, area_sqm__isnull=False, area_sqm__gt=0
        ).prefetch_related('town', 'paper_type', 'access_type')

        land_data_for_training = []
        for land in land_properties_qs:
            land_data_for_training.append({
                'town_id': land.town_id,
                'paper_type_id': land.paper_type_id,
                'access_type_id': land.access_type_id,
                'is_fenced': land.is_fenced,
                'is_ready_to_build': land.is_ready_to_build,
                'price_per_sqm': land.price / land.area_sqm  # Target variable; area_sqm is NOT an input feature here
            })

        if land_data_for_training:
            self.stdout.write(f"Training land (price per sqm) model with {len(land_data_for_training)} records...")
            train_land_model(land_data_for_training)  # train_land_model expects price_per_sqm
            self.stdout.write(self.style.SUCCESS('Land (price per sqm) model training complete.'))
        else:
            self.stdout.write(
                self.style.WARNING('No valid land data (price and area_sqm > 0) found to train the model.'))

        self.stdout.write(self.style.SUCCESS('All model training processes finished.'))