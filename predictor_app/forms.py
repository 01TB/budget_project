from django import forms
from .models import RentalProperty, LandForSale, Town

class RentalPredictionForm(forms.Form):
    town = forms.ModelChoiceField(queryset=Town.objects.all(), empty_label="Select Town", widget=forms.HiddenInput(attrs={'id': 'rental_town_id'})) # Will be set by map
    town_name_display = forms.CharField(label="Selected Town", disabled=True, required=False, widget=forms.TextInput(attrs={'id': 'rental_town_name_display', 'placeholder': 'Click on map to select'}))
    access_type = forms.ChoiceField(choices=RentalProperty.ACCESS_CHOICES)
    property_type = forms.ChoiceField(choices=RentalProperty.PROPERTY_TYPE_CHOICES, widget=forms.RadioSelect)
    num_rooms = forms.IntegerField(min_value=1, initial=1)

    # Apartment specific (show/hide with JS later)
    apartment_type = forms.ChoiceField(choices=[('', '---')] + list(RentalProperty.APARTMENT_TYPE_CHOICES), required=False)

    # House specific (show/hide with JS later)
    house_type = forms.ChoiceField(choices=[('', '---')] + list(RentalProperty.HOUSE_TYPE_CHOICES), required=False)
    has_house_basement = forms.BooleanField(required=False)

    # Conveniences
    has_showers_toilets = forms.BooleanField(required=False)
    has_garage = forms.BooleanField(required=False)
    has_garden = forms.BooleanField(required=False)
    has_parking = forms.BooleanField(required=False)
    has_surveillance_system = forms.BooleanField(required=False)
    has_dishwasher = forms.BooleanField(required=False)
    has_washing_machine = forms.BooleanField(required=False)
    has_internet_access = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        property_type = cleaned_data.get('property_type')
        if property_type == 'apartment' and not cleaned_data.get('apartment_type'):
            self.add_error('apartment_type', 'This field is required for apartments.')
        if property_type == 'house' and not cleaned_data.get('house_type'):
            self.add_error('house_type', 'This field is required for houses.')
        return cleaned_data


class LandPredictionForm(forms.Form):
    town = forms.ModelChoiceField(queryset=Town.objects.all(), empty_label="Select Town", widget=forms.HiddenInput(attrs={'id': 'land_town_id'}))
    town_name_display = forms.CharField(label="Selected Town", disabled=True, required=False, widget=forms.TextInput(attrs={'id': 'land_town_name_display', 'placeholder': 'Click on map to select'}))
    paper_type = forms.ChoiceField(choices=LandForSale.PAPER_TYPE_CHOICES)
    access_type = forms.ChoiceField(choices=LandForSale.ACCESS_CHOICES)
    is_fenced = forms.BooleanField(required=False)
    is_ready_to_build = forms.BooleanField(required=False)
    area_sqm = forms.DecimalField(min_value=1, label="Area (sqm)")


class RentalPropertyForm(forms.ModelForm):
    class Meta:
        model = RentalProperty
        exclude = ['created_at', 'updated_at']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'town': forms.Select(attrs={'class': 'form-select w-full p-2 border rounded'}),
            # Add more widgets if needed for styling
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.EmailInput)):
                field.widget.attrs.update({'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
            elif isinstance(field.widget, forms.CheckboxInput):
                 field.widget.attrs.update({'class': 'mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
            elif isinstance(field.widget, forms.RadioSelect):
                 # RadioSelect needs special handling, usually in the template
                 pass


class LandForSaleForm(forms.ModelForm):
    class Meta:
        model = LandForSale
        exclude = ['created_at', 'updated_at']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'area_sqm': forms.NumberInput(attrs={'step': '0.01'}),
            'town': forms.Select(attrs={'class': 'form-select w-full p-2 border rounded'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.EmailInput)):
                field.widget.attrs.update({'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
            elif isinstance(field.widget, forms.CheckboxInput):
                 field.widget.attrs.update({'class': 'mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File")
    model_type = forms.ChoiceField(choices=[
        ('rental', 'Rental Properties'),
        ('land', 'Land For Sale'),
        ('town', 'Towns') # Added town import
    ])