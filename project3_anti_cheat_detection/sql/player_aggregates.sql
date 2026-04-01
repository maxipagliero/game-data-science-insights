-- player_aggregates.sql
-- Aggregates each player's LAST 10 matches (by match_date) into one row.
-- Adds stddev_accuracy and stddev_reaction_time_ms as consistency signals.
-- Result saved to: raw.player_features_last10

DROP TABLE IF EXISTS raw.player_features_last10;

CREATE TABLE raw.player_features_last10 AS
WITH ranked AS (
    -- Rank each match per player newest-first
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY player_id
            ORDER BY match_date DESC, match_id  -- match_id breaks ties deterministically
        ) AS rn
    FROM raw.match_events
),
last10 AS (
    SELECT * FROM ranked WHERE rn <= 10
)
SELECT
    player_id,
    COUNT(*)                                        AS matches_played,
    ROUND(AVG(kills)::NUMERIC, 2)                   AS avg_kills,
    ROUND(AVG(deaths)::NUMERIC, 2)                  AS avg_deaths,
    ROUND(
        AVG(kills)::NUMERIC /
        NULLIF(AVG(deaths)::NUMERIC, 0)
    , 4)                                            AS kd_ratio,
    ROUND(AVG(accuracy)::NUMERIC, 4)                AS avg_accuracy,
    ROUND(STDDEV(accuracy)::NUMERIC, 6)             AS stddev_accuracy,
    ROUND(AVG(headshot_rate)::NUMERIC, 4)           AS avg_headshot_rate,
    ROUND(AVG(avg_reaction_time_ms)::NUMERIC, 2)    AS avg_reaction_time_ms,
    ROUND(STDDEV(avg_reaction_time_ms)::NUMERIC, 4) AS stddev_reaction_time_ms,
    ROUND(AVG(damage_dealt)::NUMERIC, 2)            AS avg_damage_dealt,
    MAX(is_cheater::INT)                            AS cheater_flag
FROM last10
GROUP BY player_id;

-- Indexes for suspicious-player lookups
CREATE INDEX idx_pf10_player  ON raw.player_features_last10 (player_id);
CREATE INDEX idx_pf10_cheater ON raw.player_features_last10 (cheater_flag);
