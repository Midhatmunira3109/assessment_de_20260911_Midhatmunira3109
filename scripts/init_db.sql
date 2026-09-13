-- Creates the pipeline user and weather DB on first container start
-- Airflow DB is created by POSTGRES_DB env var; this script adds the weather DB.

CREATE USER weather_user WITH PASSWORD 'weather_pass';
CREATE DATABASE weather OWNER weather_user;
\connect weather
CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION weather_user;
GRANT ALL PRIVILEGES ON SCHEMA raw TO weather_user;

CREATE TABLE IF NOT EXISTS raw.weather_daily (
    city                TEXT        NOT NULL,
    date                DATE        NOT NULL,
    temp_max_c          NUMERIC(6,2),
    temp_min_c          NUMERIC(6,2),
    precipitation_mm    NUMERIC(8,2),
    windspeed_max_kmh   NUMERIC(8,2),
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (city, date)
);
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO weather_user;

