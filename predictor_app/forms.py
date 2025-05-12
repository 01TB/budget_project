from django import forms
from .models import RentalProperty, LandForSale, Town, AccessType, PaperType, Convenience

# --- Prediction Forms ---
class RentalPredictionForm(forms.Form):
    town = forms.ModelChoiceField(
        queryset=Town.objects.all(),
        empty_label="Select Town",
        widget=forms.HiddenInput(attrs={'id': 'rental_town_id'})
    )
    town_name_display = forms.CharField(
        label="Selected Town",
        disabled=True,
        required=False,
        widget=forms.TextInput(attrs={'id': 'rental_town_name_display', 'placeholder': 'Click on map to select'})
    )
    access_type = forms.ModelChoiceField(
        queryset=AccessType.objects.all(),
        empty_label="Select Access Type",
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )
    property_type = forms.ChoiceField(
        choices=RentalProperty.PROPERTY_TYPE_CHOICES,
        widget=forms.RadioSelect # Consider styling this in template if RadioSelect default isn't good
    )
    num_rooms = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )

    apartment_type = forms.ChoiceField(
        choices=RentalProperty.APARTMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )
    house_type = forms.ChoiceField(
        choices=RentalProperty.HOUSE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )
    has_house_basement = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
    )

    conveniences = forms.ModelMultipleChoiceField(
        queryset=Convenience.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # This is key for checkboxes
        required=False,
        label="Available Conveniences"  # Add a label if you want one
    )

    def clean(self):
        cleaned_data = super().clean()
        property_type = cleaned_data.get('property_type')
        if property_type == 'apartment' and not cleaned_data.get('apartment_type'):
            self.add_error('apartment_type', 'This field is required for apartments.')
        if property_type == 'house' and not cleaned_data.get('house_type'):
            self.add_error('house_type', 'This field is required for houses.')
        return cleaned_data


class LandPredictionForm(forms.Form): # For Option C (Price Per SqM)
    town = forms.ModelChoiceField(
        queryset=Town.objects.all(),
        empty_label="Select Town",
        widget=forms.HiddenInput(attrs={'id': 'land_town_id'})
    )
    town_name_display = forms.CharField(
        label="Selected Town",
        disabled=True,
        required=False,
        widget=forms.TextInput(attrs={'id': 'land_town_name_display', 'placeholder': 'Click on map to select'})
    )
    paper_type = forms.ModelChoiceField(
        queryset=PaperType.objects.all(),
        empty_label="Select Paper Type",
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )
    access_type = forms.ModelChoiceField(
        queryset=AccessType.objects.all(),
        empty_label="Select Access Type",
        required=True,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )
    is_fenced = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
    )
    is_ready_to_build = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
    )
    # area_sqm is removed for Option C prediction form

# --- CRUD ModelForms ---
class BaseStyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.EmailInput, forms.Textarea)):
                current_class = field.widget.attrs.get('class', '')
                field.widget.attrs.update({'class': f'{current_class} w-full p-2 border border-gray-300 rounded mt-1'.strip()})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
            # CheckboxSelectMultiple (for ManyToMany) usually needs template-side styling

class RentalPropertyForm(BaseStyledModelForm):
    class Meta:
        model = RentalProperty
        exclude = ['created_at', 'updated_at']
        widgets = {
            'conveniences': forms.CheckboxSelectMultiple,
        }

class LandForSaleForm(BaseStyledModelForm):
    class Meta:
        model = LandForSale
        exclude = ['created_at', 'updated_at', 'price_per_sqm'] # price_per_sqm is auto-calculated

# --- CRUD Forms for Lookup Tables ---
class AccessTypeForm(BaseStyledModelForm):
    class Meta:
        model = AccessType
        fields = ['name', 'description']

class PaperTypeForm(BaseStyledModelForm):
    class Meta:
        model = PaperType
        fields = ['name', 'description']

class ConvenienceForm(BaseStyledModelForm):
    class Meta:
        model = Convenience
        fields = ['name', 'description']

# --- CSV Import Form ---
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File")
    model_type = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('town', 'Towns'),
            ('access_type', 'Access Types'),
            ('paper_type', 'Paper Types'),
            ('convenience', 'Convenience Types'),
            ('rental', 'Rental Properties'),
            ('land', 'Land For Sale'),
        ],
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded mt-1'})
    )