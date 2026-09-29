import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Strava Fitness Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# FILE PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATHS = [
    os.path.join(BASE_DIR, "data", "cleaned", "strava_master_dataset.csv"),
    os.path.join(BASE_DIR, "data", "strava_master_dataset.csv"),
    os.path.join(BASE_DIR, "data", "cleaned", "daily_activity_cleaned.csv"),
]

DB_PATHS = [
    os.path.join(BASE_DIR, "sql", "strava_fitness.db"),
    os.path.join(BASE_DIR, "strava_fitness.db"),
]


# =========================
# LOAD MASTER DATA
# =========================

@st.cache_data
def load_data():

    for path in DATA_PATHS:

        if os.path.exists(path):

            df = pd.read_csv(path)

            if "ActivityDate" in df.columns:
                df["ActivityDate"] = pd.to_datetime(
                    df["ActivityDate"],
                    errors="coerce"
                )

            return df

    return pd.DataFrame()


df = load_data()


# =========================
# LOAD DATABASE
# =========================

def get_database_path():

    for path in DB_PATHS:

        if os.path.exists(path):
            return path

    return None


DB_PATH = get_database_path()


# =========================
# DATABASE CONNECTION
# =========================

def get_connection():

    if DB_PATH is None:
        return None

    return sqlite3.connect(DB_PATH)


# =========================
# HELPER FUNCTIONS
# =========================

def column_exists(column_name):

    return column_name in df.columns


def numeric_average(column_name):

    if column_name not in df.columns:
        return 0

    return df[column_name].mean()


def distinct_users():

    if "Id" in df.columns:
        return df["Id"].nunique()

    return 0


# =========================
# SIDEBAR
# =========================

st.sidebar.title("🏃 Strava Fitness Analytics")

st.sidebar.markdown(
    "Analyze smart-device fitness data "
    "to understand activity, calories, steps and health behavior."
)

page = st.sidebar.radio(
    "Select Page",
    [
        "🏠 Dashboard",
        "📊 Fitness Analysis",
        "🗄️ SQL Analysis"
    ]
)

st.sidebar.markdown("---")

if not df.empty:

    st.sidebar.success(
        f"Dataset Loaded\n\n{df.shape[0]:,} records"
    )

else:

    st.sidebar.error("Dataset not found")


# =========================
# HOME DASHBOARD
# =========================

if page == "🏠 Dashboard":

    st.title("🏃 Strava Fitness Analytics Dashboard")

    st.markdown(
        "### Smart Device Usage & Fitness Behavior Analysis"
    )

    st.markdown(
        "This dashboard analyzes fitness-tracking data to understand "
        "consumer activity patterns, steps, distance, calories and health behavior."
    )

    st.markdown("---")

    if df.empty:

        st.error(
            "Master dataset could not be found. "
            "Please check the data/cleaned folder."
        )

        st.stop()

    # KPI values

    total_users = distinct_users()

    avg_steps = numeric_average("TotalSteps")

    avg_distance = numeric_average("TotalDistance")

    avg_calories = numeric_average("Calories")

    avg_sedentary = numeric_average("SedentaryMinutes")

    # KPI cards

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "Total Users",
            f"{total_users:,}"
        )

    with c2:
        st.metric(
            "Avg Daily Steps",
            f"{avg_steps:,.0f}"
        )

    with c3:
        st.metric(
            "Avg Distance",
            f"{avg_distance:,.2f}"
        )

    with c4:
        st.metric(
            "Avg Calories",
            f"{avg_calories:,.0f}"
        )

    with c5:
        st.metric(
            "Avg Sedentary Minutes",
            f"{avg_sedentary:,.0f}"
        )

    st.markdown("---")

    # Date filter

    if "ActivityDate" in df.columns:

        min_date = df["ActivityDate"].min()
        max_date = df["ActivityDate"].max()

        selected_dates = st.date_input(
            "Select Date Range",
            value=(min_date.date(), max_date.date())
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:

            start_date = pd.Timestamp(selected_dates[0])
            end_date = pd.Timestamp(selected_dates[1])

            filtered_df = df[
                (df["ActivityDate"] >= start_date)
                &
                (df["ActivityDate"] <= end_date)
            ].copy()

        else:

            filtered_df = df.copy()

    else:

        filtered_df = df.copy()

    st.markdown("### 📈 Activity Overview")

    col1, col2 = st.columns(2)

    with col1:

        if "ActivityDate" in filtered_df.columns and "TotalSteps" in filtered_df.columns:

            steps_data = (
                filtered_df
                .groupby("ActivityDate")["TotalSteps"]
                .mean()
                .reset_index()
                .set_index("ActivityDate")
            )

            st.subheader("Daily Steps")

            st.line_chart(
                steps_data,
                y="TotalSteps"
            )

    with col2:

        if "ActivityDate" in filtered_df.columns and "Calories" in filtered_df.columns:

            calories_data = (
                filtered_df
                .groupby("ActivityDate")["Calories"]
                .mean()
                .reset_index()
                .set_index("ActivityDate")
            )

            st.subheader("Daily Calories")

            st.line_chart(
                calories_data,
                y="Calories"
            )

    st.markdown("---")

    # Steps vs Calories

    if "TotalSteps" in filtered_df.columns and "Calories" in filtered_df.columns:

        st.subheader("🚶 Steps vs Calories")

        chart_data = filtered_df[
            ["TotalSteps", "Calories"]
        ].dropna()

        st.scatter_chart(
            chart_data,
            x="TotalSteps",
            y="Calories"
        )

    st.markdown("---")

    st.subheader("📋 Dataset Preview")

    st.dataframe(
        filtered_df.head(20),
        use_container_width=True
    )


# =========================
# FITNESS ANALYSIS
# =========================

elif page == "📊 Fitness Analysis":

    st.title("📊 Fitness & Health Analysis")

    if df.empty:

        st.error("Dataset not found.")

        st.stop()

    # Activity analysis

    st.header("1. Activity Analysis")

    activity_columns = [
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes",
        "SedentaryMinutes"
    ]

    available_activity_columns = [
        col for col in activity_columns
        if col in df.columns
    ]

    if available_activity_columns:

        activity_summary = (
            df[available_activity_columns]
            .mean()
            .sort_values(ascending=False)
        )

        st.bar_chart(activity_summary)

    else:

        st.warning(
            "Activity minute columns are not available."
        )

    st.markdown("---")

    # Steps analysis

    st.header("2. Daily Steps Analysis")

    if "ActivityDate" in df.columns and "TotalSteps" in df.columns:

        steps_analysis = (
            df.groupby("ActivityDate")["TotalSteps"]
            .mean()
            .reset_index()
            .set_index("ActivityDate")
        )

        st.line_chart(
            steps_analysis,
            y="TotalSteps"
        )

        highest_steps = df.loc[
            df["TotalSteps"].idxmax()
        ]

        st.info(
            f"Highest recorded steps: "
            f"{highest_steps['TotalSteps']:,.0f}"
        )

    st.markdown("---")

    # Calories

    st.header("3. Calories Analysis")

    if "ActivityDate" in df.columns and "Calories" in df.columns:

        calories_analysis = (
            df.groupby("ActivityDate")["Calories"]
            .mean()
            .reset_index()
            .set_index("ActivityDate")
        )

        st.line_chart(
            calories_analysis,
            y="Calories"
        )

    st.markdown("---")

    # Distance

    st.header("4. Distance Analysis")

    if "ActivityDate" in df.columns and "TotalDistance" in df.columns:

        distance_analysis = (
            df.groupby("ActivityDate")["TotalDistance"]
            .mean()
            .reset_index()
            .set_index("ActivityDate")
        )

        st.line_chart(
            distance_analysis,
            y="TotalDistance"
        )

    st.markdown("---")

    # Heart rate

    st.header("5. Heart Rate Analysis")

    heart_columns = [
        "AvgHeartRate",
        "Value"
    ]

    heart_column = None

    for col in heart_columns:

        if col in df.columns:

            heart_column = col
            break

    if heart_column is not None:

        heart_data = df[heart_column].dropna()

        if len(heart_data) > 0:

            st.metric(
                "Average Heart Rate",
                f"{heart_data.mean():.1f}"
            )

            st.metric(
                "Maximum Heart Rate",
                f"{heart_data.max():.1f}"
            )

    else:

        st.info(
            "Average heart-rate column is not available in the master dataset."
        )

    st.markdown("---")

    # Activity intensity

    st.header("6. Activity Intensity")

    if "TotalSteps" in df.columns:

        analysis_df = df.copy()

        def classify_activity(steps):

            if pd.isna(steps):
                return "Unknown"

            if steps < 5000:
                return "Low Activity"

            elif steps < 10000:
                return "Moderate Activity"

            else:
                return "High Activity"

        analysis_df["Activity_Level"] = (
            analysis_df["TotalSteps"]
            .apply(classify_activity)
        )

        activity_count = (
            analysis_df["Activity_Level"]
            .value_counts()
        )

        st.bar_chart(activity_count)

        st.dataframe(
            analysis_df[
                ["Activity_Level", "TotalSteps"]
            ].head(20),
            use_container_width=True
        )

    st.markdown("---")

    # User analysis

    st.header("7. User-Level Fitness Analysis")

    if "Id" in df.columns and "TotalSteps" in df.columns:

        user_columns = ["Id"]

        aggregation = {
            "TotalSteps": "mean"
        }

        if "Calories" in df.columns:
            aggregation["Calories"] = "mean"

        if "TotalDistance" in df.columns:
            aggregation["TotalDistance"] = "mean"

        user_summary = (
            df.groupby("Id")
            .agg(aggregation)
            .reset_index()
        )

        user_summary = user_summary.sort_values(
            "TotalSteps",
            ascending=False
        )

        st.dataframe(
            user_summary.head(20),
            use_container_width=True
        )

        st.download_button(
            "⬇️ Download User Analysis",
            data=user_summary.to_csv(index=False),
            file_name="user_fitness_analysis.csv",
            mime="text/csv"
        )


# =========================
# SQL ANALYSIS
# =========================

elif page == "🗄️ SQL Analysis":

    st.title("🗄️ SQL Analysis")

    st.markdown(
        "Run predefined SQL analytics queries on the fitness database."
    )

    if DB_PATH is None:

        st.error(
            "SQLite database not found. "
            "Expected file: sql/strava_fitness.db"
        )

        st.stop()

    conn = get_connection()

    try:

        # Get tables

        tables_df = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """,
            conn
        )

        if tables_df.empty:

            st.error(
                "No tables found in the SQLite database."
            )

            st.stop()

        table_names = tables_df["name"].tolist()

        selected_table = st.selectbox(
            "Select Database Table",
            table_names
        )

        st.success(
            f"Connected to database: {os.path.basename(DB_PATH)}"
        )

        st.markdown("---")

        # Predefined SQL queries

        queries = {}

        queries["1. Total Records"] = f"""
        SELECT COUNT(*) AS Total_Records
        FROM "{selected_table}";
        """

        queries["2. Total Unique Users"] = f"""
        SELECT COUNT(DISTINCT Id) AS Total_Users
        FROM "{selected_table}";
        """

        queries["3. Average Daily Steps"] = f"""
        SELECT ROUND(AVG(TotalSteps), 2) AS Avg_Daily_Steps
        FROM "{selected_table}";
        """

        queries["4. Average Calories Burned"] = f"""
        SELECT ROUND(AVG(Calories), 2) AS Avg_Calories
        FROM "{selected_table}";
        """

        queries["5. Average Distance"] = f"""
        SELECT ROUND(AVG(TotalDistance), 2) AS Avg_Distance
        FROM "{selected_table}";
        """

        queries["6. Highest Steps Recorded"] = f"""
        SELECT
            Id,
            ActivityDate,
            TotalSteps
        FROM "{selected_table}"
        ORDER BY TotalSteps DESC
        LIMIT 10;
        """

        queries["7. Highest Calories Burned"] = f"""
        SELECT
            Id,
            ActivityDate,
            Calories
        FROM "{selected_table}"
        ORDER BY Calories DESC
        LIMIT 10;
        """

        queries["8. Top Users by Average Steps"] = f"""
        SELECT
            Id,
            ROUND(AVG(TotalSteps), 2) AS Avg_Steps
        FROM "{selected_table}"
        GROUP BY Id
        ORDER BY Avg_Steps DESC
        LIMIT 10;
        """

        queries["9. Activity Level Analysis"] = f"""
        SELECT
            CASE
                WHEN TotalSteps < 5000 THEN 'Low Activity'
                WHEN TotalSteps < 10000 THEN 'Moderate Activity'
                ELSE 'High Activity'
            END AS Activity_Level,
            COUNT(*) AS Records,
            ROUND(AVG(TotalSteps), 2) AS Avg_Steps,
            ROUND(AVG(Calories), 2) AS Avg_Calories
        FROM "{selected_table}"
        GROUP BY Activity_Level
        ORDER BY Avg_Steps DESC;
        """

        queries["10. Daily Activity Summary"] = f"""
        SELECT
            ActivityDate,
            ROUND(AVG(TotalSteps), 2) AS Avg_Steps,
            ROUND(AVG(TotalDistance), 2) AS Avg_Distance,
            ROUND(AVG(Calories), 2) AS Avg_Calories
        FROM "{selected_table}"
        GROUP BY ActivityDate
        ORDER BY ActivityDate;
        """

        queries["11. Average Sedentary Minutes"] = f"""
        SELECT
            ROUND(AVG(SedentaryMinutes), 2)
            AS Avg_Sedentary_Minutes
        FROM "{selected_table}";
        """

        queries["12. Activity Minutes Summary"] = f"""
        SELECT
            ROUND(AVG(VeryActiveMinutes), 2)
            AS Avg_VeryActive_Minutes,

            ROUND(AVG(FairlyActiveMinutes), 2)
            AS Avg_FairlyActive_Minutes,

            ROUND(AVG(LightlyActiveMinutes), 2)
            AS Avg_LightlyActive_Minutes,

            ROUND(AVG(SedentaryMinutes), 2)
            AS Avg_Sedentary_Minutes

        FROM "{selected_table}";
        """

        selected_query_name = st.selectbox(
            "Select SQL Analysis",
            list(queries.keys())
        )

        selected_query = queries[selected_query_name]

        st.code(
            selected_query,
            language="sql"
        )

        if st.button(
            "▶️ Run SQL Query",
            type="primary"
        ):

            try:

                result = pd.read_sql_query(
                    selected_query,
                    conn
                )

                st.subheader("Query Result")

                st.dataframe(
                    result,
                    use_container_width=True
                )

                st.download_button(
                    "⬇️ Download Result",
                    data=result.to_csv(index=False),
                    file_name="sql_result.csv",
                    mime="text/csv"
                )

            except Exception as e:

                st.error(
                    f"SQL query could not be executed: {e}"
                )

        st.markdown("---")

        st.subheader("📝 Custom SQL Query")

        custom_query = st.text_area(
            "Enter your SQL query",
            height=150,
            placeholder="SELECT * FROM fitness_data LIMIT 10;"
        )

        if st.button("Run Custom Query"):

            if custom_query.strip():

                try:

                    custom_result = pd.read_sql_query(
                        custom_query,
                        conn
                    )

                    st.dataframe(
                        custom_result,
                        use_container_width=True
                    )

                except Exception as e:

                    st.error(
                        f"Query Error: {e}"
                    )

            else:

                st.warning(
                    "Please enter a SQL query."
                )

    finally:

        conn.close()


# =========================
# FOOTER
# =========================

st.markdown("---")

st.markdown(
    "<center>Strava Fitness Analytics | "
    "Python • SQL • Streamlit • Power BI</center>",
    unsafe_allow_html=True
)