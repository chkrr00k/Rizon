import MySQLdb
	
def checkExisitingPlayer(db, player):
	c = db.cursor()
	c.execute("SELECT * FROM PLAYERS WHERE PLAYERS.NAME = '" + player + "'")
	tmp = c.fetchall()
	return (len(tmp)) != 0

def insertNewPlayer(db, player):
	c = db.cursor()
	try:
		c.execute("INSERT INTO PLAYERS(NAME) VALUE('" + player + "')")
		db.commit()
	except Exception as e:
		print e
		db.rollback()
		
def addGame(db, duration, winner, score):
	ID = _getIDnumber(db)
	try:
		c = db.cursor()
		c.execute("INSERT INTO GAME(WINNER, DURATION, ID, SCORE) VALUE('" + winner + "'," + str(duration) + "," + str(ID) + ","+ str(score) +")")
		db.commit()
		return ID
	except Exception as e:
		db.rollback()
		print e
		return None

def _getIDnumber(db):
	c = db.cursor()
	c.execute("SELECT MAX(GAME.ID) FROM GAME")
	tmp = c.fetchone()
	if tmp[0] is not None:
		return tmp[0] + 1
	else:
		return 0

def addPlayersToGame(db, players, duration, ID):
	for player in players:
		try:
			c = db.cursor()
			c.execute("INSERT INTO RELATION(PLAYER, DURATION, ID) VALUE('" + player + "'," + str(duration) + "," + str(ID) + ")")
			db.commit()
		except Exception as e:
			db.rollback()
			print e

#def updatePlayerScore(db, player, score):
#        try:
#                c = db.cursor()
#                c.execute("UPDATE PLAYERS SET SCORE = " + str(score) + " WHERE NAME = '" + player + "'")
#                db.commit()
#        except Exception as e:
#                db.rollback()
#                print e
#                print "here"        

def saveScores(players, winner, score, time):
	db = MySQLdb.connect(host="localhost", user="root", passwd="caldazzo", db="TEST")
	for player in players:
		if not checkExisitingPlayer(db, player):
			insertNewPlayer(db, player)
    
#	updatePlayerScore(db, winner, score)
	id = addGame(db, 12, winner, score)
	addPlayersToGame(db, players, 12, id)

def getAllScores(db):
	c = db.cursor()
	c.execute("SELECT G.WINNER, SUM(G.SCORE) AS TOTALSCORE FROM GAME G GROUP BY G.WINNER ORDER BY TOTALSCORE DESC")
	tmp = c.fetchall()
	return tmp
	
def getPlayerScore(db, player):
	c = db.cursor()
	c.execute("SELECT G.WINNER, SUM(G.SCORE) AS TOTALSCORE FROM GAME G GROUP BY G.WINNER HAVING G.WINNER = '" + player + "'")
	tmp = c.fetchall()
	return tmp
	
def getPlayedPerPlayer(db, player):
	c = db.cursor()
	c.execute("SELECT R.PLAYER, COUNT(*) FROM RELATION R GROUP BY R.PLAYER HAVING R.PLAYER = '" + player + "'")
	tmp = c.fetchone()
	return tmp
	
def getWinnedPerPlayer(db, player):
	c = db.cursor()
	c.execute("SELECT G.WINNER, COUNT(*) FROM GAME G GROUP BY G.WINNER HAVING G.WINNER = '" + player + "'")
	tmp = c.fetchone()
	return tmp
	
def getAllScoresPercentual(db):
	c = db.cursor()
	c.execute("""SELECT WINNED.WINNER, WINNED.WINNED, PLAYED.PLAYED, (WINNED.WINNED/PLAYED.PLAYED*100) AS RATIO
	FROM (
		SELECT G.WINNER, COUNT(*) AS WINNED
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
	""")
	tmp = c.fetchall()
	return tmp

#players = ["Alguem", "chkrr00k", "Audi"]
#saveScores(players, "Alguem", 3, 1)
#saveScores(players, "chkrr00k", 1, 2)
#saveScores(players, "Audi", 1, 1)

db = MySQLdb.connect(host="localhost", user="root", passwd="caldazzo", db="TEST")
print getAllScoresPercentual(db)
