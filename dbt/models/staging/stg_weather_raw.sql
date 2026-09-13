/*
  stg_weather_raw.sql
  ────────────────────
  Staging model: a thin cleaning layer over raw.weather_daily.

  Responsibilities:
  - Cast types explicitly so downstream models can rely on them.
  - Rename columns to a consistent snake_case convention.
  - Add a surrogate key for easy joining.
  - No business logic here — that lives in the mart.

  Materialisation: view (cheap, always fresh)
*/

with source as (

    select * from {{ source('raw', 'weather_daily') }}

),

staged as (

    select
        -- surrogate key (city + date uniquely identifies a row)
        {{ dbt_utils.generate_surrogate_key(['city', 'date']) }} as weather_id,

        -- dimensions
        city::text                              as city,
        date::date                              as weather_date,
        latitude::numeric(9,6)                  as latitude,
        longitude::numeric(9,6)                 as longitude,

        -- measures (null-safe casts — source values can be null on missing days)
        temp_max_c::numeric(6,2)                as temp_max_c,
        temp_min_c::numeric(6,2)                as temp_min_c,
        precipitation_mm::numeric(8,2)          as precipitation_mm,
        windspeed_max_kmh::numeric(8,2)         as windspeed_max_kmh,

        -- metadata
        loaded_at::timestamptz                  as loaded_at

    from source

)

select * from staged
