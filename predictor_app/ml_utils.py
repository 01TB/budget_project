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

RENTAL_MODEL_PATH = os.path.join(settings.MEDIA_ROOT, 'trained_models', 'rental_model.joblib')
RENTAL_PREPROCESSOR_PATH = os.path.join(settings.MEDIA_ROOT, 'trained_models', 'rental_preprocessor.joblib')
LAND_MODEL_PATH = os.path.join(settings.MEDIA_ROOT, 'trained_models', 'land_model.joblib')
LAND_PREPROCESSOR_PATH = os.path.join(settings.MEDIA_ROOT, 'trained_models', 'land_preprocessor.joblib')

# Ensure directories exist
os.makedirs(os.path.dirname(RENTAL_MODEL_PATH), exist_ok=True)
os.makedirs(os.path.dirname(LAND_MODEL_PATH), exist_ok=True)


def train_rental_model(data):
    """
    Trains a linear regression model for rental properties.
    data: A list of dictionaries, where each dictionary is a rental property instance.
    """
    if not data:
        print("No data to train rental model.")
        return None, None

    df = pd.DataFrame(data)

    # Define features
    categorical_features = ['town_id', 'access_type', 'property_type', 'apartment_type', 'house_type']
    numerical_features = ['num_rooms']
    boolean_features = [
        'has_house_basement', 'has_showers_toilets', 'has_garage', 'has_garden',
        'has_parking', 'has_surveillance_system', 'has_dishwasher',
        'has_washing_machine', 'has_internet_access'
    ]

    # Ensure all expected columns exist, fill NaNs appropriately
    for col in categorical_features:
        df[col] = df[col].fillna('None')  # Handle missing apartment/house types
    for col in numerical_features + boolean_features:
        df[col] = df[col].fillna(0)  # Fill missing numerical/boolean with 0

    X = df[categorical_features + numerical_features + boolean_features]
    y = df['price']

    # Preprocessing: One-hot encode categoricals, passthrough others
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('num', 'passthrough', numerical_features + boolean_features)
        ])

    # Create a pipeline
    model_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                     ('regressor', LinearRegression())])

    # Split data (optional for final deployment model, but good for evaluation)
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Fit the model on all available data for deployment
    model_pipeline.fit(X, y)

    # Save the model and preprocessor
    joblib.dump(model_pipeline, RENTAL_MODEL_PATH)
    print(f"Rental model trained and saved to {RENTAL_MODEL_PATH}")

    # For evaluation (if using train/test split)
    # y_pred = model_pipeline.predict(X_test)
    # print(f"Rental Model MSE: {mean_squared_error(y_test, y_pred)}")
    # print(f"Rental Model R^2: {r2_score(y_test, y_pred)}")

    return model_pipeline


def train_land_model(data):
    """
    Trains a linear regression model for land for sale.
    data: A list of dictionaries, where each dictionary is a land instance.
    """
    if not data:
        print("No data to train land model.")
        return None, None

    df = pd.DataFrame(data)

    categorical_features = ['town_id', 'paper_type', 'access_type']
    numerical_features = ['area_sqm']  # area_sqm is crucial
    boolean_features = ['is_fenced', 'is_ready_to_build']

    for col in categorical_features:
        df[col] = df[col].fillna('None')
    for col in numerical_features + boolean_features:
        df[col] = df[col].fillna(0)

    df['area_sqm'] = pd.to_numeric(df['area_sqm'], errors='coerce').fillna(0)

    X = df[categorical_features + numerical_features + boolean_features]
    y = df['price']

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('num', 'passthrough', numerical_features + boolean_features)
        ])

    model_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                     ('regressor', LinearRegression())])
    model_pipeline.fit(X, y)

    joblib.dump(model_pipeline, LAND_MODEL_PATH)
    print(f"Land model trained and saved to {LAND_MODEL_PATH}")
    return model_pipeline


def predict_rental_price(input_data):
    """
    Predicts rental price based on input_data.
    input_data: A dictionary or pd.Series with feature values.
    """
    try:
        model_pipeline = joblib.load(RENTAL_MODEL_PATH)
    except FileNotFoundError:
        return "Model not trained yet."

    # Convert input_data to DataFrame to match training structure
    # Ensure all columns are present and in the correct order
    # This requires knowing the full feature set after one-hot encoding,
    # or, more robustly, fitting the preprocessor on all possible categories
    # during training and saving it. For now, we rely on the pipeline.

    df_input = pd.DataFrame([input_data])

    # Ensure columns match the ones used in training the preprocessor
    # This is a simplified approach. A robust solution would involve
    # saving the preprocessor's feature names or re-fitting it carefully.
    categorical_features = ['town_id', 'access_type', 'property_type', 'apartment_type', 'house_type']
    numerical_features = ['num_rooms']
    boolean_features = [
        'has_house_basement', 'has_showers_toilets', 'has_garage', 'has_garden',
        'has_parking', 'has_surveillance_system', 'has_dishwasher',
        'has_washing_machine', 'has_internet_access'
    ]

    # Fill missing expected features with defaults if not in input_data
    for col in categorical_features:
        if col not in df_input.columns:
            df_input[col] = 'None'  # Or a suitable default
    for col in numerical_features + boolean_features:
        if col not in df_input.columns:
            df_input[col] = 0  # Or a suitable default

    # Ensure order for the preprocessor
    df_input = df_input[categorical_features + numerical_features + boolean_features]

    prediction = model_pipeline.predict(df_input)
    return prediction[0]


def predict_land_price(input_data):
    """
    Predicts land price based on input_data.
    input_data: A dictionary or pd.Series with feature values.
    """
    try:
        model_pipeline = joblib.load(LAND_MODEL_PATH)
    except FileNotFoundError:
        return "Model not trained yet."

    df_input = pd.DataFrame([input_data])

    categorical_features = ['town_id', 'paper_type', 'access_type']
    numerical_features = ['area_sqm']
    boolean_features = ['is_fenced', 'is_ready_to_build']

    for col in categorical_features:
        if col not in df_input.columns:
            df_input[col] = 'None'
    for col in numerical_features + boolean_features:
        if col not in df_input.columns:
            df_input[col] = 0

    df_input['area_sqm'] = pd.to_numeric(df_input['area_sqm'], errors='coerce').fillna(0)

    df_input = df_input[categorical_features + numerical_features + boolean_features]

    prediction = model_pipeline.predict(df_input)
    return prediction[0]