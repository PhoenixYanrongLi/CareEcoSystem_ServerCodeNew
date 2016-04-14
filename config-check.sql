SET @room_0='[Bedroom]';
SET @room_1='[Bathroom]';
SET @room_2='[Kitchen]';

SELECT START INTO @t_0 FROM `_julien.jacquemot`.profile;
SELECT MIN(timestamp) INTO @t_1 FROM `_julien.jacquemot`.configMMGT WHERE current_room=@room_1 AND timestamp>=@t_0;
SELECT MIN(timestamp), MAX(timestamp) INTO @t_0, @t_1 FROM `_julien.jacquemot`.configMMGT WHERE current_room=@room_0 AND timestamp BETWEEN @t_0 AND @t_1;
SELECT count(*) AS n_entries, AVG(t1.value_0) AS room_0, AVG(t1.value_1) AS room_1, AVG(t1.value_2) AS room_2 FROM `_julien.jacquemot`.dataHMRSSI AS t1 WHERE t1.timestamp BETWEEN @t_0 AND @t_1;

SET @t_0 := @t_1;
SELECT MIN(timestamp) INTO @t_1 FROM `_julien.jacquemot`.configMMGT WHERE current_room=@room_2 AND timestamp>=@t_0;
SELECT MIN(timestamp), MAX(timestamp) INTO @t_0, @t_1 FROM `_julien.jacquemot`.configMMGT WHERE current_room=@room_1 AND timestamp BETWEEN @t_0 AND @t_1;
SELECT count(*) AS n_entries, AVG(t1.value_0) AS room_0, AVG(t1.value_1) AS room_1, AVG(t1.value_2) AS room_2 FROM `_julien.jacquemot`.dataHMRSSI AS t1 WHERE t1.timestamp BETWEEN @t_0 AND @t_1;

SET @t_0 := @t_1;
SELECT MIN(timestamp) INTO @t_1 FROM `_julien.jacquemot`.configMMGT WHERE current_room=@room_0 AND timestamp>=@t_0;
SELECT MIN(timestamp), MAX(timestamp) INTO @t_0, @t_1 FROM `_julien.jacquemot`.configMMGT WHERE current_room=@room_2 AND timestamp BETWEEN @t_0 AND @t_1;
SELECT count(*) AS n_entries, AVG(t1.value_0) AS room_0, AVG(t1.value_1) AS room_1, AVG(t1.value_2) AS room_2 FROM `_julien.jacquemot`.dataHMRSSI AS t1 WHERE t1.timestamp BETWEEN @t_0 AND @t_1;
