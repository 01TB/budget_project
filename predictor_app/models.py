from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify  # For generating slugs if needed, or for default names


# New Models for Choices / Lookup Tables
class AccessType(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Internal identifier, e.g., car_access_parking")
    description = models.CharField(max_length=100, blank=True,
                                   help_text="User-friendly display name, e.g., Car Access + Parking")

    def __str__(self):
        return self.description if self.description else self.name.replace('_', ' ').title()

    def save(self, *args, **kwargs):
        if not self.description:  # Auto-generate description if empty
            self.description = self.name.replace('_', ' ').title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name = "Access Type"
        verbose_name_plural = "Access Types"


class PaperType(models.Model):  # Specific to Land
    name = models.CharField(max_length=50, unique=True, help_text="Internal identifier, e.g., titre_propriete")
    description = models.CharField(max_length=100, blank=True,
                                   help_text="User-friendly display name, e.g., Titre de propriété (French)")

    def __str__(self):
        return self.description if self.description else self.name.replace('_', ' ').title()

    def save(self, *args, **kwargs):
        # Auto-populate French descriptions if name matches known values and description is blank
        if not self.description:
            if self.name == 'titre_propriete':
                self.description = 'Titre de propriété'
            elif self.name == 'acte_juridique':
                self.description = 'Acte juridique'
            elif self.name == 'plan_cadastre':
                self.description = 'Plan cadastre'
            else:  # Default auto-generation
                self.description = self.name.replace('_', ' ').title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name = "Paper Type"
        verbose_name_plural = "Paper Types"


class Convenience(models.Model):  # Primarily for RentalProperty
    name = models.CharField(max_length=50, unique=True,
                            help_text="Internal identifier, e.g., has_garage, internet_access")
    description = models.CharField(max_length=100, blank=True,
                                   help_text="User-friendly display name, e.g., Garage, Internet Access")

    def __str__(self):
        return self.description if self.description else self.name.replace('has_', '').replace('_', ' ').title()

    def save(self, *args, **kwargs):
        if not self.description:  # Auto-generate description if empty
            self.description = self.name.replace('has_', '').replace('_', ' ').title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name = "Convenience"
        verbose_name_plural = "Conveniences"


class Town(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Town"
        verbose_name_plural = "Towns"


class RentalProperty(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
    ]
    APARTMENT_TYPE_CHOICES = [
        ('', '---------'),
        ('T1', 'T1'), ('T2', 'T2'), ('T3', 'T3'),
        ('T4', 'T4'), ('T5', 'T5'), ('T6', 'T6'),
    ]
    HOUSE_TYPE_CHOICES = [
        ('', '---------'),
        ('F1', 'F1'), ('F2', 'F2'), ('F3', 'F3'),
        ('F4', 'F4'), ('F5', 'F5'), ('F6', 'F6'),
    ]

    town = models.ForeignKey(Town, on_delete=models.CASCADE, related_name='rental_properties')
    access_type = models.ForeignKey(AccessType, on_delete=models.SET_NULL, null=True, blank=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)

    num_rooms = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Actual rent price for training data")

    apartment_type = models.CharField(max_length=10, choices=APARTMENT_TYPE_CHOICES, null=True, blank=True)
    house_type = models.CharField(max_length=10, choices=HOUSE_TYPE_CHOICES, null=True, blank=True)
    has_house_basement = models.BooleanField(default=False, help_text="Is there a basement (specific to houses)?")

    conveniences = models.ManyToManyField(Convenience, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_property_type_display()} in {self.town.name} (${self.price or 0:,.2f})"  # Added price formatting

    class Meta:
        verbose_name = "Rental Property"
        verbose_name_plural = "Rental Properties"
        ordering = ['-created_at']


class LandForSale(models.Model):
    town = models.ForeignKey(Town, on_delete=models.CASCADE, related_name='lands_for_sale')
    paper_type = models.ForeignKey(PaperType, on_delete=models.SET_NULL, null=True, blank=True)
    access_type = models.ForeignKey(AccessType, on_delete=models.SET_NULL, null=True, blank=True)

    is_fenced = models.BooleanField(default=False)
    is_ready_to_build = models.BooleanField(default=False)

    area_sqm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                   help_text="Area in square meters")
    price = models.DecimalField(max_digits=14, decimal_places=2, help_text="Actual sale price for training data")

    price_per_sqm = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, editable=False,
                                        help_text="Price per Square Meter (auto-calculated)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.price and self.area_sqm and self.area_sqm > 0:
            self.price_per_sqm = self.price / self.area_sqm
        else:
            self.price_per_sqm = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Land in {self.town.name} ({self.area_sqm or 'N/A'} sqm) - (${self.price or 0:,.2f})"  # Added price formatting

    class Meta:
        verbose_name = "Land For Sale"
        verbose_name_plural = "Lands For Sale"
        ordering = ['-created_at']