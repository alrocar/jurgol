with teams as
(SELECT the_geom, id, name FROM teams),
lines as
(SELECT cartodb_id, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los, ST_Segmentize(ST_MakeLine(st_centroid((SELECT the_geom FROM teams WHERE id = win)), st_centroid((SELECT the_geom FROM teams WHERE id = los)))::geography, 100000)::geometry as the_geom
    FROM matches order by date asc),
tosplit AS (
  SELECT * FROM lines
  WHERE ST_XMax(the_geom) - ST_XMin(the_geom) > 180
),
nosplit AS (
  SELECT * FROM lines
  WHERE ST_XMax(the_geom) - ST_XMin(the_geom) <= 180
),
split AS (
  SELECT
    cartodb_id, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los,
    ST_Difference(ST_Shift_Longitude(the_geom),
                  ST_Buffer(ST_GeomFromText('LINESTRING(180 90, 180 -90)',4326),
                            0.00001)) AS the_geom
  FROM tosplit order by date asc
),
final AS (
  SELECT * FROM split
  UNION ALL
  SELECT * FROM nosplit
)
INSERT INTO matches_lines (cartodb_id, the_geom, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los) SELECT row_number() over() as cartodb_id, the_geom, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los from final order by date asc