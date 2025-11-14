import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
        'Home?': 'Home',
        'Result T1': 'ELO_Change_T1', 
        'Result T2': 'ELO_Change_T2'
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

#football_summary = load_summary_data("data/🏐 GAA Elo ratings - Football.xlsx", county_col_name='Unnamed: 0')
#hurling_summary = load_summary_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_col_name='Team')

# Get the unique county lists to pass to the next function
#football_counties = football_summary['County'].unique()
#hurling_counties = hurling_summary['County'].unique()

# Load detailed match data
#football_detail = load_match_data("data/🏐 GAA Elo ratings - Football.xlsx", county_list=football_counties)
#hurling_detail = load_match_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_list=hurling_counties)

# --- Sidebar ---
st.sidebar.title("GAA ELO Explorer 🏐🏑")

selected_sport = st.sidebar.radio(
    "Select Sport",
    ("Football", "Hurling"),
    horizontal=True,
    key='selected_sport'
)

st.sidebar.markdown("---") # Adds the separator line
st.sidebar.caption(
    """
    Created by Jack Sheehan.
    Link to [GitHub profile](https://github.com/JSheehan-Projects/).
    """
)
# --- Add Data Source Credit (moves to bottom of sidebar) ---
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Data Source Credit**
    
    All ELO data compiled and maintained by Gavan Reilly.
    
    * [Hurling Data Sheet](https://docs.google.com/spreadsheets/d/1qMFKYJedRQJW0OaokjPuxGLaiKNvLybrBSQdvxSLr2E/edit?usp=sharing)
    * [Football Data Sheet](https://docs.google.com/spreadsheets/d/1y5VpAqogmLXSVOBYKaGLKX2YOaAOZOJK2SYIN2SpgrA/edit?usp=sharing)
    """
)

# --- DYNAMIC DATA ASSIGNMENT ---
# Assign data based on the sidebar selection
#if selected_sport == "Football":
#    df_summary = football_summary
#    df_detail = football_detail
#    default_summary_teams = ["Dublin", "Kerry"]
#    default_detail_teams = ["Dublin", "Kerry"] # Can be different
#else:
#    df_summary = hurling_summary
#    df_detail = hurling_detail
#    default_summary_teams = ["Limerick", "Kilkenny", "Cork", "Tipperary"]
#    default_detail_teams = ["Limerick", "Kilkenny"] # Can be different


if selected_sport == "Football":
    df_summary = load_summary_data("data/🏐 GAA Elo ratings - Football.xlsx", county_col_name='Unnamed: 0')
    
    football_counties = df_summary['County'].unique()
    df_detail = load_match_data("data/🏐 GAA Elo ratings - Football.xlsx", county_list=football_counties)
    
    default_summary_teams = ["Dublin", "Kerry"]
    default_detail_teams = ["Dublin", "Kerry"] 
else:
    df_summary = load_summary_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_col_name='Team')
    
    hurling_counties = df_summary['County'].unique()
    df_detail = load_match_data("data/⚾ GAA Elo ratings - Hurling.xlsx", county_list=hurling_counties)
    
    default_summary_teams = ["Limerick", "Kilkenny", "Cork", "Tipperary"]
    default_detail_teams = ["Limerick", "Kilkenny"]

# --- MAIN PAGE ---
st.title(f"Intercounty {selected_sport} ELO Ratings")

# --- CREATE THE TABS ---
tab1, tab2 = st.tabs(["End of Year Comparison", "Single Season Deep-Dive"])


# --- TAB 1: END OF YEAR SUMMARY ---
with tab1:
    st.header("Compare Team ELO at the End of Each Season")
    
    all_teams_summary = sorted(df_summary['County'].unique())
    
    select_all_summary = st.checkbox("Select All Counties", value=False, key="select_all_summary")
    
    if select_all_summary:
        selected_teams_summary = all_teams_summary
        st.multiselect(
            "Select Teams to Compare",
            options=all_teams_summary,
            default=all_teams_summary,
            disabled=True,
            key="teams_summary_disabled"
        )
    else:
        selected_teams_summary = st.multiselect(
            "Select Teams to Compare",
            options=all_teams_summary,
            default=default_summary_teams,
            key="teams_summary"
        )
    
    # Plotting logic for Tab 1
    if not selected_teams_summary:
        st.warning("Please select at least one team to compare.")
    else:
        plot_df_summary = df_summary[df_summary['County'].isin(selected_teams_summary)]
        plot_df_summary = plot_df_summary.sort_values(by="Year")
        
        fig_summary = px.line(
            plot_df_summary,
            x="Year",
            y="ELO",
            color="County",
            title="End-of-Year ELO Rating Over Time"
        )
        fig_summary.update_xaxes(type='category')
        st.plotly_chart(fig_summary, use_container_width=True)


# --- TAB 2: SINGLE SEASON DEEP-DIVE ---
# --- TAB 2: SINGLE SEASON DEEP-DIVE ---
# --- TAB 2: SINGLE SEASON DEEP-DIVE ---
with tab2:
    st.header("Track Team Progression During a Single Season")
    
    # --- Season Selector (Same as before) ---
    all_seasons = sorted(df_detail['Season'].unique(), reverse=True)
    selected_season = st.selectbox("First, select a season:", all_seasons)
    
    # Filter the detail_df for *only* the selected season
    season_df = df_detail[df_detail['Season'] == selected_season].copy()
    
    # Check if we have data
    if season_df.empty:
        st.warning(f"No match data found for {selected_season}.")
    else:
        # --- Team-Specific Plot (This now comes FIRST) ---
        st.subheader(f"Team-Specific Plot for {selected_season}")
        
        all_teams_season = sorted(season_df['County'].unique())
        
        select_all_season = st.checkbox("Select All Counties", value=False, key="select_all_season")

        if select_all_season:
            selected_teams_season = all_teams_season
            st.multiselect(
                "Select Teams to Compare",
                options=all_teams_season,
                default=all_teams_season,
                disabled=True,
                key="teams_season_disabled"
            )
        else:
            selected_teams_season = st.multiselect(
                "Select Teams to Compare",
                options=all_teams_season,
                default=default_detail_teams,
                key="teams_season"
            )
            
        if not selected_teams_season:
            st.warning("Please select at least one team to compare.")
        else:
            # (Your existing plot logic... no changes needed here)
            plot_df_season = season_df[season_df['County'].isin(selected_teams_season)]
            plot_df_season = plot_df_season[
                (plot_df_season['County'] == plot_df_season['Team 1']) |
                (plot_df_season['County'] == plot_df_season['Team 2'])
            ].copy()
            
            # (Your numpy .where() logic for Opponent, Score_For, etc. is all correct)
            plot_df_season['Opponent'] = np.where(
                plot_df_season['County'] == plot_df_season['Team 1'],
                plot_df_season['Team 2'],
                plot_df_season['Team 1']
            )
            plot_df_season['Score_For'] = np.where(
                plot_df_season['County'] == plot_df_season['Team 1'],
                plot_df_season['Sc_T1'],
                plot_df_season['Sc_T2']
            )
            plot_df_season['Score_Against'] = np.where(
                plot_df_season['County'] == plot_df_season['Team 1'],
                plot_df_season['Sc_T2'],
                plot_df_season['Sc_T1']
            )
            plot_df_season['ELO_Change'] = np.where(
                plot_df_season['County'] == plot_df_season['Team 1'],
                plot_df_season['ELO_Change_T1'],
                plot_df_season['ELO_Change_T2']
            )
            plot_df_season = plot_df_season.sort_values(by="Date")
            
            fig_season = px.line(
                plot_df_season,
                x="Date",
                y="ELO",
                color="County",
                title=f"ELO Progression During {selected_season} Season",
                hover_data={
                    "County": True,
                    "ELO": ":.0f",
                    "Opponent": True,
                    "Score_For": True,
                    "Score_Against": True,
                    "ELO_Change": ":.1f",
                    "Grade": True,
                    "Date": "|%B %d, %Y"
                }
            )
            fig_season.update_traces(line_shape='hv')
            st.plotly_chart(fig_season, use_container_width=True)

        
        # --- NEW LOCATION: TOP 5 SHOCKS OF THE SEASON ---
        # (This section is now below the plot)
        st.markdown("---") # Separator line
        st.subheader(f"Top 5 Biggest Shocks of {selected_season}")

        # 1. Get only the unique matches
        match_cols = ['Date', 'Team 1', 'Team 2', 'G_T1', 'P_T1', 'G_T2', 'P_T2', 'ELO_Change_T1', 'Grade']
        unique_matches_df = season_df[match_cols].drop_duplicates()

        # --- NEW: Convert G/P columns to integer for clean formatting ---
        g_p_cols = ['G_T1', 'P_T1', 'G_T2', 'P_T2']
        unique_matches_df[g_p_cols] = unique_matches_df[g_p_cols].fillna(0).astype(int)

        # 2. Calculate the 'Shock_Factor'
        unique_matches_df['Shock_Factor'] = unique_matches_df['ELO_Change_T1'].abs()

        # 3. Get the top 5
        top_5_shocks = unique_matches_df.sort_values(by='Shock_Factor', ascending=False).head(5)

        # 4. Display them
        for i, (index, row) in enumerate(top_5_shocks.iterrows()):
            
            # --- UPDATED LOGIC for score strings ---
            if row['ELO_Change_T1'] > 0: # Team 1 won
                winner, loser = row['Team 1'], row['Team 2']
                # Get winner's score
                g_w, p_w = row['G_T1'], row['P_T1']
                total_w = (g_w * 3) + p_w
                # Get loser's score
                g_l, p_l = row['G_T2'], row['P_T2']
                total_l = (g_l * 3) + p_l
                
                elo_change = row['ELO_Change_T1']
            else: # Team 2 won
                winner, loser = row['Team 2'], row['Team 1']
                # Get winner's score
                g_w, p_w = row['G_T2'], row['P_T2']
                total_w = (g_w * 3) + p_w
                # Get loser's score
                g_l, p_l = row['G_T1'], row['P_T1']
                total_l = (g_l * 3) + p_l

                elo_change = -row['ELO_Change_T1'] # Make the swing positive
            
            # Create the formatted score strings
            winner_score = f"{g_w}-{p_w} ({total_w})"
            loser_score = f"{g_l}-{p_l} ({total_l})"

            # Display the metric and the formatted string
            col1, col2 = st.columns([1, 4])
            col1.metric(label=f"Rank {i+1}", value=f"+{elo_change:.1f}", help="ELO Swing")
            
            col2.markdown(f"**{winner}** {winner_score} beat **{loser}** {loser_score}")
            col2.caption(f"**Competition:** {row['Grade']} | **Date:** {row['Date'].strftime('%B %d, %Y')}")