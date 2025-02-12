import sys
import logging

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
import pendulum
import time
from requests import Request

from calls.openf1 import OpenF1Connector

# pandas config
pd.set_option("future.no_silent_downcasting", True)

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s %(name)s: %(levelname)-4s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="Real-Time F1 Lap Times",
    page_icon="🏎️",
    layout="wide",
)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Applies user-selected filters to the dataframe."""

    # Create two columns for team and driver filters
    col1, col2 = st.columns(2)
    with col1:
        team_filter = st.multiselect("Select the team(s)", pd.unique(df["team_name"]))

    min_lap_number = df["lap_number"].min()
    max_lap_number = df["lap_number"].max()
    selected_lap_range = st.slider(
        "Select lap range",
        min_lap_number,
        max_lap_number,
        (min_lap_number, max_lap_number),
    )
    smooth_pit_laps = st.checkbox("Smoothen pit in/out laps")

    if team_filter:
        df = df[df["team_name"].isin(team_filter)]

    with col2:
        driver_filter = st.multiselect(
            "Select the driver(s)", pd.unique(df["last_name"])
        )
    if driver_filter:
        df = df[df["last_name"].isin(driver_filter)]

    df = df[df["lap_number"].between(selected_lap_range[0], selected_lap_range[1])]
    return df, smooth_pit_laps


def calculate_fields(df: pd.DataFrame, smooth_pit_laps: bool) -> pd.DataFrame:
    """Calculates additional fields needed for the visualization."""
    df["lap_duration_actual"] = df["lap_duration"]
    df["lap_duration_actual_str"] = df["lap_duration_actual"].apply(
        lambda x: f"{int(x // 60)}:{int(x % 60):02}.{int((x % 1) * 1000):03}"
    )

    df["is_pit_in_lap"] = (
        df.sort_values(by=["lap_number"], ascending=True)
        .groupby(["name_acronym"])["is_pit_out_lap"]
        .shift(-1)
        .fillna(False)
        .infer_objects(copy=False)
    )

    if smooth_pit_laps:

        def calculate_avg_sector_after_pit_out(df: pd.DataFrame) -> tuple:
            avg_sector_1_after_pit_out = []
            avg_sector_3_before_pit_in = []

            for _, row in df.iterrows():
                if row["is_pit_out_lap"]:
                    next_laps = df[
                        (df["name_acronym"] == row["name_acronym"])
                        & (df["lap_number"] > row["lap_number"])
                    ].sort_values(by=["lap_number"], ascending=True)[
                        "duration_sector_1"
                    ]

                    avg_sector_1_duration = (
                        next_laps.head(3).mean().round(3)
                        if len(next_laps) >= 3
                        else (
                            next_laps.mean().round(3) if len(next_laps) > 0 else np.nan
                        )
                    )
                    avg_sector_1_after_pit_out.append(avg_sector_1_duration)
                    avg_sector_3_before_pit_in.append(np.nan)

                elif row["is_pit_in_lap"]:
                    previous_laps = df[
                        (df["name_acronym"] == row["name_acronym"])
                        & (df["lap_number"] < row["lap_number"])
                    ].sort_values(by=["lap_number"], ascending=False)[
                        "duration_sector_3"
                    ]

                    avg_sector_3_duration = (
                        previous_laps.head(3).mean().round(3)
                        if len(previous_laps) >= 3
                        else (
                            previous_laps.mean().round(3)
                            if len(previous_laps) > 0
                            else np.nan
                        )
                    )
                    avg_sector_3_before_pit_in.append(avg_sector_3_duration)
                    avg_sector_1_after_pit_out.append(np.nan)

                else:
                    avg_sector_1_after_pit_out.append(np.nan)
                    avg_sector_3_before_pit_in.append(np.nan)

            return avg_sector_1_after_pit_out, avg_sector_3_before_pit_in

        avg_sector_1_after_pit_out, avg_sector_3_before_pit_out = (
            calculate_avg_sector_after_pit_out(df)
        )
        df["avg_sector_1_after_pit_out"] = avg_sector_1_after_pit_out
        df["avg_sector_3_before_pit_out"] = avg_sector_3_before_pit_out
        df["avg_sector_1_after_pit_out"] = df["avg_sector_1_after_pit_out"].fillna(
            df["duration_sector_1"]
        )
        df["avg_sector_3_before_pit_out"] = df["avg_sector_3_before_pit_out"].fillna(
            df["duration_sector_3"]
        )

        df["lap_duration"] = (
            df["avg_sector_1_after_pit_out"]
            + df["duration_sector_2"]
            + df["avg_sector_3_before_pit_out"]
        )

    min_laptime = df["lap_duration"].min()
    max_laptime = df["lap_duration"].max()

    driver_avg_lap = (
        df.groupby(["team_name", "name_acronym"])["lap_duration"].mean().reset_index()
    )
    driver_avg_lap.columns = ["team_name", "name_acronym", "avg_lap_duration"]
    driver_avg_lap["avg_lap_duration"] = driver_avg_lap["avg_lap_duration"].round(3)
    df = df.merge(
        driver_avg_lap[["team_name", "name_acronym", "avg_lap_duration"]],
        on=["team_name", "name_acronym"],
        how="inner",
    )

    team_slowest_driver = driver_avg_lap.loc[
        driver_avg_lap.groupby("team_name")["avg_lap_duration"].idxmax()
    ]
    team_slowest_driver["line_dash"] = "dashed"
    df = df.merge(
        team_slowest_driver[["team_name", "name_acronym", "line_dash"]],
        on=["team_name", "name_acronym"],
        how="left",
    )
    df["line_dash"] = df["line_dash"].fillna("solid")

    last_lap_df = df.loc[df.groupby("name_acronym")["lap_number"].idxmax()]
    df["lap_duration_str"] = df["lap_duration"].apply(
        lambda x: f"{int(x // 60)}:{int(x % 60):02}.{int((x % 1) * 1000):03}"
    )
    df["avg_lap_duration_str"] = df["avg_lap_duration"].apply(
        lambda x: f"{int(x // 60)}:{int(x % 60):02}.{int((x % 1) * 1000):03}"
    )

    team_avg_lap = (
        df.groupby(["team_name", "team_colour"])["lap_duration"].mean().reset_index()
    )
    team_avg_lap.columns = ["team_name", "team_colour", "avg_lap_duration"]
    fastest_team = team_avg_lap.loc[team_avg_lap["avg_lap_duration"].idxmin()]
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

    df["point_size"] = df["pit_duration"] ** 3

    return df, last_lap_df, min_laptime, max_laptime, team_avg_lap, fastest_team


def create_lap_times_chart(
    df: pd.DataFrame,
    last_lap_df: pd.DataFrame,
    min_laptime: float,
    max_laptime: float,
) -> alt.Chart:
    line_chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("lap_number:O", title="Lap Number", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(
                "lap_duration:Q",
                scale=alt.Scale(domain=[min_laptime, max_laptime]),
                title="Lap Time (s)",
            ),
            color=alt.Color("team_colour").scale(None),
            detail="name_acronym",
            strokeDash=alt.StrokeDash(
                "line_dash:N", sort=["solid", "dashed"], legend=None
            ),  # Set line dash pattern
            tooltip=[
                alt.Tooltip("name_acronym", title="Driver"),
                alt.Tooltip("lap_number", title="Lap #"),
                alt.Tooltip("lap_duration_str", title="Lap Time (m:ss.sss)"),
                alt.Tooltip("avg_lap_duration_str", title="Avg. lap time (m:ss.sss)"),
            ],  # Optional: add tooltips for better interactivity
        )
    )
    text_labels = (
        alt.Chart(last_lap_df)
        .mark_text(dx=5, dy=-5, align="left", size=16)
        .encode(
            x=alt.X("lap_number:O"),
            y="lap_duration",
            text="name_acronym",
            color=alt.Color("team_colour:N").scale(
                None
            ),  # Use 'team_colour' for the text color
        )
    )
    # Adding vertical lines to signify pit out laps
    pit_labels = (
        alt.Chart(df[df["is_pit_in_lap"]])
        .mark_text(dy=-20, size=12, color="black", fontWeight="bold")
        .encode(
            x=alt.X("lap_number:O", title="Lap Number"),
            y=alt.Y("lap_duration:Q", title="Lap Time (s)"),
            tooltip=[
                alt.Tooltip("name_acronym", title="Driver"),
                alt.Tooltip("lap_number", title="Lap #"),
                alt.Tooltip("lap_duration_str", title="Smoothened Lap Time (m:ss.sss)"),
                alt.Tooltip(
                    "lap_duration_actual_str", title="Actual Lap Time (m:ss.sss)"
                ),
                alt.Tooltip("pit_duration", title="Pit stop duration (s)"),
            ],
            text=alt.value("Pit stop"),
        )
    )
    # Points for pit out laps
    pit_points = (
        alt.Chart(df[df["is_pit_in_lap"]])
        .mark_point(color="black")  # Customize marker color and size
        .encode(
            x="lap_number:O",
            y="lap_duration:Q",
            size=alt.Size("point_size:Q", legend=None),
            tooltip=[
                alt.Tooltip("name_acronym", title="Driver"),
                alt.Tooltip("lap_number", title="Lap #"),
                alt.Tooltip(
                    "lap_duration_actual_str", title="Actual Lap Time (m:ss.sss)"
                ),
                alt.Tooltip("pit_duration", title="Pit stop duration (s)"),
            ],
        )
    )
    combined_chart = line_chart + text_labels + pit_points + pit_labels
    return combined_chart


def create_visualization(
    df: pd.DataFrame,
    last_lap_df: pd.DataFrame,
    min_laptime: float,
    max_laptime: float,
    team_avg_lap: pd.DataFrame,
    fastest_team: pd.DataFrame,
):
    """Creates the visualization based on the dataframe."""
    placeholder = st.empty()

    with placeholder.container():
        combined_chart = create_lap_times_chart(
            df, last_lap_df, min_laptime, max_laptime
        )
        st.markdown("### Lap times")
        st.altair_chart(combined_chart, use_container_width=True)

        # Display team average lap time differences
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


# Main script
f1 = OpenF1Connector()
SESSION_NAME = "Race"


def fetch_session(_f1: OpenF1Connector) -> tuple[Request, Request, Request] | str:
    current_meeting = _f1.get_meetings()
    if current_meeting.status_code == 200:
        meeting_key = current_meeting.json()[0]["meeting_key"]
        drivers = f1.get_drivers(meeting_key=meeting_key)
        session = f1.get_sessions(meeting_key=meeting_key, session_name=SESSION_NAME)
        if session.status_code == 200:
            log.info("Session found successfully, continuing...")
            return current_meeting, drivers, session
        log.info("Session is not available.")
        return "The requested session is not available 😔"
    log.info("Meeting is not available.")
    return "There is no race this weekend 😔"


def get_data(
    f1: OpenF1Connector,
    session_key: int,
    df_drivers: pd.DataFrame,
    df_meeting: pd.DataFrame,
    session_name: str,
) -> pd.DataFrame:
    log.info("Fetching laps data...")
    laps = f1.get_laps(session_key=session_key)
    pits = f1.get_pits(session_key=session_key)
    if laps.status_code != 200 and pits.status_code != 200:
        log.error("Unable to fetch data")
        return "Lap times and pit stops data is unavailable"
    df_pits = pd.DataFrame(pits.json())
    df_laps = pd.DataFrame(laps.json())
    df_laps = df_laps.merge(
        df_pits,
        on=["driver_number", "meeting_key", "session_key", "lap_number"],
        how="left",
    )
    df_laps = df_laps.merge(
        df_drivers, on=["driver_number", "meeting_key", "session_key"], how="inner"
    )
    df_laps = df_laps.merge(df_meeting, on=["meeting_key"], how="inner")
    df_laps["session_name"] = session_name
    df_laps.dropna(subset=["lap_duration"], inplace=True)
    log.info("Data fetching complete, waiting for next fetch attempt!")
    return df_laps


def visualize_data(placeholder) -> None:
    df = get_data(
        f1=f1,
        session_key=session.json()[0]["session_key"],
        df_drivers=df_drivers,
        df_meeting=df_meeting,
        session_name=SESSION_NAME,
    )

    if not df.empty:
        df["team_colour"] = df["team_colour"].apply(
            lambda x: "#" + x if x and not x.startswith("#") else x
        )
        race_title = f"{df.iloc[0].meeting_name} - {df.iloc[0].session_name}"

        st.title(f"Real-Time F1 Lap Times: {race_title}")

        df, smooth_pit_laps = apply_filters(df)
        df, last_lap_df, min_laptime, max_laptime, team_avg_lap, fastest_team = (
            calculate_fields(df, smooth_pit_laps)
        )
        create_visualization(
            df, last_lap_df, min_laptime, max_laptime, team_avg_lap, fastest_team
        )
    else:
        st.error("Unable to fetch data 😭")


fetched_session = fetch_session(f1)

if isinstance(fetched_session, tuple):
    current_meeting, drivers, session = fetched_session
    df_drivers = pd.DataFrame(drivers.json())
    df_meeting = pd.DataFrame(current_meeting.json())

    # Use st.empty to create a container that will be refreshed
    placeholder = st.empty()
    date_end_t10 = pendulum.parse(session.json()[0]["date_end"]).add(minutes=10)

    while True:
        visualize_data(placeholder)
        now = pendulum.now("utc")
        if now >= date_end_t10:
            break
        time.sleep(30)
else:
    st.error(fetched_session)

# Final visualization to retain visuals after loop
# visualize_data(st.empty())
