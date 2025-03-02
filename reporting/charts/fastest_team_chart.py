import pandas as pd
import streamlit as st


def calculate_team_avg_lap(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame]:
    team_avg_lap = (
        df[df["lap_number"] > 1]
        .groupby(["team_name", "team_colour"])["lap_duration_selected"]
        .mean()
        .reset_index()
    )
    team_avg_lap.columns = ["team_name", "team_colour", "avg_lap_duration"]

    if not team_avg_lap.empty:
        fastest_team = team_avg_lap.loc[team_avg_lap["avg_lap_duration"].idxmin()]
        team_avg_lap["avg_lap_diff"] = (
            team_avg_lap["avg_lap_duration"] - fastest_team["avg_lap_duration"]
        )
    else:
        fastest_team = pd.Series({"team_name": "N/A", "avg_lap_duration": 0})
        team_avg_lap["avg_lap_diff"] = 0

    team_avg_lap["avg_lap_diff"] = (
        team_avg_lap["avg_lap_duration"] - fastest_team["avg_lap_duration"]
    )

    team_avg_lap["text"] = team_avg_lap.apply(
        lambda row: (
            f"Team {row['team_name']} is {row['avg_lap_diff']:.3f} seconds slower than Team {fastest_team['team_name']}"
            if row["team_name"] != fastest_team["team_name"]
            else f"Team {row['team_name']} is the fastest"
        ),
        axis=1,
    )
    team_avg_lap.sort_values(by="avg_lap_diff", inplace=True)
    return team_avg_lap, fastest_team


def create_fastest_team_chart(
    df: pd.DataFrame,
):
    team_avg_lap, fastest_team = calculate_team_avg_lap(df=df)

    for _, row in team_avg_lap.iterrows():
        team_name = row["team_name"]
        avg_lap_diff = row["avg_lap_diff"]
        team_color = row["team_colour"]

        if team_name != fastest_team["team_name"]:
            st.markdown(
                f"<span style='font-size: 22px;'><b><span style='color:{team_color}; font-weight:bold;'>{team_name}</span></b> is {avg_lap_diff:.3f} seconds slower than {fastest_team['team_name']}.</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<span style='font-size: 22px;'><b><span style='color:{team_color}; font-weight:bold;'>{team_name}</span></b> is the faster car.</span>",
                unsafe_allow_html=True,
            )
