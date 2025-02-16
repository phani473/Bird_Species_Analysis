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
        location_diversity = df.groupby('location_type')['scientific_name'].nunique().reset_index()
        location_diversity.columns = ['Location Type', 'Number of Species']

        fig_species_diversity = px.bar(
            location_diversity, 
            x='Location Type', 
            y='Number of Species', 
            title='Species Richness by Location Type', 
            color='Location Type'
        )
        st.plotly_chart(fig_species_diversity)

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

    # Distance Analysis
    if "distance" in df.columns:
        st.subheader("Distance Analysis")
        distance_counts = df["distance"].value_counts().reset_index()
        distance_counts.columns = ["Distance", "Count"]
        
        fig_distance = px.bar(
            distance_counts,
            x="Distance",
            y="Count",
            title="Distribution of Observation Distances",
            labels={"Count": "Number of Observations"},
            color="Distance"
        )
        st.plotly_chart(fig_distance)

        # Distance Impact on Species Observations
        distance_impact = df.groupby(["distance", "scientific_name"]).size().reset_index(name="count")
        
        fig_distance_impact = px.bar(
            distance_impact,
            x="distance",
            y="count",
            color="scientific_name",
            title="Impact of Distance on Species Observations",
            labels={"count": "Number of Observations", "distance": "Distance"},
            barmode="stack"
        )
        st.plotly_chart(fig_distance_impact)

    # Disturbance Analysis
    if "disturbance" in df.columns:
        st.subheader("Disturbance Analysis")

        # Distribution of Disturbance Types
        disturbance_counts = df["disturbance"].value_counts().reset_index()
        disturbance_counts.columns = ["Disturbance Type", "Count"]
        
        fig_disturbance = px.bar(
            disturbance_counts, 
            x="Disturbance Type", 
            y="Count", 
            title="Distribution of Disturbance Types",
            labels={"Count": "Number of Observations"},
            color="Disturbance Type"
        )
        st.plotly_chart(fig_disturbance)

        # Impact of Disturbance on Observations
        disturbance_impact = df.groupby(["disturbance", "scientific_name"]).size().reset_index(name="count")

        fig_disturbance_impact = px.bar(
            disturbance_impact,
            x="disturbance",
            y="count",
            color="scientific_name",
            title="Impact of Disturbance on Species Observations",
            labels={"count": "Number of Observations", "disturbance": "Disturbance Type"},
            barmode="stack"
        )
        st.plotly_chart(fig_disturbance_impact)

# Step 4: Create Streamlit Dashboard
def create_dashboard(df):
    st.title("Bird Species Observation Analysis")
    st.write("This dashboard provides insights into bird species distribution and diversity across forests and grasslands.")

    if df.empty:
        st.warning("No data available.")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    if "location_type" in df.columns:
        location_type = st.sidebar.selectbox("Select Location Type", ["All", "Forest", "Grassland"])
    else:
        st.sidebar.write("Location Type data not available.")
        location_type = "All"

    if "admin_unit_code" in df.columns:
        admin_units = df["admin_unit_code"].unique()
        selected_admin_unit = st.sidebar.selectbox("Select Admin Unit Code", ["All"] + list(admin_units))
    else:
        selected_admin_unit = "All"
    
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        min_date, max_date = df["date"].min(), df["date"].max()
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    else:
        st.sidebar.write("Date data not available.")
        date_range = None

    if "disturbance" in df.columns:
        disturbance_type = st.sidebar.multiselect("Select Disturbance Type", options=df["disturbance"].unique(), default=df["disturbance"].unique())
    else:
        st.sidebar.write("Disturbance data not available.")
        disturbance_type = None

    # Apply filters
    filtered_df = df
    if selected_admin_unit != "All":
        filtered_df = filtered_df[filtered_df['admin_unit_code'] == selected_admin_unit]
    if location_type and location_type != "All":
        filtered_df = filtered_df[filtered_df['location_type'] == location_type]
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]
    if disturbance_type:
        filtered_df = filtered_df[filtered_df['disturbance'].isin(disturbance_type)]

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
