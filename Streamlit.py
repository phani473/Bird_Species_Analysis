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
    
    # 1. Temporal Analysis: Observations by Date
    st.subheader("1. Temporal Analysis Observations by Date")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])  # Ensure date is in datetime format
        date_counts = df["date"].value_counts().sort_index()
        fig = px.line(x=date_counts.index, y=date_counts.values, labels={'x': 'Date', 'y': 'Number of Observations'})
        st.plotly_chart(fig)
        st.write("**Summary:** The temporal analysis shows the number of bird observations over time. Peaks in the graph indicate periods of higher bird activity, which may correlate with migration or breeding seasons.")

    # 2. Spatial Analysis: Species Diversity by Location Type
    st.subheader("2. Spatial Analysis")
    if "location_type" in df.columns and "scientific_name" in df.columns:
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
        st.write("**Summary:** This chart compares species richness across different location types (e.g., forest, grassland). It highlights which habitats support the highest biodiversity.")

    # Plot-Level Analysis: Observations by Plot Name
    if "plot_name" in df.columns:
        plot_observations = df.groupby('plot_name')['scientific_name'].nunique().reset_index()
        plot_observations.columns = ['Plot Name', 'Number of Species']
        fig_plot_observations = px.bar(plot_observations, x='Plot Name', y='Number of Species', title='Species Observations by Plot Name', color='Plot Name')
        st.plotly_chart(fig_plot_observations)
        st.write("**Summary:** This analysis shows the number of unique species observed in each plot. Plots with higher species counts may indicate biodiversity hotspots.")

    # 3. Species Analysis
    st.subheader("3. Species Analysis")
    # Activity Patterns: Check most common activity types
    if "interval_length" in df.columns and "id_method" in df.columns:
        activity_patterns = df.groupby(['interval_length', 'id_method']).size().reset_index(name='Observations')
        fig_activity = px.bar(activity_patterns, x='interval_length', y='Observations', color='id_method', title="Activity Patterns by Interval Length and Method")
        st.plotly_chart(fig_activity)
        st.write("**Summary:** This chart shows the most common bird activity patterns based on observation intervals and identification methods. It helps identify preferred observation durations and methods.")

    # Sex Ratio: Analyze male-to-female ratio for different species
    if "sex" in df.columns:
        sex_ratio = df.groupby(['scientific_name', 'sex']).size().reset_index(name='Count')
        fig_sex_ratio = px.bar(sex_ratio, x='scientific_name', y='Count', color='sex', title="Sex Ratio for Species")
        st.plotly_chart(fig_sex_ratio)
        st.write("**Summary:** The sex ratio analysis reveals the male-to-female distribution across species. Some species may show a skewed ratio, which could indicate gender-based behavioral differences.")

    # 4. Environmental Conditions: Weather Correlation
    if "temperature" in df.columns and "humidity" in df.columns and "sky" in df.columns and "wind" in df.columns:
        st.subheader("4. Environmental Conditions: Weather Correlation")
        weather_conditions = df.groupby(['temperature', 'humidity', 'sky', 'wind']).size().reset_index(name='Observations')
        fig_weather = px.scatter(weather_conditions, x='temperature', y='humidity', color='sky', title="Weather Correlation with Observations")
        st.plotly_chart(fig_weather)
        st.write("**Summary:** This scatter plot explores the relationship between weather conditions (temperature, humidity, sky, wind) and bird observations. Certain weather conditions may correlate with higher bird activity.")

    if "disturbance" in df.columns:
        st.subheader("Impact of Disturbance on Bird Sightings")
        disturbance_effect = df.groupby('disturbance')['scientific_name'].count().reset_index()
        disturbance_effect.columns = ['Disturbance', 'Sighting_Count']
        fig = px.bar(disturbance_effect, 
                     x='Disturbance', 
                     y='Sighting_Count', 
                     title='Impact of Disturbance on Bird Sightings',
                     labels={'Disturbance': 'Disturbance Type', 'Sighting_Count': 'Number of Bird Sightings'},
                     color='Sighting_Count', color_continuous_scale='Viridis')
        fig.update_layout(xaxis_title='Disturbance Type', yaxis_title='Number of Bird Sightings')
        fig.update_xaxes(tickangle=45)  # Rotate x-axis labels for better readability
        st.plotly_chart(fig)
        st.write("**Summary:** This chart shows how different types of disturbances (e.g., human activity, weather events) impact bird sightings. Some disturbances may reduce bird activity, while others may have no significant effect.")

    # 5. Distance and Behavior
    st.subheader("5. Distance and Behavior")
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
        st.write("**Summary:** This bar chart shows the distribution of observation distances. It helps identify whether birds are typically observed closer or farther from the observer.")

    # Flyover Frequency: Detect trends in bird behavior during observation (Flyover_Observed)
    if "flyover_observed" in df.columns:
        st.subheader("Flyover Frequency Analysis")
        flyover_counts = df["flyover_observed"].value_counts().reset_index()
        flyover_counts.columns = ["Flyover Observed", "Count"]
        fig_flyover = px.bar(
            flyover_counts,
            x="Flyover Observed",
            y="Count",
            title="Flyover Frequency",
            labels={"Count": "Number of Observations"},
            color="Flyover Observed"
        )
        st.plotly_chart(fig_flyover)
        st.write("**Summary:** This chart shows how often flyovers (birds flying overhead) are observed. Frequent flyovers may indicate migration patterns or preferred flight paths.")

    # 6. Observer Trends & Bias Analysis
    st.subheader("6. Observer Trends")
    if "observer" in df.columns:
        observer_counts = df.groupby('observer')['scientific_name'].nunique().reset_index()
        observer_counts.columns = ['Observer', 'Unique Species Count']
        fig_observer_bias = px.bar(
            observer_counts, 
            x='Observer', 
            y='Unique Species Count', 
            title='Observer Trends and Bias', 
            color='Observer'
        )
        st.plotly_chart(fig_observer_bias)
        st.write("**Summary:** This chart highlights observer trends, showing how many unique species each observer has recorded. It helps identify potential observer bias or expertise.")

    # Visit Patterns: Evaluate repeated visits and species count/diversity
    if "visit" in df.columns:
        st.subheader("Visit Patterns Analysis")
        visit_counts = df.groupby('visit')['scientific_name'].nunique().reset_index()
        visit_counts.columns = ['Visit', 'Number of Unique Species']
        fig_visit_patterns = px.line(
            visit_counts, 
            x='Visit', 
            y='Number of Unique Species', 
            title='Visit Patterns and Species Diversity'
        )
        st.plotly_chart(fig_visit_patterns)
        st.write("**Summary:** This line chart shows how species diversity changes with repeated visits to the same location. Increased diversity over time may indicate effective monitoring or seasonal changes.")

    # 7. Conservation Insights: Watchlist Trends
    st.subheader("7. Conservation Insights")
    if "pif_watchlist_status" in df.columns and "regional_stewardship_status" in df.columns:
        # Watchlist status trends: Count species in each status category
        watchlist_status_counts = df.groupby('pif_watchlist_status')['scientific_name'].nunique().reset_index()
        watchlist_status_counts.columns = ['Watchlist Status', 'Species Count']
        fig_watchlist = px.bar(watchlist_status_counts, x='Watchlist Status', y='Species Count', title='Species Count by PIF Watchlist Status', color='Watchlist Status')
        st.plotly_chart(fig_watchlist)
        st.write("**Summary:** This chart shows the number of species on the PIF Watchlist, highlighting those at risk and requiring conservation focus.")

        # Regional Stewardship Status trends
        stewardship_status_counts = df.groupby('regional_stewardship_status')['scientific_name'].nunique().reset_index()
        stewardship_status_counts.columns = ['Stewardship Status', 'Species Count']
        fig_stewardship = px.bar(stewardship_status_counts, x='Stewardship Status', y='Species Count', title='Species Count by Regional Stewardship Status', color='Stewardship Status')
        st.plotly_chart(fig_stewardship)
        st.write("**Summary:** This chart highlights species under regional stewardship, indicating areas where conservation efforts are most needed.")

    # 8. Distance vs. Species Heatmap
    if "distance" in df.columns and "scientific_name" in df.columns:
        distance_impact = df.groupby(["distance", "scientific_name"]).size().reset_index(name="count")
        st.subheader("8. Distance vs. Species Heatmap")
        fig_heatmap = px.density_heatmap(
            distance_impact,
            x="distance",
            y="scientific_name",
            z="count",
            title="Heatmap of Distance vs. Species Observations",
            labels={"count": "Observation Density", "distance": "Distance", "scientific_name": "Species"},
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_heatmap)
        st.write("**Summary:** This heatmap shows the relationship between observation distance and species. It helps identify species that are typically observed at specific distances.")

    # 9. Number of Bird Species Observed at Different Temperatures
    if "temperature" in df.columns and "scientific_name" in df.columns:
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
        df_cleaned = df.dropna(subset=['temperature', 'scientific_name'])
        temp_bird_counts = df_cleaned.groupby('temperature')['scientific_name'].nunique().reset_index()
        temp_bird_counts.columns = ['Temperature', 'Number of Species']
        fig = px.bar(temp_bird_counts, x='Temperature', y='Number of Species', 
                     title='9. Number of Bird Species Observed at Different Temperatures',
                     labels={'Temperature': 'Temperature (°C)', 'Number of Species': 'Unique Species Count'})
        st.plotly_chart(fig)
        st.write("**Summary:** This chart shows how bird species diversity varies with temperature. Certain temperature ranges may support higher biodiversity.")

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
