import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import numpy as np
from django.conf import settings
import os

from .models import Convenience  # Needed for feature engineering

# Define paths for saved models
BASE_MODEL_DIR = os.path.join(settings.MEDIA_ROOT, 'trained_models')
RENTAL_MODEL_PATH = os.path.join(BASE_MODEL_DIR, 'rental_model.joblib')
LAND_MODEL_PATH = os.path.join(BASE_MODEL_DIR, 'land_price_per_sqm_model.joblib')

# Ensure directories exist
os.makedirs(BASE_MODEL_DIR, exist_ok=True)


def train_rental_model(rental_data_list_of_dicts):
    if not rental_data_list_of_dicts:
        print("No data provided to train rental model.")
        return None

    df = pd.DataFrame(rental_data_list_of_dicts)

    # Define feature columns
    categorical_features = ['town_id', 'access_type_id', 'property_type', 'apartment_type', 'house_type']
    numerical_direct_features = ['num_rooms']  # Features that are already numeric
    boolean_direct_features = ['has_house_basement']  # Booleans that become 0/1

    # One-hot encode convenience_ids:
    # Get all possible convenience IDs from the database to ensure consistent columns
    all_db_convenience_ids = sorted(list(Convenience.objects.values_list('id', flat=True)))
    convenience_feature_cols = [f'convenience_{cid}' for cid in all_db_convenience_ids]

    # Create convenience columns in the DataFrame
    for cid in all_db_convenience_ids:
        df[f'convenience_{cid}'] = df['convenience_ids'].apply(lambda x: 1 if isinstance(x, list) and cid in x else 0)

    # Combine all features
    # Note: convenience_feature_cols are already 0/1, so they can be treated as numerical or passthrough.
    # We'll pass them through as numerical.
    all_numerical_features = numerical_direct_features + boolean_direct_features + convenience_feature_cols

    # Fill NaN values
    for col in categorical_features:
        df[col] = df[col].fillna('None_CAT')  # Use a distinct string for missing categorical FKs
    for col in all_numerical_features:
        df[col] = df[col].fillna(0).astype(int)  # Ensure 0/1 for booleans and conveniences

    X = df[categorical_features + all_numerical_features]
    y = df['price'].astype(float)

    if X.empty or y.empty:
        print("Not enough data after processing for rental model training.")
        return None

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False, drop=None), categorical_features),
            # drop=None to see all columns
            ('num', 'passthrough', all_numerical_features)
        ],
        remainder='drop'  # Explicitly drop any other columns
    )

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

    try:
        model_pipeline.fit(X, y)
        joblib.dump(model_pipeline, RENTAL_MODEL_PATH)
        print(f"Rental model trained and saved to {RENTAL_MODEL_PATH}")
        # print("Features after preprocessing:", model_pipeline.named_steps['preprocessor'].get_feature_names_out()) # For debugging
    except Exception as e:
        print(f"Error during rental model training or saving: {e}")
        return None
    return model_pipeline


def predict_rental_price(input_data_dict):
    try:
        model_pipeline = joblib.load(RENTAL_MODEL_PATH)
    except FileNotFoundError:
        return "Rental model not trained yet. Please run the training script."
    except Exception as e:
        return f"Error loading rental model: {e}"

    # Prepare input DataFrame matching the training structure
    all_db_convenience_ids = sorted(list(Convenience.objects.values_list('id', flat=True)))

    # Start with a copy of the input to avoid modifying the original dict
    df_row = {}
    df_row['town_id'] = input_data_dict.get('town_id')
    df_row['access_type_id'] = input_data_dict.get('access_type_id')
    df_row['property_type'] = input_data_dict.get('property_type')
    df_row['apartment_type'] = input_data_dict.get('apartment_type', 'None_CAT')  # Default if not present
    df_row['house_type'] = input_data_dict.get('house_type', 'None_CAT')  # Default if not present
    df_row['num_rooms'] = input_data_dict.get('num_rooms', 0)
    df_row['has_house_basement'] = int(input_data_dict.get('has_house_basement', False))

    # One-hot encode conveniences
    selected_convenience_ids = input_data_dict.get('convenience_ids', [])
    for cid in all_db_convenience_ids:
        df_row[f'convenience_{cid}'] = 1 if cid in selected_convenience_ids else 0

    df_input = pd.DataFrame([df_row])

    # Ensure all categorical features are present and handle None/NaN for them before prediction
    categorical_features_expected = ['town_id', 'access_type_id', 'property_type', 'apartment_type', 'house_type']
    for col in categorical_features_expected:
        if col not in df_input.columns or pd.isna(df_input[col].iloc[0]):
            df_input[col] = 'None_CAT'  # Must match fillna during training

    # Ensure all numerical features are present and handle None/NaN for them
    numerical_direct_features = ['num_rooms']
    boolean_direct_features = ['has_house_basement']
    convenience_feature_cols = [f'convenience_{cid}' for cid in all_db_convenience_ids]
    all_numerical_features_expected = numerical_direct_features + boolean_direct_features + convenience_feature_cols

    for col in all_numerical_features_expected:
        if col not in df_input.columns or pd.isna(df_input[col].iloc[0]):
            df_input[col] = 0  # Default for missing numerical/boolean/convenience features
        else:  # Ensure it's int if it's a boolean/convenience feature
            if col in boolean_direct_features or col in convenience_feature_cols:
                df_input[col] = int(df_input[col].iloc[0])

    # Ensure feature order matches training
    ordered_feature_list = categorical_features_expected + all_numerical_features_expected
    try:
        df_input = df_input[ordered_feature_list]
    except KeyError as e:
        return f"Prediction error: Missing expected feature column: {e}. Check model training and prediction input consistency."

    try:
        prediction = model_pipeline.predict(df_input)
        return prediction[0]
    except Exception as e:
        # Try to get more info from the preprocessor if it fails there
        # try:
        #     transformed_features = model_pipeline.named_steps['preprocessor'].transform(df_input)
        #     print("Transformed features for prediction:", transformed_features)
        # except Exception as pe:
        #     print("Error during preprocessor transform in prediction:", pe)
        return f"Error during prediction: {e}"


def train_land_model(land_data_list_of_dicts):  # For Option C: Price Per SqM
    if not land_data_list_of_dicts:
        print("No data provided to train land model.")
        return None

    df = pd.DataFrame(land_data_list_of_dicts)

    categorical_features = ['town_id', 'paper_type_id', 'access_type_id']
    boolean_features = ['is_fenced', 'is_ready_to_build']  # Will be 0/1

    for col in categorical_features:
        df[col] = df[col].fillna('None_CAT')
    for col in boolean_features:
        df[col] = df[col].fillna(0).astype(int)  # Ensure 0 or 1

    X = df[categorical_features + boolean_features]
    y = df['price_per_sqm'].astype(float)  # Target variable

    if X.empty or y.empty:
        print("Not enough data after processing for land model training.")
        return None

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('bool', 'passthrough', boolean_features)
        ],
        remainder='drop'
    )

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])
    try:
        model_pipeline.fit(X, y)
        joblib.dump(model_pipeline, LAND_MODEL_PATH)
        print(f"Land (price per sqm) model trained and saved to {LAND_MODEL_PATH}")
    except Exception as e:
        print(f"Error during land model training or saving: {e}")
        return None
    return model_pipeline


def predict_land_price_per_sqm(input_data_dict):  # For Option C
    try:
        model_pipeline = joblib.load(LAND_MODEL_PATH)
    except FileNotFoundError:
        return "Land model not trained yet. Please run the training script."
    except Exception as e:
        return f"Error loading land model: {e}"

    df_row = {
        'town_id': input_data_dict.get('town_id'),
        'paper_type_id': input_data_dict.get('paper_type_id'),
        'access_type_id': input_data_dict.get('access_type_id'),
        'is_fenced': int(input_data_dict.get('is_fenced', False)),
        'is_ready_to_build': int(input_data_dict.get('is_ready_to_build', False)),
    }
    df_input = pd.DataFrame([df_row])

    categorical_features_expected = ['town_id', 'paper_type_id', 'access_type_id']
    boolean_features_expected = ['is_fenced', 'is_ready_to_build']

    for col in categorical_features_expected:
        if col not in df_input.columns or pd.isna(df_input[col].iloc[0]):
            df_input[col] = 'None_CAT'
    for col in boolean_features_expected:
        if col not in df_input.columns or pd.isna(df_input[col].iloc[0]):
            df_input[col] = 0
        else:
            df_input[col] = int(df_input[col].iloc[0])

    ordered_feature_list = categorical_features_expected + boolean_features_expected
    try:
        df_input = df_input[ordered_feature_list]
    except KeyError as e:
        return f"Prediction error: Missing expected feature column for land model: {e}."

    try:
        prediction = model_pipeline.predict(df_input)
        return prediction[0]
    except Exception as e:
        return f"Error during land prediction: {e}"