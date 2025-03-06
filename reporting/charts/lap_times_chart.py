import pandas as pd
import altair as alt
import streamlit as st


def create_lap_times_chart(
    df: pd.DataFrame, last_lap_df: pd.DataFrame, min_laptime: float, max_laptime: float
) -> alt.Chart:
    line_chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("lap_number:O", title="Lap Number", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(
                "lap_duration_selected:Q",
                scale=alt.Scale(domain=[min_laptime, max_laptime]),
                title="Lap Time (s)",
            ),
            color=alt.Color("team_colour").scale(None),
            detail="name_acronym",
            strokeDash=alt.StrokeDash(
                "line_type:N", sort=["solid", "dashed"], legend=None
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
            y="lap_duration_selected",
            text="name_acronym",
            color=alt.Color("team_colour:N").scale(
                None
            ),  # Use 'team_colour' for the text color
            tooltip=[
                alt.Tooltip("name_acronym", title="Driver"),
                alt.Tooltip("lap_number", title="Lap #"),
                alt.Tooltip("avg_lap_duration_str", title="Avg. lap time (m:ss.sss)"),
            ],
        )
    )
    # Adding vertical lines to signify pit out laps
    pit_labels = (
        alt.Chart(df[df["is_pit_out_lap"]])
        .mark_text(dy=-20, size=12, color="black", fontWeight="bold")
        .encode(
            x=alt.X("lap_number:O", title="Lap Number"),
            y=alt.Y("lap_duration_selected:Q", title="Lap Time (s)"),
            tooltip=[
                alt.Tooltip("name_acronym", title="Driver"),
                alt.Tooltip("lap_number", title="Lap #"),
                alt.Tooltip("pit_duration", title="Pit stop duration (s)"),
            ],
            text=alt.value("Pit stop"),
        )
    )
    # Points for pit out laps
    pit_points = (
        alt.Chart(df[df["is_pit_out_lap"]])
        .mark_point(color="black")  # Customize marker color and size
        .encode(
            x="lap_number:O",
            y="lap_duration_selected:Q",
            size=alt.Size("point_size:Q", legend=None),
            tooltip=[
                alt.Tooltip("name_acronym", title="Driver"),
                alt.Tooltip("lap_number", title="Lap #"),
                alt.Tooltip("pit_duration", title="Pit stop duration (s)"),
            ],
        )
    )
    combined_chart = line_chart + text_labels + pit_points + pit_labels
    st.markdown("### Lap times")
    st.altair_chart(combined_chart, use_container_width=True)
