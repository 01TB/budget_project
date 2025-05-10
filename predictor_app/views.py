from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib import messages
from .models import RentalProperty, LandForSale, Town
from .forms import (
    RentalPredictionForm, LandPredictionForm,
    RentalPropertyForm, LandForSaleForm, CSVImportForm
)
from .ml_utils import predict_rental_price, predict_land_price
import csv
import io
import pandas as pd  # For easier CSV processing
from django.http import JsonResponse  # For map town data


# --- Helper for map data ---
def get_towns_for_map(request):
    towns = Town.objects.all().values('id', 'name', 'latitude', 'longitude')
    return JsonResponse(list(towns), safe=False)


# --- Main Pages ---
class HomePageView(TemplateView):
    template_name = 'predictor_app/home.html'


class PredictRentalView(FormView):
    template_name = 'predictor_app/predict_rental.html'
    form_class = RentalPredictionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['towns_json_url'] = reverse('get_towns_for_map')
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        input_features = {
            'town_id': data['town'].id if data.get('town') else None,  # Ensure town_id is passed
            'access_type': data['access_type'],
            'property_type': data['property_type'],
            'num_rooms': data['num_rooms'],
            'apartment_type': data.get('apartment_type') if data.get('property_type') == 'apartment' else 'None',
            'house_type': data.get('house_type') if data.get('property_type') == 'house' else 'None',
            'has_house_basement': data.get('has_house_basement', False),
            'has_showers_toilets': data.get('has_showers_toilets', False),
            'has_garage': data.get('has_garage', False),
            'has_garden': data.get('has_garden', False),
            'has_parking': data.get('has_parking', False),
            'has_surveillance_system': data.get('has_surveillance_system', False),
            'has_dishwasher': data.get('has_dishwasher', False),
            'has_washing_machine': data.get('has_washing_machine', False),
            'has_internet_access': data.get('has_internet_access', False),
        }

        # Convert boolean features to int (0 or 1) if model expects that
        for key, value in input_features.items():
            if isinstance(value, bool):
                input_features[key] = int(value)

        predicted_price = predict_rental_price(input_features)

        # Re-populate town_name_display for the form if validation fails or for re-display
        if data.get('town'):
            form.fields['town_name_display'].initial = data['town'].name

        return self.render_to_response(self.get_context_data(form=form, predicted_price=predicted_price))


class PredictLandView(FormView):
    template_name = 'predictor_app/predict_land.html'
    form_class = LandPredictionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['towns_json_url'] = reverse('get_towns_for_map')
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        input_features = {
            'town_id': data['town'].id if data.get('town') else None,
            'paper_type': data['paper_type'],
            'access_type': data['access_type'],
            'is_fenced': int(data.get('is_fenced', False)),  # Convert boolean to int
            'is_ready_to_build': int(data.get('is_ready_to_build', False)),  # Convert boolean to int
            'area_sqm': data['area_sqm']
        }
        predicted_price = predict_land_price(input_features)

        if data.get('town'):
            form.fields['town_name_display'].initial = data['town'].name

        return self.render_to_response(self.get_context_data(form=form, predicted_price=predicted_price))


# --- CRUD Views ---
# Rental Property CRUD
class RentalPropertyListView(ListView):
    model = RentalProperty
    template_name = 'predictor_app/rentalproperty_list.html'
    context_object_name = 'properties'


class RentalPropertyCreateView(CreateView):
    model = RentalProperty
    form_class = RentalPropertyForm
    template_name = 'predictor_app/rentalproperty_form.html'
    success_url = reverse_lazy('rentalproperty_list')

    def form_valid(self, form):
        messages.success(self.request, "Rental property created successfully!")
        return super().form_valid(form)


class RentalPropertyUpdateView(UpdateView):
    model = RentalProperty
    form_class = RentalPropertyForm
    template_name = 'predictor_app/rentalproperty_form.html'
    success_url = reverse_lazy('rentalproperty_list')

    def form_valid(self, form):
        messages.success(self.request, "Rental property updated successfully!")
        return super().form_valid(form)


class RentalPropertyDeleteView(DeleteView):
    model = RentalProperty
    template_name = 'predictor_app/rentalproperty_confirm_delete.html'
    success_url = reverse_lazy('rentalproperty_list')

    def form_valid(self, form):
        messages.success(self.request, "Rental property deleted successfully!")
        return super().form_valid(form)


# Land For Sale CRUD
class LandForSaleListView(ListView):
    model = LandForSale
    template_name = 'predictor_app/landforsale_list.html'
    context_object_name = 'lands'


class LandForSaleCreateView(CreateView):
    model = LandForSale
    form_class = LandForSaleForm
    template_name = 'predictor_app/landforsale_form.html'
    success_url = reverse_lazy('landforsale_list')

    def form_valid(self, form):
        messages.success(self.request, "Land for sale created successfully!")
        return super().form_valid(form)


class LandForSaleUpdateView(UpdateView):
    model = LandForSale
    form_class = LandForSaleForm
    template_name = 'predictor_app/landforsale_form.html'
    success_url = reverse_lazy('landforsale_list')

    def form_valid(self, form):
        messages.success(self.request, "Land for sale updated successfully!")
        return super().form_valid(form)


class LandForSaleDeleteView(DeleteView):
    model = LandForSale
    template_name = 'predictor_app/landforsale_confirm_delete.html'
    success_url = reverse_lazy('landforsale_list')

    def form_valid(self, form):
        messages.success(self.request, "Land for sale deleted successfully!")
        return super().form_valid(form)


# --- CSV Import ---
class ImportCSVView(FormView):
    template_name = 'predictor_app/import_csv.html'
    form_class = CSVImportForm
    success_url = reverse_lazy('home')  # Or a more specific success page

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        model_type = form.cleaned_data['model_type']

        # Ensure file is text
        try:
            decoded_file = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            messages.error(self.request, "Invalid file encoding. Please use UTF-8.")
            return self.form_invalid(form)

        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created_count = 0
        error_count = 0
        errors = []

        try:
            if model_type == 'town':
                for row in reader:
                    try:
                        Town.objects.update_or_create(
                            name=row['name'],
                            defaults={
                                'latitude': float(row['latitude']) if row.get('latitude') else None,
                                'longitude': float(row['longitude']) if row.get('longitude') else None
                            }
                        )
                        created_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row error (Town: {row.get('name', 'N/A')}): {str(e)}")

            elif model_type == 'rental':
                for row in reader:
                    try:
                        town_name = row.get('town_name')
                        if not town_name:
                            errors.append(f"Row error (Rental): Missing town_name")
                            error_count += 1
                            continue
                        town, _ = Town.objects.get_or_create(name=town_name.strip())

                        # Convert boolean strings to actual booleans
                        bool_fields = ['has_house_basement', 'has_showers_toilets', 'has_garage',
                                       'has_garden', 'has_parking', 'has_surveillance_system',
                                       'has_dishwasher', 'has_washing_machine', 'has_internet_access']
                        for field in bool_fields:
                            row[field] = row.get(field, 'False').lower() in ['true', '1', 'yes']

                        # Handle potentially empty apartment/house types
                        apartment_type = row.get('apartment_type') if row.get('apartment_type') else None
                        house_type = row.get('house_type') if row.get('house_type') else None

                        # Ensure price is float/decimal
                        price = float(row['price']) if row.get('price') else 0.0

                        RentalProperty.objects.create(
                            town=town,
                            access_type=row['access_type'],
                            property_type=row['property_type'],
                            num_rooms=int(row['num_rooms']),
                            price=price,
                            apartment_type=apartment_type,
                            house_type=house_type,
                            has_house_basement=row['has_house_basement'],
                            has_showers_toilets=row['has_showers_toilets'],
                            has_garage=row['has_garage'],
                            has_garden=row['has_garden'],
                            has_parking=row['has_parking'],
                            has_surveillance_system=row['has_surveillance_system'],
                            has_dishwasher=row['has_dishwasher'],
                            has_washing_machine=row['has_washing_machine'],
                            has_internet_access=row['has_internet_access'],
                        )
                        created_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row error (Rental): {str(e)} - Data: {row}")

            elif model_type == 'land':
                for row in reader:
                    try:
                        town_name = row.get('town_name')
                        if not town_name:
                            errors.append(f"Row error (Land): Missing town_name")
                            error_count += 1
                            continue
                        town, _ = Town.objects.get_or_create(name=town_name.strip())

                        # Convert boolean strings to actual booleans
                        is_fenced = row.get('is_fenced', 'False').lower() in ['true', '1', 'yes']
                        is_ready_to_build = row.get('is_ready_to_build', 'False').lower() in ['true', '1', 'yes']

                        # Ensure numeric fields are correctly typed
                        area_sqm = float(row['area_sqm']) if row.get('area_sqm') else 0.0
                        price = float(row['price']) if row.get('price') else 0.0

                        LandForSale.objects.create(
                            town=town,
                            paper_type=row['paper_type'],
                            access_type=row['access_type'],
                            is_fenced=is_fenced,
                            is_ready_to_build=is_ready_to_build,
                            area_sqm=area_sqm,
                            price=price
                        )
                        created_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row error (Land): {str(e)} - Data: {row}")

            if error_count > 0:
                messages.warning(self.request,
                                 f"Imported {created_count} records. Encountered {error_count} errors. Details: {'; '.join(errors[:5])}")  # Show first 5 errors
            else:
                messages.success(self.request, f"Successfully imported {created_count} records for {model_type}.")

        except Exception as e:
            messages.error(self.request, f"An error occurred during CSV processing: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)