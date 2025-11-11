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

# Add this new function to app.py
@st.cache_data
def load_match_data(file_path, county_list):
    """
    Loads all individual season tabs, stacks them, and melts the
    per-match ELO data into a long-format DataFrame.
    """
    xls = pd.ExcelFile(file_path)
    
    # 1. Get all year tabs (all sheets EXCEPT 'Elo values' and the other unneccessary sheets)
    year_sheets = [sheet for sheet in xls.sheet_names if sheet not in ["Elo values","Rules","2026"]]

    all_seasons_data = []
    for sheet in year_sheets:
        try:
            # 2. Load sheet, skipping row 2 (index 1) which is "starting values"
            df = pd.read_excel(xls, sheet_name=sheet, skiprows=[1])
            # Add season column
            df['Season'] = sheet
            all_seasons_data.append(df)
        except Exception as e:
            st.warning(f"Could not load or process sheet: {sheet}. Error: {e}")

    # 3. Combine all seasons into one big DataFrame
    if not all_seasons_data:
        return pd.DataFrame() # Return empty if no data
        
    full_df = pd.concat(all_seasons_data, ignore_index=True)

    # 4. Clean column names
    rename_map = {
        'Elo': 'Elo_T1', 'G': 'G_T1', 'P': 'P_T1', 'Sc': 'Sc_T1',
        'Elo.1': 'Elo_T2', 'G.1': 'G_T2', 'P.1': 'P_T2', 'Sc.1': 'Sc_T2',
        'Home?': 'Home'
        }
    full_df = full_df.rename(columns=rename_map)

    # --- 4.5. Manually merge the 'odds' columns (NEW STEP) ---
    if 'T1 win odds' in full_df.columns and 'Expect T1' in full_df.columns:
        # Use .combine_first() to take values from 'T1 win odds' and
        # fill any of its missing values with data from 'Expect T1'
        full_df['T1_Win_Odds'] = full_df['T1 win odds'].combine_first(full_df['Expect T1'])
        # Drop the original columns
        full_df = full_df.drop(columns=['T1 win odds', 'Expect T1'])
        
    elif 'T1 win odds' in full_df.columns:
        # If only one exists, just rename it
        full_df = full_df.rename(columns={'T1 win odds': 'T1_Win_Odds'})
        
    elif 'Expect T1' in full_df.columns:
        # If only the other exists, just rename it
        full_df = full_df.rename(columns={'Expect T1': 'T1_Win_Odds'})

    # 5. Drop all 'Unnamed' (blank) columns
    full_df = full_df.loc[:, ~full_df.columns.str.contains('^Unnamed')]

    # 6. Prepare for the melt
    # Find all columns that are county names (these are our ELO values)
    elo_cols = [col for col in full_df.columns if col in county_list]
    
    # id_vars are all columns that are NOT county ELO values
    id_cols = [col for col in full_df.columns if col not in elo_cols]

    # 7. Melt the ELO data!
    melted_df = full_df.melt(
        id_vars=id_cols,
        value_vars=elo_cols,
        var_name='County',
        value_name='ELO'
    )

    # 8. Final cleanup
    melted_df['Date'] = pd.to_datetime(melted_df['Date'])
    melted_df = melted_df.dropna(subset=['ELO']) # Drop rows where ELO is missing
    melted_df = melted_df.sort_values(by='Date')

    return melted_df

# --- Load both datasets --- ratings - Football.xlsx"

football_summary = load_summary_data("data/🏐 GAA Elo ratings - Football.xlsx", county_col_name='Unnamed: 0')
hurling_summary = load_summary_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_col_name='Team')

# Get the unique county lists to pass to the next function
football_counties = football_summary['County'].unique()
hurling_counties = hurling_summary['County'].unique()

# Load detailed match data
football_detail = load_match_data("data/🏐 GAA Elo ratings - Football.xlsx", county_list=football_counties)
hurling_detail = load_match_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_list=hurling_counties)

# --- Sidebar ---
st.sidebar.title("GAA ELO Explorer 🏐🏑")

selected_sport = st.sidebar.radio(
    "Select Sport",
    ("Football", "Hurling"),
    horizontal=True
)

analysis_type = st.sidebar.selectbox(
    "Select Analysis Type",
    ("End of Year Summary", "Detailed Match History")
)

# --- Dynamically assign data BASED ON BOTH selectors ---
if selected_sport == "Football":
    # Use the 'analysis_type' to pick which df to use
    df = football_summary if analysis_type == "End of Year Summary" else football_detail
    default_teams = ["Dublin", "Kerry"]
else:
    df = hurling_summary if analysis_type == "End of Year Summary" else hurling_detail
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
st.title(f"{selected_sport} - {analysis_type}")

# --- Plot ---
if not selected_teams:
    st.warning("Please select at least one team from the sidebar.")
else:
    plot_df = df[df['County'].isin(selected_teams)]
    
    # The x-axis needs to be dynamic
    # For summary, it's "Year". For detail, it's "Date".
    x_axis = "Year" if analysis_type == "End of Year Summary" else "Date"
    
    # Sort the data
    plot_df = plot_df.sort_values(by=x_axis) 
    
    fig = px.line(
        plot_df,
        x=x_axis,
        y="ELO",
        color="County",
        title="ELO Rating Over Time"
    )
    
    if analysis_type == "End of Year Summary":
        fig.update_xaxes(type='category') # Keep years distinct
    
    st.plotly_chart(fig, use_container_width=True)