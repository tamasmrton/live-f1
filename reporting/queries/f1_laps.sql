with avg_lap as (
    select
        dim_sessions_key,
        name_acronym,
        team_name,
        avg(lap_duration) as avg_lap_duration
    from
        warehouse.reporting.rpt_laps
    group by
        dim_sessions_key,
        name_acronym,
        team_name
),
ranked_lap as (
    select
        dim_sessions_key,
        name_acronym,
        team_name,
        avg_lap_duration,
        rank() over (
            partition by dim_sessions_key, team_name
            order by
                avg_lap_duration
        ) as driver_rank
    from
        avg_lap
)
select
    l.dim_sessions_key,
    l.meeting_name,
    l.session_name,
    l.name_acronym,
    l.team_name,
    l.first_name || ' ' || l.last_name as driver_full_name,
    l.lap_number,
    l.lap_duration,
    l.lap_duration_smoothened,
    avg_lap_duration,
    l.is_pit_in_lap,
    l.is_pit_out_lap,
    l.pit_duration,
    r.driver_rank,
    case
        when r.driver_rank = 1 then 'solid'
        else 'dotted'
    end as line_type,
    l.team_colour
from
    warehouse.reporting.rpt_laps l
inner join ranked_lap r on l.name_acronym = r.name_acronym and l.dim_sessions_key = r.dim_sessions_key
where l.dim_sessions_key = ?
