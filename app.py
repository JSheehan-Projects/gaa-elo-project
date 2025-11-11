import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_summary_data(file_path, county_col_name): # <-- Add it here
    # 1. Load *only* the "Elo values" sheet
    df_summary = pd.read_excel(file_path, sheet_name="Elo values")

    # 2. Create the rename mapping
    rename_mapping = {
        county_col_name: 'County', # <-- Use the new parameter
        'Today': 'EOY 2025'
    }
    for year in range(2009, 2025): # 2009 up to (but not including) 2025
        rename_mapping[f'end of {year}'] = f'EOY {year}'

    # 3. Apply the rename
    df_summary = df_summary.rename(columns=rename_mapping)

    # 4. Melt into long format
    df_long = df_summary.melt(
        id_vars=['County'],
        var_name='Season_Text', # We'll rename this after cleaning
        value_name='ELO'
    )

    # 5. Clean up the Season column
    # This turns 'EOY 2025' into '2025'
    df_long['Year'] = df_long['Season_Text'].str.extract('(\d{4})').astype(int)
    
    # Drop any rows where we couldn't find a year (if any)
    df_long = df_long.dropna(subset=['Year'])

    return df_long

# --- Load both datasets --- ratings - Football.xlsx"

football_summary_df = load_summary_data("data/🏐 GAA Elo ratings - Football.xlsx", county_col_name='Unnamed: 0')
hurling_summary_df = load_summary_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_col_name='Team')

# --- Sidebar ---
st.sidebar.title("GAA ELO Explorer 🏐🏑")

selected_sport = st.sidebar.radio(
    "Select Sport",
    ("Football", "Hurling"),
    horizontal=True
)

# --- Dynamically assign data ---
if selected_sport == "Football":
    df = football_summary_df
    default_teams = ["Dublin", "Kerry"]
else:
    df = hurling_summary_df
    default_teams = ["Limerick", "Kilkenny", "Cork", "Tipperary"]
# --- Sidebar Filters ---
all_teams = sorted(df['County'].unique())

select_all = st.sidebar.checkbox("Select All Counties", value=False)

if select_all:
    # If checked, just use all teams
    selected_teams = all_teams 
    # We can also disable the multiselect to make it clear
    st.sidebar.multiselect(
        "Select Teams to Compare",
        options=all_teams,
        default=all_teams, # Show all as selected
        disabled=True
    )
else:
    # If not checked, show the normal multiselect
    selected_teams = st.sidebar.multiselect(
        "Select Teams to Compare",
        options=all_teams,
        default=default_teams # This uses your new default list
    )

st.sidebar.markdown("---") # Adds a nice separator line
st.sidebar.markdown(
    """
    **Data Source Credit**
    
    All ELO data compiled and maintained by Gavan Reilly.

    * [Football Data Sheet](https://docs.google.com/spreadsheets/d/1y5VpAqogmLXSVOBYKaGLKX2YOaAOZOJK2SYIN2SpgrA/edit?usp=sharing)
    * [Hurling Data Sheet](https://docs.google.com/spreadsheets/d/1qMFKYJedRQJW0OaokjPuxGLaiKNvLybrBSQdvxSLr2E/edit?usp=sharing)
    """
)

# --- Main Page ---
st.title(f"{selected_sport} End-of-Year ELO Values")

# --- Plot ---
if not selected_teams:
    st.warning("Please select at least one team from the sidebar.")
else:
    # Filter the data based on user's selection
    plot_df = df[df['County'].isin(selected_teams)]
    
# Sort the data by Year in ascending order
    plot_df = plot_df.sort_values(by="Year")

    # Create the line chart
    fig = px.line(
        plot_df,
        x="Year",    # Use our new numeric Year column for the x-axis
        y="ELO",
        color="County", # One line per county
        title="End-of-Year ELO Rating Over Time"
    )
    
    # Ensure the x-axis treats years as distinct categories (optional, but nice)
    fig.update_xaxes(type='category') 
    
    st.plotly_chart(fig, use_container_width=True)