-- build_features.sql
-- Aggregates ALL match-level rows into one row per player.
-- Result saved to: raw.player_features

DROP TABLE IF EXISTS raw.player_features;

CREATE TABLE raw.player_features AS
SELECT
    player_id,
    COUNT(*)                                    AS matches_played,
    ROUND(AVG(kills)::NUMERIC, 2)               AS avg_kills,
    ROUND(AVG(deaths)::NUMERIC, 2)              AS avg_deaths,
    ROUND(
        AVG(kills)::NUMERIC /
        NULLIF(AVG(deaths)::NUMERIC, 0)
    , 4)                                        AS kd_ratio,
    ROUND(AVG(accuracy)::NUMERIC, 4)            AS avg_accuracy,
    ROUND(AVG(headshot_rate)::NUMERIC, 4)       AS avg_headshot_rate,
    ROUND(AVG(avg_reaction_time_ms)::NUMERIC, 2) AS avg_reaction_time_ms,
    ROUND(AVG(damage_dealt)::NUMERIC, 2)        AS avg_damage_dealt,
    MAX(is_cheater::INT)                        AS cheater_flag
FROM raw.match_events
GROUP BY player_id;

-- Index for fast lookup and ordering
CREATE INDEX idx_player_features_player  ON raw.player_features (player_id);
CREATE INDEX idx_player_features_cheater ON raw.player_features (cheater_flag);
