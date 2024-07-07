import sys
import logging
from time import sleep

import pandas as pd
import pendulum

from calls.openf1 import OpenF1Connector

SESSION_NAME = "Race"

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s %(name)s: %(levelname)-4s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def get_laps_df(
    session_key: int,
    date_end: str,
    f1: OpenF1Connector,
    drivers: pd.DataFrame,
    meeting: pd.DataFrame,
    session_name: str,
) -> None:
    now = pendulum.now("utc")
    date_end_t10 = pendulum.parse(date_end).add(minutes=10)
    while now <= date_end_t10:
        log.info("Fetching laps at %s...", now.to_iso8601_string())
        laps = f1.get_laps(session_key=session_key)
        pits = f1.get_pits(session_key=session_key)
        df_pits = pd.DataFrame(pits.json())
        df = pd.DataFrame(laps.json())
        df = df.merge(
            df_pits,
            on=["driver_number", "meeting_key", "session_key", "lap_number"],
            how="left",
        )
        df = df.merge(
            drivers, on=["driver_number", "meeting_key", "session_key"], how="inner"
        )
        df = df.merge(meeting, on=["meeting_key"], how="inner")
        df["session_name"] = session_name
        log.info("Storing lap times in csv file...")
        df.to_csv("lap_times.csv", index=False)
        log.info("Storing complete, waiting for next fetch attempt!")
        sleep(30)
        now = pendulum.now("utc")


f1 = OpenF1Connector()
current_meeting = f1.get_meetings()
df_meeting = pd.DataFrame(current_meeting.json())[["meeting_key", "meeting_name"]]
drivers = f1.get_drivers(current_meeting.json()[0]["meeting_key"])
df_drivers = pd.DataFrame(drivers.json())
# print(current_meeting.json())
current_session = f1.get_sessions(
    current_meeting.json()[0]["meeting_key"], session_name=SESSION_NAME
)
get_laps_df(
    session_key=current_session.json()[0]["session_key"],
    date_end=current_session.json()[0]["date_end"],
    f1=f1,
    drivers=df_drivers,
    meeting=df_meeting,
    session_name=SESSION_NAME,
)
