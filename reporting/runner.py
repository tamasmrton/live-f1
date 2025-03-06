from dataclasses import dataclass
import logging

import pandas as pd
import streamlit as st

from reporting.charts.fastest_team_chart import create_fastest_team_chart
from reporting.charts.lap_times_chart import create_lap_times_chart
from reporting.connection import MotherDuckConnection
from reporting.query_registry import QueryRegistry

log = logging.getLogger(__name__)


@dataclass
class ReportingRunner:
    query_registry: QueryRegistry
    connection: MotherDuckConnection

    def _get_race_weekends(self) -> pd.DataFrame:
        """Fetch and return race weekend data."""
        query_name = "f1_race_weekends"
        log.info(f"Executing query `{query_name}`...")
        query = self.query_registry.get_query(query_name=query_name)
        df = self.connection.execute_query(query)
        return df

    def _get_lap_data(self, sessions_key: int) -> pd.DataFrame:
        """Fetch and return lap data for a specific session."""
        query_name = "f1_laps"
        log.info(f"Executing query `{query_name}`...")
        query = self.query_registry.get_query(query_name=query_name)
        df = self.connection.execute_query(query, params=[sessions_key])
        return df

    def _get_drivers(self, sessions_key: int) -> pd.DataFrame:
        """Fetch and return drivers for a specific session."""
        query_name = "f1_drivers"
        log.info(f"Executing query `{query_name}`...")
        query = self.query_registry.get_query(query_name=query_name)
        df = self.connection.execute_query(query, params=[sessions_key])
        return df

    def _select_race(self) -> pd.DataFrame:
        """Handle race selection UI and return selected race data."""

        @st.cache_data
        def get_cached_race_weekends() -> pd.DataFrame:
            return self._get_race_weekends()

        race_weekend_df = get_cached_race_weekends()
        race_weekend_df.sort_values(by="race_start_date", ascending=False, inplace=True)

        with st.sidebar:
            race = st.selectbox(
                "**Select a race weekend**", race_weekend_df["race_weekend"]
            )
        return race_weekend_df[race_weekend_df["race_weekend"] == race]

    def _select_drivers_teams(
        self, drivers_df: pd.DataFrame
    ) -> tuple[list[str], list[str]]:
        """Handle driver and team selection UI and return selected filters."""

        col1, col2 = st.columns(2)
        with col1:
            teams_filter = st.multiselect(
                "Select the team(s)", pd.unique(drivers_df["team_name"].sort_values())
            )

        if teams_filter:
            drivers_df = drivers_df[drivers_df["team_name"].isin(teams_filter)]

        with col2:
            drivers_filter = st.multiselect(
                "Select the driver(s)",
                pd.unique(drivers_df["driver_full_name"].sort_values()),
            )

        return teams_filter, drivers_filter

    def _select_lap_range(self, laps_df: pd.DataFrame) -> tuple[int, int]:
        """Handle lap range selection UI and return selected lap range."""
        min_lap_number = laps_df["lap_number"].min()
        max_lap_number = laps_df["lap_number"].max()

        selected_lap_range = st.slider(
            "Select lap range",
            min_lap_number,
            max_lap_number,
            (min_lap_number, max_lap_number),
        )
        return selected_lap_range

    def _select_smoothed_pit_laps(self) -> str:
        """Handle smoothed lap duration selection UI and return selection."""
        smooth_pit_laps = st.checkbox("Smoothen pit in/out laps")
        if smooth_pit_laps:
            return "lap_duration_smoothened"
        return "lap_duration"

    def _process_lap_data(
        self, laps_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
        """Process lap data and return required dataframes and metrics."""
        laps_df["point_size"] = laps_df["pit_duration"] ** 3
        min_laptime = laps_df["lap_duration_selected"].min()
        max_laptime = laps_df["lap_duration_selected"].max()

        laps_df["lap_duration_str"] = laps_df["lap_duration"].apply(
            lambda x: f"{int(x // 60)}:{int(x % 60):02}.{int((x % 1) * 1000):03}"
        )
        laps_df["avg_lap_duration_str"] = laps_df["avg_lap_duration"].apply(
            lambda x: f"{int(x // 60)}:{int(x % 60):02}.{int((x % 1) * 1000):03}"
        )

        last_lap_df = laps_df.loc[
            laps_df.groupby("name_acronym")["lap_number"].idxmax()
        ]
        return laps_df, last_lap_df, min_laptime, max_laptime

    def _load_all_session_data(self, sessions_key: int) -> None:
        """Load and cache all session related data."""

        @st.cache_data
        def get_cached_lap_data(key: int) -> pd.DataFrame:
            return self._get_lap_data(sessions_key=key)

        @st.cache_data
        def get_cached_drivers(key: int) -> pd.DataFrame:
            return self._get_drivers(sessions_key=key)

        get_cached_lap_data.clear()
        get_cached_drivers.clear()

        if "base_lap_data" not in st.session_state:
            st.session_state.base_lap_data = get_cached_lap_data(sessions_key)

        if "drivers_data" not in st.session_state:
            st.session_state.drivers_data = get_cached_drivers(sessions_key)

    def _apply_filters(self) -> pd.DataFrame:
        """Apply filters to the base lap data and return filtered dataframe."""
        laps_df = st.session_state.base_lap_data.copy()
        drivers_df = st.session_state.drivers_data.copy()

        teams_filter, drivers_filter = self._select_drivers_teams(drivers_df=drivers_df)
        selected_lap_range = self._select_lap_range(laps_df=laps_df)
        lap_duration_column = self._select_smoothed_pit_laps()

        if teams_filter:
            laps_df = laps_df[laps_df["team_name"].isin(teams_filter)]
        if drivers_filter:
            laps_df = laps_df[laps_df["driver_full_name"].isin(drivers_filter)]

        laps_df = laps_df[
            laps_df["lap_number"].between(selected_lap_range[0], selected_lap_range[1])
        ]
        laps_df["lap_duration_selected"] = laps_df[lap_duration_column]

        return laps_df

    @st.fragment
    def _fragment_function(self, sessions_key: int) -> None:
        """Main fragment function to display visuals."""
        # Load data only once
        self._load_all_session_data(sessions_key)

        # Apply filters to the base data
        filtered_df = self._apply_filters()

        # Process and display
        laps_df, last_lap_df, min_laptime, max_laptime = self._process_lap_data(
            filtered_df
        )

        create_lap_times_chart(
            df=laps_df,
            last_lap_df=last_lap_df,
            min_laptime=min_laptime,
            max_laptime=max_laptime,
        )

        _, col_2 = st.columns(spec=[0.9, 0.1], gap="medium")
        with col_2:
            if st.button(label="Refresh Data", icon=":material/refresh:"):
                # Clear all session state data to force reload
                st.session_state.pop("base_lap_data", None)
                st.session_state.pop("drivers_data", None)
                # Reload the data
                self._load_all_session_data(sessions_key)

        create_fastest_team_chart(df=laps_df)

    def run(self) -> None:
        """Main execution flow."""
        st.set_page_config(
            page_title="F1 Lap Times",
            page_icon="🏎️",
            layout="wide",
        )

        # Get the previously selected race weekend from session state
        previous_race = st.session_state.get("selected_race_weekend", None)

        race_df = self._select_race()
        current_race = race_df.iloc[0].race_weekend
        sessions_key = race_df["dim_sessions_key"].values[0]

        # Check if race weekend changed
        if previous_race != current_race:
            # Clear session state and cached data
            st.session_state.pop("base_lap_data", None)
            st.session_state.pop("drivers_data", None)
            # Store new race weekend
            st.session_state.selected_race_weekend = current_race

        st.title(f"F1 Lap Times: {current_race}")

        self._fragment_function(sessions_key=sessions_key)
