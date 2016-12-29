--DEFINE THIS TABLES IN THE DATABASE
CREATE TABLE PLAYERS(
	NAME VARCHAR(200) NOT NULL PRIMARY KEY
);

CREATE TABLE RELATION(
	PLAYER VARCHAR(200) NOT NULL REFERENCES PLAYERS,
	DURATION INT NOT NULL REFERENCES GAME.DURATION,
	ID INT NOT NULL REFERENCES GAME.ID,
	PRIMARY KEY (PLAYER, DURATION, ID)
);

CREATE TABLE GAME(
	WINNER VARCHAR(200) NOT NULL REFERENCES PLAYERS,
	DURATION INT NOT NULL,
	ID INT NOT NULL UNIQUE,
	SCORE INT NOT NULL,
	PRIMARY KEY (DURATION, ID)
);
--BEFORE TRIGGER TO CHECK IF A GAME.WINNER IS REFERENCED IN THE RELATION.PLAYER AT THE SAME ID (IE HE PARTICICPATED THAT GAME)
delimiter //
CREATE TRIGGER CONSISTENCY
BEFORE INSERT ON GAME
FOR EACH ROW
BEGIN
	IF (NOT EXISTS(SELECT * FROM RELATION R WHERE NEW.WINNER = R.PLAYER AND NEW.ID = R.ID)) THEN
	SIGNAL SQLSTATE '70000';
	END IF;
END;
//
delimiter ;


--SET SOME SECURITY ON THE DATABASE
--CONSIDER FORCING CONNECT FROM LOCALHOST OR GIVE SINGLE TABLE PERIMSSIONS
CREATE USER 'unobot' IDENTIFIED BY 'unopass';
GRANT SELECT ON TEST.* TO 'unobot';
GRANT INSERT ON TEST.* TO 'unobot';


--GET HIGHEST ID
SELECT MAX(G.ID)
FROM GAME G
;

--GET ONE PLAYER
SELECT *
FROM PLAYERS
WHERE PLAYERS.NAME = 'name'
;

--GET SCORE FOR PLAYER
SELECT PLAYERS.SCORE
FROM PLAYERS
WHERE PLAYERS.NAME = 'player'
;

--INSERT NEW PLAYER
INSERT INTO PLAYERS(NAME, SCORE) VALUE ('player', 00);

--INSERT NEW GAME
INSERT INTO GAME(WINNER, DURATION, ID) VALUE ('winner', 00, 0);

--INSERT NEW RELATION
INSERT INTO RELATION(PLAYER, DURATION, ID) VALUE ('player', 00, 0);

--QUERIES TO EXTRACT DATA

--GET ALL PLAYERS
SELECT *
FROM PLAYERS
;

--GET THE MAX NUMBER OF WINNED
SELECT G.WINNER
FROM GAME G
GROUP BY G.WINNER
HAVING COUNT(*) >= ALL (
	SELECT COUNT(*)
	FROM GAME G1
	GROUP BY G1.WINNER
);

--GET THE NUMBER OF WINNED PER USER
SELECT G.WINNER, COUNT(*) AS WINNED
FROM GAME G
GROUP BY G.WINNER
ORDER BY WINNED DESC
;

--GET THE NUMBER OF WINNED PER ONE USER
SELECT G.WINNER, COUNT(*) AS WINNED
FROM GAME G
GROUP BY G.WINNER
HAVING G.WINNER = 'name'
;
	
--GET THE NUMBER OF PLAYED PER USER
SELECT R.PLAYER, COUNT(*) AS PLAYED
FROM RELATION R
GROUP BY R.PLAYER
ORDER BY PLAYED DESC
;

--GET THE NUMBER OF PLAYED PER USER
SELECT R.PLAYER, COUNT(*) AS PLAYED
FROM RELATION R
GROUP BY R.PLAYER
HAVING R.PLAYER = 'name'
;

--GET THE SCORE OF PLAYERS
SELECT G.WINNER, SUM(G.SCORE) AS TOTALSCORE
FROM GAME G
GROUP BY G.WINNER
ORDER BY TOTALSCORE DESC
;

--GET THE SCORE OF ONE PLAYER
SELECT G.WINNER, SUM(G.SCORE) AS TOTALSCORE
FROM GAME G
GROUP BY G.WINNER
HAVING G.WINNER = 'name'
;

--GET THE TOTAL PLAYED TIME
SELECT R.PLAYER, SUM(R.DURATION) AS TOTALTIME
FROM RELATION R
GROUP BY R.PLAYER
;

--GET STATS FOR ALL PLAYERS
SELECT WINNED.WINNER, WINNED.WINNED, PLAYED.PLAYED,(WINNED.SCORE/PLAYED.PLAYED) AS POINT_PER_GAME, (WINNED.WINNED/PLAYED.PLAYED*100) AS RATIO
FROM (
	SELECT G.WINNER, SUM(G.SCORE) AS SCORE, COUNT(*) AS WINNED
	FROM GAME G
	GROUP BY G.WINNER
)AS WINNED,
(
	SELECT R.PLAYER, COUNT(*) AS PLAYED
	FROM RELATION R
	GROUP BY R.PLAYER
)AS PLAYED
WHERE WINNED.WINNER = PLAYED.PLAYER
ORDER BY RATIO DESC
;

