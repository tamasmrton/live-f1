select distinct
    ds.dim_sessions_key,
    drw.year || ' - ' || drw.meeting_name as race_weekend,
    ds.date_start as race_start_date
from
    warehouse.modeling.dim_sessions ds
inner join warehouse.modeling.dim_race_weekends drw
on ds.dim_race_weekends_key = drw.dim_race_weekends_key
where ds.session_name = 'Race'
