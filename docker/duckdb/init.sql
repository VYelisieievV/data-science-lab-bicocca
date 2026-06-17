-- Rebuild the local DuckDB database from the raw V-Dem and V-Party CSV files.
-- This keeps the database reproducible and avoids committing generated data.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS meta;

SET preserve_insertion_order = false;
SET threads = 1;

DROP TABLE IF EXISTS raw.vdem_country_year;
CREATE TABLE raw.vdem_country_year AS
SELECT *
FROM read_csv(
    '/data/raw/V-Dem/V-Dem-CY-Full+Others-v16.csv',
    header = true,
    auto_detect = true,
    sample_size = 20480
);

DROP TABLE IF EXISTS raw.vparty_country_party_date;
CREATE TABLE raw.vparty_country_party_date AS
SELECT *
FROM read_csv(
    '/data/raw/V-Party/V-Dem-CPD-Party-V2.csv',
    header = true,
    auto_detect = true,
    sample_size = 20480
);

CREATE OR REPLACE VIEW meta.import_summary AS
SELECT
    'raw.vdem_country_year' AS table_name,
    COUNT(*) AS row_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    COUNT(DISTINCT country_id) AS country_count
FROM raw.vdem_country_year
UNION ALL
SELECT
    'raw.vparty_country_party_date' AS table_name,
    COUNT(*) AS row_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    COUNT(DISTINCT country_id) AS country_count
FROM raw.vparty_country_party_date;

CREATE OR REPLACE VIEW meta.analysis_window AS
SELECT
    GREATEST(
        (SELECT MIN(year) FROM raw.vdem_country_year),
        (SELECT MIN(year) FROM raw.vparty_country_party_date)
    ) AS min_year,
    LEAST(
        (SELECT MAX(year) FROM raw.vdem_country_year),
        (SELECT MAX(year) FROM raw.vparty_country_party_date)
    ) AS max_year;
