import pandas as pd
import numpy as np
from datetime import date, timedelta

# --- 1. Configuration & Product Definitions ---

# Define the product variants we want to simulate
PRODUCTS = [
    {'ASIN': 'B0B94152F6', 'Model_Name': 'MacBook Air M2', 'Release_Year': 2022, 'RAM_GB': 8, 'Storage_GB': 256, 'Color': 'Midnight', 'Base_Price': 110000},
    {'ASIN': 'B0B94213G7', 'Model_Name': 'MacBook Air M2', 'Release_Year': 2022, 'RAM_GB': 16, 'Storage_GB': 512, 'Color': 'Starlight', 'Base_Price': 140000},
    {'ASIN': 'B0CJ5KWD22', 'Model_Name': 'MacBook Pro M3', 'Release_Year': 2023, 'RAM_GB': 8, 'Storage_GB': 512, 'Color': 'Space Grey', 'Base_Price': 169900},
    {'ASIN': 'B0CJ5LSM38', 'Model_Name': 'MacBook Pro M3 Pro', 'Release_Year': 2023, 'RAM_GB': 18, 'Storage_GB': 512, 'Color': 'Space Black', 'Base_Price': 199900},
    {'ASIN': 'B08N5XSG8Z', 'Model_Name': 'MacBook Air M1', 'Release_Year': 2020, 'RAM_GB': 8, 'Storage_GB': 256, 'Color': 'Silver', 'Base_Price': 99900},
]

# Simulation parameters
START_DATE = date(2022, 1, 1)
END_DATE = date(2024, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

# Define key event dates
APPLE_EVENTS = [date(2022, 9, 7), date(2023, 9, 12), date(2024, 9, 10)]
MAJOR_SALES = { # Using month and day for annual repetition
    'Diwali_Sale_Start': (10, 20),
    'Prime_Day_Start': (7, 15)
}

# --- 2. Data Generation Loop ---

all_data = []
print("Generating raw data...")

for product in PRODUCTS:
    # Initialize state variables for each product
    current_price = product['Base_Price']
    days_since_last_price_change = 0
    total_reviews = np.random.randint(50, 500)
    avg_rating = np.random.uniform(4.7, 4.9)

    for i in range(TOTAL_DAYS):
        current_date = START_DATE + timedelta(days=i)

        # --- Calculate Time-Based & Event Features ---
        days_until_apple_event = min([abs((event - current_date).days) for event in APPLE_EVENTS if event > current_date], default=999)

        # Check for upcoming annual sales
        days_until_major_sale = 999
        for sale, (month, day) in MAJOR_SALES.items():
            sale_date = date(current_date.year, month, day)
            if sale_date > current_date:
                days_until_major_sale = min(days_until_major_sale, (sale_date - current_date).days)

        # --- Dynamic Pricing Logic ---
        price_drop_prob = 0.005 # Base probability

        # Rule 1: Apple Event Approaching (for older models)
        if days_until_apple_event < 30 and product['Release_Year'] < current_date.year:
            price_drop_prob += 0.15 * ((30 - days_until_apple_event) / 30)

        # Rule 2: Major Sale Approaching
        if days_until_major_sale < 15:
            price_drop_prob += 0.10 * ((15 - days_until_major_sale) / 15)

        # Rule 3: Product is getting old
        age_in_years = (current_date.year - product['Release_Year'])
        if age_in_years > 1:
             price_drop_prob += age_in_years * 0.01

        # Trigger price drop
        if np.random.rand() < price_drop_prob and days_since_last_price_change > 30:
            discount_percentage = np.random.uniform(0.05, 0.15)
            current_price *= (1 - discount_percentage)
            current_price = round(current_price / 10) * 10 - 10 # Make it look like real pricing (e.g., 89,990)
            days_since_last_price_change = 0
        else:
            days_since_last_price_change += 1

        # --- Simulate Other Dynamic Features ---
        stock_status = np.random.choice(['In Stock', 'Low Stock', 'Temporarily Unavailable'], p=[0.90, 0.08, 0.02])
        total_reviews += np.random.randint(0, 5)
        avg_rating -= np.random.uniform(0, 0.0005) # Slow decay
        avg_rating = max(3.5, avg_rating) # Floor the rating

        # Append the daily record
        all_data.append({
            'Date': current_date,
            'ASIN': product['ASIN'],
            **{k: v for k, v in product.items() if k not in ['ASIN', 'Base_Price']},
            'Amazon_Price': current_price,
            'Stock_Status': stock_status,
            'Customer_Rating_Avg': round(avg_rating, 2),
            'Total_Reviews_Count': total_reviews,
            'Days_Since_Last_Price_Change': days_since_last_price_change,
            'Days_Until_Apple_Event': days_until_apple_event,
            'Days_Until_Major_Sale': days_until_major_sale,
        })

df = pd.DataFrame(all_data)

# --- 3. Post-Processing & Feature Engineering ---
print("Engineering final features...")
df['Date'] = pd.to_datetime(df['Date'])
df.sort_values(by=['ASIN', 'Date'], inplace=True)

# Time-based features
df['Day_of_Week'] = df['Date'].dt.dayofweek
df['Is_Weekend'] = (df['Day_of_Week'] >= 5).astype(int)
df['Week_of_Year'] = df['Date'].dt.isocalendar().week.astype(int)
df['Is_Month_End'] = df['Date'].dt.is_month_end.astype(int)

# Price-based features (calculated per product)
df['Amazon_Price_7_Day_Moving_Avg'] = df.groupby('ASIN')['Amazon_Price'].transform(lambda x: x.rolling(7, min_periods=1).mean())
df['Price_Volatility_30_Day'] = df.groupby('ASIN')['Amazon_Price'].transform(lambda x: x.rolling(30, min_periods=1).std())
df['Review_Velocity_7_Day'] = df.groupby('ASIN')['Total_Reviews_Count'].transform(lambda x: x.diff().rolling(7, min_periods=1).sum())

# Fill NaN values created by rolling windows
df.fillna(0, inplace=True)

# --- 4. Generate the Target Variable ---
print("Generating the target variable...")

def will_price_drop(series):
    current_price = series.iloc[0]
    future_prices = series.iloc[1:8] # Look at the next 7 days
    return 1 if (future_prices < current_price).any() else 0

# This is computationally intensive. We apply the function on a rolling window for each product.
# We group by ASIN to ensure the window doesn't cross over different products.
df['Price_Dropped_In_Next_7_Days'] = df.groupby('ASIN')['Amazon_Price'].transform(
    lambda s: s.rolling(window=8, min_periods=1).apply(will_price_drop, raw=False)
).fillna(0).astype(int)

# --- 5. Finalize and Save ---
print("Finalizing and saving the dataset...")
# A dummy 'Our_Price' for context
df['Our_Price'] = df['Amazon_Price'] * np.random.uniform(0.98, 1.05, size=len(df))

# Reorder columns for clarity
final_columns = [
    'Date', 'ASIN', 'Model_Name', 'Release_Year', 'RAM_GB', 'Storage_GB', 'Color',
    'Amazon_Price', 'Our_Price', 'Stock_Status', 'Customer_Rating_Avg', 'Total_Reviews_Count',
    'Day_of_Week', 'Is_Weekend', 'Week_of_Year', 'Is_Month_End',
    'Days_Until_Apple_Event', 'Days_Until_Major_Sale', 'Days_Since_Last_Price_Change',
    'Amazon_Price_7_Day_Moving_Avg', 'Price_Volatility_30_Day', 'Review_Velocity_7_Day',
    'Price_Dropped_In_Next_7_Days'
]
df = df[final_columns]

# Save to CSV
output_filename = 'synthetic_macbook_price_data.csv'
df.to_csv(output_filename, index=False)

print(f"\nSuccessfully generated {len(df)} rows of data.")
print(f"Dataset saved to '{output_filename}'")



# MODEL BUILDING

# ===========================================
# Data Preparation for Price Drop Prediction
# ===========================================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# --------------------------
# Load dataset
# --------------------------
file_path = "/content/synthetic_macbook_price_data.csv"
df = pd.read_csv(file_path)

# --------------------------
# Feature/Target separation
# --------------------------
target_col = "Price_Dropped_In_Next_7_Days"
X = df.drop(columns=[target_col])
y = df[target_col]

# Drop 'Date' column (already encoded through other temporal features)
X = X.drop(columns=["Date"])

# --------------------------
# Identify feature types
# --------------------------
categorical_features = ["ASIN", "Model_Name", "Color", "Stock_Status"]
numeric_features = [col for col in X.columns if col not in categorical_features]

# --------------------------
# Preprocessing pipelines
# --------------------------
numeric_transformer = Pipeline(steps=[
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]
)

# --------------------------
# Train-test split
# --------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --------------------------
# Transform features
# --------------------------
X_train_prepared = preprocessor.fit_transform(X_train)
X_test_prepared = preprocessor.transform(X_test)

# --------------------------
# Print shapes
# --------------------------
print("✅ Data Preparation Complete")
print("X_train shape:", X_train_prepared.shape)
print("X_test shape:", X_test_prepared.shape)
print("y_train shape:", y_train.shape)
print("y_test shape:", y_test.shape)


# --------------------------
# Define models
# --------------------------

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import inspect, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

models = {
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    "LightGBM": LGBMClassifier(random_state=42) if LGBMClassifier else None,
    "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric="logloss", random_state=42) if XGBClassifier else None,
    "Logistic Regression": LogisticRegression(max_iter=2000),
    "KNN": KNeighborsClassifier(),
    "SVM": SVC(kernel="rbf", probability=True, random_state=42)
}

# --------------------------
# Train and evaluate
# --------------------------
results = []

for name, model in models.items():
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model)
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    results.append({
        "Model": name,
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall": recall_score(y_test, y_pred, zero_division=0),
        "F1 Score": f1_score(y_test, y_pred, zero_division=0)
    })

# --------------------------
# Results comparison table
# --------------------------
results_df = pd.DataFrame(results).sort_values(by="F1 Score", ascending=False).reset_index(drop=True)
print("\n✅ Model Comparison Results:\n")
print(results_df.to_string(index=False))
