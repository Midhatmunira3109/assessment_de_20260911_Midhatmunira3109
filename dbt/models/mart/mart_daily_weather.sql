/*
  mart_daily_weather.sql
  ──────────────────────
  Mart model: business-facing daily weather summary.

  Adds value over the staging layer by:
  - Computing a temperature range per day.
  - Computing a 7-day rolling average precipitation (centred on weather_date).
  - Classifying days as rainy / dry / trace for easy filtering.
  - Surfacing a human-readable "feels" label based on temp_max_c.

  Materialisation: table (so queries are fast for consumers / BI tools).
*/

with staged as (

    select * from {{ ref('stg_weather_raw') }}

),

enriched as (

    select
        weather_id,
        city,
        weather_date,
        latitude,
        longitude,

        -- temperature metrics
        temp_max_c,
        temp_min_c,
        round(temp_max_c - temp_min_c, 2)                           as temp_range_c,
        round((temp_max_c + temp_min_c) / 2.0, 2)                   as temp_avg_c,

        -- precipitation metrics
        precipitation_mm,
        round(
            avg(precipitation_mm) over (
                partition by city
                order by weather_date
                rows between 6 preceding and current row
            ),
            2
        )                                                            as precip_7d_rolling_avg_mm,

        -- classification labels
        case
            when precipitation_mm > 5  then 'rainy'
            when precipitation_mm > 0  then 'trace'
            else                            'dry'
        end                                                          as precipitation_class,

        case
            when temp_max_c >= 35 then 'Very Hot'
            when temp_max_c >= 25 then 'Hot'
            when temp_max_c >= 15 then 'Mild'
            when temp_max_c >= 5  then 'Cool'
            else                       'Cold'
        end                                                          as temperature_label,

        windspeed_max_kmh,
        loaded_at

    from staged

)

select * from enriched
order by city, weather_date
