from django.db import models
from django.core.validators import MinValueValidator

class Town(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # Add any other town-specific data if needed (e.g., region, country)

    def __str__(self):
        return self.name

class RentalProperty(models.Model):
    ACCESS_CHOICES = [
        ('without_access', 'Without Access'),
        ('motorcycle_access', 'Motorcycle Access'),
        ('car_access', 'Car Access'),
        ('car_access_parking', 'Car Access + Parking'),
    ]
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
    ]
    APARTMENT_TYPE_CHOICES = [
        ('T1', 'T1'), ('T2', 'T2'), ('T3', 'T3'),
        ('T4', 'T4'), ('T5', 'T5'), ('T6', 'T6'),
    ]
    HOUSE_TYPE_CHOICES = [
        ('F1', 'F1'), ('F2', 'F2'), ('F3', 'F3'),
        ('F4', 'F4'), ('F5', 'F5'), ('F6', 'F6'),
    ]

    town = models.ForeignKey(Town, on_delete=models.CASCADE, related_name='rental_properties')
    access_type = models.CharField(max_length=50, choices=ACCESS_CHOICES)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)

    # Common fields
    num_rooms = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)]) # Primarily for houses, but can be used for apartments too
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual rent price for training data") # Dependent variable

    # Apartment specific
    apartment_type = models.CharField(max_length=10, choices=APARTMENT_TYPE_CHOICES, null=True, blank=True)

    # House specific
    house_type = models.CharField(max_length=10, choices=HOUSE_TYPE_CHOICES, null=True, blank=True)
    has_house_basement = models.BooleanField(default=False)

    # Conveniences (Boolean fields are easier for linear regression than ManyToMany)
    has_showers_toilets = models.BooleanField(default=False)
    has_garage = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False) # Could be distinct from access_type parking
    has_surveillance_system = models.BooleanField(default=False)
    has_dishwasher = models.BooleanField(default=False)
    has_washing_machine = models.BooleanField(default=False)
    has_internet_access = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_property_type_display()} in {self.town.name} - {self.price}"

    # You might add a clean method here to ensure apartment_type is set if property_type is apartment, etc.

class LandForSale(models.Model):
    PAPER_TYPE_CHOICES = [
        ('titre_propriete', 'Titre de propriété'),
        ('acte_juridique', 'Acte juridique'),
        ('plan_cadastre', 'Plan cadastre'),
    ]
    ACCESS_CHOICES = RentalProperty.ACCESS_CHOICES # Reuse choices

    town = models.ForeignKey(Town, on_delete=models.CASCADE, related_name='lands_for_sale')
    paper_type = models.CharField(max_length=50, choices=PAPER_TYPE_CHOICES)
    access_type = models.CharField(max_length=50, choices=ACCESS_CHOICES)
    is_fenced = models.BooleanField(default=False)
    is_ready_to_build = models.BooleanField(default=False)
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Area in square meters") # Important predictor
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Actual sale price for training data") # Dependent variable

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Land in {self.town.name} ({self.area_sqm} sqm) - {self.price}"