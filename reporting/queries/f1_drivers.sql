select distinct
    l.team_name,
    l.first_name || ' ' || l.last_name as driver_full_name,
from
    reporting.rpt_laps as l
where
    l.dim_sessions_key = ?
