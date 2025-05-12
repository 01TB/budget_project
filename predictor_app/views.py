import csv
import io
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg  # For Land Prediction Option A (if you revert)

from .models import (
    RentalProperty, LandForSale, Town,
    AccessType, PaperType, Convenience
)
from .forms import (
    RentalPredictionForm, LandPredictionForm,
    RentalPropertyForm, LandForSaleForm, CSVImportForm,
    AccessTypeForm, PaperTypeForm, ConvenienceForm
)
# Ensure correct prediction function name is imported for land
from .ml_utils import predict_rental_price, predict_land_price_per_sqm


# --- Helper for map data ---
def get_towns_for_map(request):
    towns = Town.objects.all().values('id', 'name', 'latitude', 'longitude')
    return JsonResponse(list(towns), safe=False)


# --- Main Pages ---
class HomePageView(TemplateView):
    template_name = 'predictor_app/home.html'


# --- Prediction Views ---
class PredictRentalView(FormView):
    template_name = 'predictor_app/predict_rental.html'
    form_class = RentalPredictionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['towns_json_url'] = reverse('get_towns_for_map')
        return context

    def form_valid(self, form):
        data = form.cleaned_data

        convenience_ids_list = []
        if 'conveniences' in data and data['conveniences']:
            convenience_ids_list = [c.id for c in data['conveniences']]

        input_features = {
            'town_id': data['town'].id if data.get('town') else None,
            'access_type_id': data['access_type'].id if data.get('access_type') else None,
            'property_type': data['property_type'],
            'num_rooms': data['num_rooms'],
            'apartment_type': data.get('apartment_type') if data.get('property_type') == 'apartment' else 'None',
            # Pass 'None' as string
            'house_type': data.get('house_type') if data.get('property_type') == 'house' else 'None',
            # Pass 'None' as string
            'has_house_basement': data.get('has_house_basement', False),
            'convenience_ids': convenience_ids_list,
        }

        predicted_price = predict_rental_price(input_features)

        if data.get('town'):
            form.fields['town_name_display'].initial = data['town'].name

        return self.render_to_response(self.get_context_data(form=form, predicted_price=predicted_price))


class PredictLandView(FormView):  # Option C: Price Per SqM
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
            'paper_type_id': data['paper_type'].id if data.get('paper_type') else None,
            'access_type_id': data['access_type'].id if data.get('access_type') else None,
            'is_fenced': data.get('is_fenced', False),
            'is_ready_to_build': data.get('is_ready_to_build', False),
        }
        print(f"DEBUG: Land input_features: {input_features}")  # <-- ADD THIS
        predicted_price_sqm_result = predict_land_price_per_sqm(input_features)
        print(f"DEBUG: Predicted Price SqM Result: {predicted_price_sqm_result}")  # <-- ADD

        if data.get('town'):
            form.fields['town_name_display'].initial = data['town'].name

        context_data = self.get_context_data(form=form, predicted_price_sqm=predicted_price_sqm_result)

        # Add example plot sizes for price range display
        if isinstance(predicted_price_sqm_result, (int, float)):  # Check if prediction is a number
            example_sizes = {
                "Small Plot (e.g., 100 sqm)": predicted_price_sqm_result * 100,
                "Medium Plot (e.g., 300 sqm)": predicted_price_sqm_result * 300,
                "Large Plot (e.g., 500 sqm)": predicted_price_sqm_result * 500,
            }
            context_data['example_total_prices'] = example_sizes

        return self.render_to_response(context_data)


# --- CRUD Views for Main Models ---
class RentalPropertyListView(ListView):
    model = RentalProperty
    template_name = 'predictor_app/rentalproperty_list.html'
    context_object_name = 'properties'


class RentalPropertyCreateView(CreateView):
    model = RentalProperty
    form_class = RentalPropertyForm
    template_name = 'predictor_app/rentalproperty_form.html'  # Generic form can be used
    success_url = reverse_lazy('rentalproperty_list')
    extra_context = {'form_title': 'Add New Rental Property'}

    def form_valid(self, form):
        messages.success(self.request, "Rental property created successfully!")
        return super().form_valid(form)


class RentalPropertyUpdateView(UpdateView):
    model = RentalProperty
    form_class = RentalPropertyForm
    template_name = 'predictor_app/rentalproperty_form.html'
    success_url = reverse_lazy('rentalproperty_list')
    extra_context = {'form_title': 'Edit Rental Property'}

    def form_valid(self, form):
        messages.success(self.request, "Rental property updated successfully!")
        return super().form_valid(form)


class RentalPropertyDeleteView(DeleteView):
    model = RentalProperty
    template_name = 'predictor_app/confirm_delete.html'  # Generic delete can be used
    success_url = reverse_lazy('rentalproperty_list')
    extra_context = {'item_type': 'Rental Property', 'list_url_name': 'rentalproperty_list'}  # For cancel link

    def form_valid(self, form):
        messages.success(self.request, "Rental property deleted successfully!")
        return super().form_valid(form)


class LandForSaleListView(ListView):
    model = LandForSale
    template_name = 'predictor_app/landforsale_list.html'
    context_object_name = 'lands'


class LandForSaleCreateView(CreateView):
    model = LandForSale
    form_class = LandForSaleForm
    template_name = 'predictor_app/landforsale_form.html'  # Generic form can be used
    success_url = reverse_lazy('landforsale_list')
    extra_context = {'form_title': 'Add New Land For Sale'}

    def form_valid(self, form):
        messages.success(self.request, "Land for sale created successfully!")
        return super().form_valid(form)


class LandForSaleUpdateView(UpdateView):
    model = LandForSale
    form_class = LandForSaleForm
    template_name = 'predictor_app/landforsale_form.html'
    success_url = reverse_lazy('landforsale_list')
    extra_context = {'form_title': 'Edit Land For Sale'}

    def form_valid(self, form):
        messages.success(self.request, "Land for sale updated successfully!")
        return super().form_valid(form)


class LandForSaleDeleteView(DeleteView):
    model = LandForSale
    template_name = 'predictor_app/confirm_delete.html'
    success_url = reverse_lazy('landforsale_list')
    extra_context = {'item_type': 'Land For Sale', 'list_url_name': 'landforsale_list'}  # For cancel link

    def form_valid(self, form):
        messages.success(self.request, "Land for sale deleted successfully!")
        return super().form_valid(form)


# --- CRUD Views for Lookup Tables ---
class AccessTypeListView(ListView):
    model = AccessType
    template_name = 'predictor_app/lookuptable_list.html'
    context_object_name = 'items'
    extra_context = {'table_name': 'Access Types', 'add_url_name': 'accesstype_new', 'edit_url_base': 'accesstype_edit',
                     'delete_url_base': 'accesstype_delete'}


class AccessTypeCreateView(CreateView):
    model = AccessType
    form_class = AccessTypeForm
    template_name = 'predictor_app/lookuptable_form.html'
    success_url = reverse_lazy('accesstype_list')
    extra_context = {'form_title': 'Add New Access Type', 'list_url_name': 'accesstype_list'}


class AccessTypeUpdateView(UpdateView):
    model = AccessType
    form_class = AccessTypeForm
    template_name = 'predictor_app/lookuptable_form.html'
    success_url = reverse_lazy('accesstype_list')
    extra_context = {'form_title': 'Edit Access Type', 'list_url_name': 'accesstype_list'}


class AccessTypeDeleteView(DeleteView):
    model = AccessType
    template_name = 'predictor_app/lookuptable_confirm_delete.html'
    success_url = reverse_lazy('accesstype_list')
    extra_context = {'item_type': 'Access Type', 'list_url_name': 'accesstype_list'}


class PaperTypeListView(ListView):
    model = PaperType
    template_name = 'predictor_app/lookuptable_list.html'
    context_object_name = 'items'
    extra_context = {'table_name': 'Paper Types', 'add_url_name': 'papertype_new', 'edit_url_base': 'papertype_edit',
                     'delete_url_base': 'papertype_delete'}


class PaperTypeCreateView(CreateView):
    model = PaperType
    form_class = PaperTypeForm
    template_name = 'predictor_app/lookuptable_form.html'
    success_url = reverse_lazy('papertype_list')
    extra_context = {'form_title': 'Add New Paper Type', 'list_url_name': 'papertype_list'}


class PaperTypeUpdateView(UpdateView):
    model = PaperType
    form_class = PaperTypeForm
    template_name = 'predictor_app/lookuptable_form.html'
    success_url = reverse_lazy('papertype_list')
    extra_context = {'form_title': 'Edit Paper Type', 'list_url_name': 'papertype_list'}


class PaperTypeDeleteView(DeleteView):
    model = PaperType
    template_name = 'predictor_app/lookuptable_confirm_delete.html'
    success_url = reverse_lazy('papertype_list')
    extra_context = {'item_type': 'Paper Type', 'list_url_name': 'papertype_list'}


class ConvenienceListView(ListView):
    model = Convenience
    template_name = 'predictor_app/lookuptable_list.html'
    context_object_name = 'items'
    extra_context = {'table_name': 'Convenience Types', 'add_url_name': 'convenience_new',
                     'edit_url_base': 'convenience_edit', 'delete_url_base': 'convenience_delete'}


class ConvenienceCreateView(CreateView):
    model = Convenience
    form_class = ConvenienceForm
    template_name = 'predictor_app/lookuptable_form.html'
    success_url = reverse_lazy('convenience_list')
    extra_context = {'form_title': 'Add New Convenience Type', 'list_url_name': 'convenience_list'}


class ConvenienceUpdateView(UpdateView):
    model = Convenience
    form_class = ConvenienceForm
    template_name = 'predictor_app/lookuptable_form.html'
    success_url = reverse_lazy('convenience_list')
    extra_context = {'form_title': 'Edit Convenience Type', 'list_url_name': 'convenience_list'}


class ConvenienceDeleteView(DeleteView):
    model = Convenience
    template_name = 'predictor_app/lookuptable_confirm_delete.html'
    success_url = reverse_lazy('convenience_list')
    extra_context = {'item_type': 'Convenience Type', 'list_url_name': 'convenience_list'}


# --- CSV Import View ---
class ImportCSVView(FormView):
    template_name = 'predictor_app/import_csv.html'
    form_class = CSVImportForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        model_type = form.cleaned_data['model_type']

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')  # Use utf-8-sig to handle potential BOM
        except UnicodeDecodeError:
            messages.error(self.request, "Invalid file encoding. Please use UTF-8.")
            return self.form_invalid(form)

        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []

        try:
            if model_type == 'town':
                for row in reader:
                    try:
                        name = row.get('name', '').strip()
                        if not name: continue  # Skip empty rows
                        _, created = Town.objects.update_or_create(
                            name=name,
                            defaults={
                                'latitude': float(row['latitude']) if row.get('latitude') else None,
                                'longitude': float(row['longitude']) if row.get('longitude') else None
                            }
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Town '{row.get('name', 'N/A')}': {str(e)}")

            elif model_type == 'access_type':
                for row in reader:
                    try:
                        name = row.get('name', '').strip()
                        if not name: continue
                        obj, created = AccessType.objects.get_or_create(name=name)
                        # Update description if provided in CSV, or let model's save() handle default
                        if row.get('description',
                                   obj.description) != obj.description:  # Check if description needs update or is new
                            obj.description = row.get('description', '')  # If CSV has blank, use blank
                            obj.save()  # Triggers model's save logic if description was blank
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1 if row.get('description', obj.description) != obj.description else 0
                    except Exception as e:
                        error_count += 1
                        errors.append(f"AccessType '{row.get('name', 'N/A')}': {str(e)}")

            elif model_type == 'paper_type':
                for row in reader:
                    try:
                        name = row.get('name', '').strip()
                        if not name: continue
                        obj, created = PaperType.objects.get_or_create(name=name)
                        if row.get('description', obj.description) != obj.description:
                            obj.description = row.get('description', '')
                            obj.save()
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1 if row.get('description', obj.description) != obj.description else 0
                    except Exception as e:
                        error_count += 1
                        errors.append(f"PaperType '{row.get('name', 'N/A')}': {str(e)}")

            elif model_type == 'convenience':
                for row in reader:
                    try:
                        name = row.get('name', '').strip()
                        if not name: continue
                        obj, created = Convenience.objects.get_or_create(name=name)
                        if row.get('description', obj.description) != obj.description:
                            obj.description = row.get('description', '')
                            obj.save()
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1 if row.get('description', obj.description) != obj.description else 0
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Convenience '{row.get('name', 'N/A')}': {str(e)}")

            elif model_type == 'rental':
                for row_idx, row in enumerate(reader):
                    try:
                        town_name = row.get('town_name', '').strip()
                        if not town_name:
                            errors.append(f"Rental Row {row_idx + 2}: Missing town_name")
                            error_count += 1
                            continue
                        town, _ = Town.objects.get_or_create(name=town_name)

                        access_type_name = row.get('access_type_name', '').strip()
                        if not access_type_name:
                            errors.append(f"Rental Row {row_idx + 2} (Town: {town_name}): Missing access_type_name")
                            error_count += 1
                            continue
                        access_type_obj, _ = AccessType.objects.get_or_create(name=access_type_name)

                        convenience_names_str = row.get('conveniences_names', '')
                        convenience_objs_to_add = []
                        if convenience_names_str:
                            for conv_name_raw in convenience_names_str.split(','):
                                conv_name = conv_name_raw.strip()
                                if conv_name:
                                    conv_obj, _ = Convenience.objects.get_or_create(name=conv_name)
                                    convenience_objs_to_add.append(conv_obj)

                        price_str = str(row.get('price', '0')).replace(',', '')
                        price = float(price_str) if price_str else 0.0

                        has_basement = row.get('has_house_basement', 'False').lower() in ['true', '1', 'yes', 'oui']

                        rental_prop = RentalProperty.objects.create(
                            town=town,
                            access_type=access_type_obj,
                            property_type=row.get('property_type', '').strip(),
                            num_rooms=int(row.get('num_rooms', 1)),
                            price=price,
                            apartment_type=row.get('apartment_type') if row.get(
                                'property_type') == 'apartment' else None,
                            house_type=row.get('house_type') if row.get('property_type') == 'house' else None,
                            has_house_basement=has_basement,
                        )
                        if convenience_objs_to_add:
                            rental_prop.conveniences.add(*convenience_objs_to_add)
                        created_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Rental Row {row_idx + 2} (Town: {row.get('town_name', 'N/A')}): {str(e)}")


            elif model_type == 'land':
                for row_idx, row in enumerate(reader):
                    try:
                        town_name = row.get('town_name', '').strip()
                        if not town_name:
                            errors.append(f"Land Row {row_idx + 2}: Missing town_name")
                            error_count += 1
                            continue
                        town, _ = Town.objects.get_or_create(name=town_name)

                        access_type_name = row.get('access_type_name', '').strip()
                        paper_type_name = row.get('paper_type_name', '').strip()

                        if not access_type_name:
                            errors.append(f"Land Row {row_idx + 2} (Town: {town_name}): Missing access_type_name")
                            error_count += 1;
                            continue
                        if not paper_type_name:
                            errors.append(f"Land Row {row_idx + 2} (Town: {town_name}): Missing paper_type_name")
                            error_count += 1;
                            continue

                        access_type_obj, _ = AccessType.objects.get_or_create(name=access_type_name)
                        paper_type_obj, _ = PaperType.objects.get_or_create(name=paper_type_name)

                        area_sqm_str = str(row.get('area_sqm', '0')).replace(',', '')
                        price_str = str(row.get('price', '0')).replace(',', '')

                        area_sqm = float(area_sqm_str) if area_sqm_str else 0.0
                        price = float(price_str) if price_str else 0.0

                        LandForSale.objects.create(
                            town=town, paper_type=paper_type_obj, access_type=access_type_obj,
                            is_fenced=row.get('is_fenced', 'False').lower() in ['true', '1', 'yes', 'oui'],
                            is_ready_to_build=row.get('is_ready_to_build', 'False').lower() in ['true', '1', 'yes',
                                                                                                'oui'],
                            area_sqm=area_sqm, price=price
                        )
                        created_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Land Row {row_idx + 2} (Town: {row.get('town_name', 'N/A')}): {str(e)}")

            msg = ""
            if created_count > 0: msg += f"{created_count} records created. "
            if updated_count > 0: msg += f"{updated_count} records updated. "  # For lookup tables
            if not msg and error_count == 0: msg = "No new data to import."

            if error_count > 0:
                detailed_errors = '; '.join(errors[:5])
                final_msg = f"Processed for {model_type}. {msg}Encountered {error_count} errors. First few: {detailed_errors}"
                messages.warning(self.request, final_msg)
                print(f"Full list of CSV import errors for {model_type}: {errors}")
            else:
                final_msg = f"Successfully processed for {model_type}. {msg}"
                messages.success(self.request, final_msg.strip())

        except csv.Error as e:  # Catch errors related to CSV parsing itself
            messages.error(self.request, f"CSV formatting error for {model_type}: {str(e)}")
            return self.form_invalid(form)
        except Exception as e:  # Catch other unexpected errors
            messages.error(self.request,
                           f"An unexpected error occurred during CSV processing for {model_type}: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)