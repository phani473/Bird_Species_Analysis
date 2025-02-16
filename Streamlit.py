import pandas as pd
import streamlit as st
import psycopg2
import plotly.express as px

# Step 1: Connect to PostgreSQL Database
def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            dbname="bird_db",
            user="postgres",  # Replace with actual username
            password="Phani@1pk",  # Replace with actual password
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Step 2: Query Data from PostgreSQL
def query_data_from_postgres(query):
    conn = connect_to_postgres()
    if conn is None:
        return pd.DataFrame()  # Return empty DataFrame if connection fails
    
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Failed to execute query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# Step 3: Exploratory Data Analysis (EDA)
def perform_eda(df):
    st.header("Exploratory Data Analysis (EDA)")

    if df.empty:
        st.warning("No data available for analysis.")
        return

    # Temporal Analysis: Observations by Date
    if "date" in df.columns:
        st.subheader("Observations by Date")
        df["date"] = pd.to_datetime(df["date"])  # Ensure date is in datetime format
        date_counts = df["date"].value_counts().sort_index()
        fig = px.line(x=date_counts.index, y=date_counts.values, labels={'x': 'Date', 'y': 'Number of Observations'})
        st.plotly_chart(fig)


    # Spatial Analysis: Species Diversity by Location Type
    if "location_type" in df.columns and "scientific_name" in df.columns:
        st.subheader("Species Diversity by Location Type")

        # Calculate species richness (number of unique species) per location type
        location_diversity = df.groupby('location_type')['scientific_name'].nunique().reset_index()
        location_diversity.columns = ['Location Type', 'Number of Species']  # More descriptive column names

        # Create bar chart
        fig_species_diversity = px.bar(
            location_diversity, 
            x='Location Type', 
            y='Number of Species', 
            title='Species Richness by Location Type', # Title added
            color='Location Type', # Color added
            labels={'Number of Species': 'Number of Unique Species'}  # Clearer label
        )
        st.plotly_chart(fig_species_diversity)


        # Enhanced Visualization: Species Composition by Location Type (Optional)
        st.subheader("Species Composition by Location Type")

        # Group by location type and species, then count occurrences
        species_composition = df.groupby(['location_type', 'scientific_name']).size().reset_index(name='count')

        # Create a more informative bar chart (stacked bar chart)
        fig_species_comp = px.bar(
            species_composition, 
            x='location_type', 
            y='count', 
            color='scientific_name',  # Different color for each species
            title='Species Composition by Location Type', # Title added
            labels={'count': 'Number of Observations', 'scientific_name': 'Species'}, # Clearer labels
            barmode='stack' # Stacked bar chart
        )
        st.plotly_chart(fig_species_comp)


    # Environmental Conditions: Temperature vs. Observations
    if "temperature" in df.columns and "scientific_name" in df.columns:
        st.subheader("Temperature vs. Observations")
        fig = px.bar(df, x='temperature', y='scientific_name', color='location_type', labels={'x': 'Temperature', 'y': 'Species'})
        st.plotly_chart(fig)

    # Conservation Insights: At-Risk Species
    if "pif_watchlist_status" in df.columns and "scientific_name" in df.columns:
        st.subheader("At-Risk Species")
        at_risk_species = df[df['pif_watchlist_status'] == True]['scientific_name'].value_counts().reset_index()
        at_risk_species.columns = ['Species', 'Count']
        fig = px.bar(at_risk_species, x='Species', y='Count', labels={'x': 'Species', 'y': 'Number of Observations'})
        st.plotly_chart(fig)

# Step 4: Create Streamlit Dashboard
def create_dashboard(df):
    st.title("Bird Species Observation Analysis")
    st.write("This dashboard provides insights into bird species distribution and diversity across forests and grasslands.")

    if df.empty:
        st.warning("No data available.")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    # Fix column name casing and check existence
    if "location_type" in df.columns:
        location_type = st.sidebar.selectbox("Select Location Type", ["All", "Forest", "Grassland"])
    else:
        st.sidebar.write("Location Type data not available.")
        location_type = "All"
    
    # Date filtering
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])  # Convert to datetime format
        min_date, max_date = df["date"].min(), df["date"].max()
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    else:
        st.sidebar.write("Date data not available.")
        date_range = None

    # Apply filters
    filtered_df = df
    if location_type and location_type != "All":
        filtered_df = filtered_df[filtered_df['location_type'] == location_type]
    if date_range and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]
    
    # Display filtered data
    st.subheader("Filtered Data")
    st.write(filtered_df)

    # Perform EDA on filtered data
    perform_eda(filtered_df)

# Main Function for Streamlit App
if __name__ == "__main__":
    st.sidebar.title("Data Source")
    
    # Query data from PostgreSQL
    query = "SELECT * FROM bird_observations;"
    df_from_postgres = query_data_from_postgres(query)

    # Create Streamlit dashboard
    create_dashboard(df_from_postgres)
