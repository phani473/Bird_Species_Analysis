# data_preprocessing.py
import pandas as pd
import psycopg2
from psycopg2 import sql

# Step 1: Load and Clean Data
def load_and_clean_data():
    # Read both Excel files 
    forest_sheets = pd.read_excel('Bird_Monitoring_Data_FOREST.xlsx', sheet_name=None)
    grassland_sheets = pd.read_excel('Bird_Monitoring_Data_GRASSLAND.xlsx', sheet_name=None)

    # Filter out empty sheets
    forest_dfs = [df for df in forest_sheets.values() if not df.empty]
    grassland_dfs = [df for df in grassland_sheets.values() if not df.empty]

    # Check if any data is available before concatenation
    forest_df = pd.concat(forest_dfs, ignore_index=True) if forest_dfs else pd.DataFrame()
    grassland_df = pd.concat(grassland_dfs, ignore_index=True) if grassland_dfs else pd.DataFrame()

    # Merge both datasets
    combined_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    # If no data is available, return an empty DataFrame
    if combined_df.empty:
        raise ValueError("No valid data found in the Excel sheets.")

    # Drop rows where 'Scientific_Name' is missing
    combined_df = combined_df.dropna(subset=['Scientific_Name'])


    # Fix: Avoid inplace=True with chained assignment
    combined_df['Temperature'] = combined_df['Temperature'].fillna(combined_df['Temperature'].mean())  # Fill missing temperature with mean
    combined_df['Humidity'] = combined_df['Humidity'].fillna(combined_df['Humidity'].mean())  # Fill missing humidity with mean

    # Standardize data
    combined_df['Date'] = pd.to_datetime(combined_df['Date'])  # Convert to datetime
    combined_df['Year'] = combined_df['Date'].dt.year  # Extract year
    combined_df['Month'] = combined_df['Date'].dt.month  # Extract month

    # Convert 'Interval_Length' to numeric, errors='coerce' turns invalid parsing into NaN
    combined_df['Interval_Length'] = pd.to_numeric(combined_df['Interval_Length'], errors='coerce')

    def categorize_interval(length):
        if pd.isnull(length):
            return 'Unknown'
        elif 0 <= length <= 2.5:
            return '0-2.5 min'
        elif 2.5 < length <= 5:
            return '2.5-5 min'
        elif 5 < length <= 7.5:
            return '5-7.5 min'
        elif 7.5 < length <= 10:
            return '7.5-10 min'
        else:
            return '10+ min'
        
    # Apply categorization to 'Interval_Length'
    combined_df['Interval_Length'] = combined_df['Interval_Length'].apply(categorize_interval)

    # Handle 'Sky' and 'Wind' columns: Clean, categorize or map values if needed
    combined_df['Sky'] = combined_df['Sky'].fillna('Unknown')  # Handle missing sky data
    combined_df['Wind'] = combined_df['Wind'].fillna('Unknown')  # Handle missing wind data

    # Filter relevant columns
    columns_to_keep = [
        'Admin_Unit_Code', 'Location_Type', 'Interval_Length', 'ID_Method', 'Year', 'Month', 'Date', 
        'Scientific_Name', 'Common_Name', 'Temperature', 'Humidity', 'Distance', 'Flyover_Observed', 
        'Sex', 'PIF_Watchlist_Status', 'Regional_Stewardship_Status', 'Disturbance', 'Plot_Name', 
        'Sky', 'Wind', 'Observer', 'Visit'  # Added Observer and Visit
    ]
    combined_df = combined_df[columns_to_keep]

    return combined_df

# Step 2: Connect to PostgreSQL Database
def connect_to_postgres():
    # Replace with your PostgreSQL credentials
    conn = psycopg2.connect(
        dbname="bird_db",
        user="postgres",
        password="Phani@1pk",
        host="localhost",
        port="5432"
    )
    return conn

# Step 3: Store Data in PostgreSQL
def store_data_in_postgres(df):
    conn = connect_to_postgres()
    cursor = conn.cursor()

    # Drop the existing table if it exists
    drop_table_query = "DROP TABLE IF EXISTS bird_observations;"
    cursor.execute(drop_table_query)
    conn.commit()

    # Create the table with the new columns 'Observer' and 'Visit'
    create_table_query = """
    CREATE TABLE bird_observations (
        Admin_Unit_Code VARCHAR(50),
        Location_Type VARCHAR(50),
        Interval_Length VARCHAR(50),
        ID_Method VARCHAR(50),
        Year INT,
        Month INT,
        Date DATE,
        Scientific_Name VARCHAR(100),
        Common_Name VARCHAR(100),
        Temperature FLOAT,
        Humidity FLOAT,
        Distance VARCHAR(50),
        Flyover_Observed BOOLEAN,
        Sex VARCHAR(50),
        PIF_Watchlist_Status BOOLEAN,
        Regional_Stewardship_Status BOOLEAN,
        Disturbance VARCHAR(100),
        Plot_Name VARCHAR(100),
        Sky VARCHAR(50),
        Wind VARCHAR(50),
        Observer VARCHAR(100),  -- Added Observer
        Visit INT  -- Added Visit
    );
    """
    cursor.execute(create_table_query)
    conn.commit()

    # Insert data into the table
    for _, row in df.iterrows():
        insert_query = sql.SQL("""
        INSERT INTO bird_observations (
            Admin_Unit_Code, Location_Type, Interval_Length, ID_Method, Year, Month, Date, Scientific_Name,
            Common_Name, Temperature, Humidity, Distance, Flyover_Observed, Sex,
            PIF_Watchlist_Status, Regional_Stewardship_Status, Disturbance, Plot_Name, Sky, Wind, Observer, Visit
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """)
        cursor.execute(insert_query, tuple(row))
    conn.commit()

    cursor.close()
    conn.close()

# Main Function for Execution
if __name__ == "__main__":
    # Load and clean data
    df = load_and_clean_data()

    # Store data in PostgreSQL
    store_data_in_postgres(df)
    print("Data successfully loaded into PostgreSQL!")
