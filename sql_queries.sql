CREATE TABLE PLAYERS(
	NAME VARCHAR(200) NOT NULL PRIMARY KEY,
	SCORE INT NOT NULL
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
	PRIMARY KEY (DURATION, ID)
);

--GET HIGHEST ID
SELECT MAX(GAME.ID)
FROM GAME G

--GET ONE PLAYER
SELECT *
FROM PLAYERS
WHERE PLAYERS.NAME = 'name'
;

--GET SCORE FOR PLAYER
SELECT PLAYERS.SCORE
FROM PLAYERS
WHERE PLAYERS.NAME = 'player'

--INSERT NEW PLAYER
INSERT INTO PLAYERS(NAME) VALUE ('player');

--INSERT NEW GAME
INSERT INTO GAME(WINNER, DURATION, ID) VALUE ('winner', 00, 0);

--INSERT NEW RELATION
INSERT INTO RELATION(PLAYER, DURATION, ID) VALUE ('player', 00, 0);
