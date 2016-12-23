import MySQLdb

#Check if there is a record with the name of the player. If it's found then the tuple tmp is len > 0 and therefore return True else False
def checkExisitingPlayer(db, player):
	c = db.cursor()
	c.execute("SELECT * FROM PLAYERS WHERE PLAYERS.NAME = '" + player + "'")
	tmp = c.fetchall()
	return (len(tmp)) != 0

#Insert a nwe player in the PLAYER table. Incase of error do a roll back
#TODO rethrow exception with "raise IOError"
def insertNewPlayer(db, player):
	c = db.cursor()
	try:
		c.execute("INSERT INTO PLAYERS(NAME) VALUE('" + player + "')")
		db.commit()
	except Exception as e:
		print e
		db.rollback()

#Add a new game in the the GAME table, the table contains all the winned game and some infos like score per play
#Returns the new ID of the current game, None if error
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

#return the new number for the play
#NEEDS SOME CHECK FOR MULTITHREADING INCOMPATIBLILITY LIKE MULTIPLE REQUESTS. MAYBE IT'S GOOD TO SINGLETON THIS LIB
def _getIDnumber(db):
	c = db.cursor()
	c.execute("SELECT MAX(GAME.ID) FROM GAME")
	tmp = c.fetchone()
	if tmp[0] is not None:
		return tmp[0] + 1
	else:
		return 0

#Add a new player for a game in the table RELATION, the table contains all info about one play. Needs the ID of the current game gaved by the addGame() function
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

#the function that needs to be implemented in the monolithic file in order to replace the old one, Use current user, password, and database
#IT COULD EVEN WORKS, BUT NEEDS SOME TESTING
def saveScores(players, winner, score, time):
	db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="TEST")
	for player in players:
		if not checkExisitingPlayer(db, player):
			insertNewPlayer(db, player)
    
#	updatePlayerScore(db, winner, score)
	id = addGame(db, 12, winner, score)
	addPlayersToGame(db, players, 12, id)

#SQL QUERIES PART
# ALL FUNCTIONS RETURNS TUPLE OR TUPLE OF TUPLES, NEEDS EXTRACTION WITH [] OPERATOR OF SINGLE ARGUMENTS. Void tuple if no selected, functions don't check that.

#Returns all score for players. In DESC order. so just result[n] to check the first n. Be carefull if n > len(result). Use [] operator to access the intern of tuple
#Tuples order [n] the nth player
#Player's tuple order [0] name of the player, [1] score
def getAllScores(db):
	c = db.cursor()
	c.execute("SELECT G.WINNER, SUM(G.SCORE) AS TOTALSCORE FROM GAME G GROUP BY G.WINNER ORDER BY TOTALSCORE DESC")
	tmp = c.fetchall()
	return tmp

#Returns score for one player. Use [] operator to access the intern of tuple
#Tuple order [0] name of the player, [1] score
def getPlayerScore(db, player):
	c = db.cursor()
	c.execute("SELECT G.WINNER, SUM(G.SCORE) AS TOTALSCORE FROM GAME G GROUP BY G.WINNER HAVING G.WINNER = '" + player + "'")
	tmp = c.fetchall()
	return tmp

#Returns the number of played games.  Use [] operator to access the intern of tuple
#Tuple order [0] player's name, [1] played
def getPlayedPerPlayer(db, player):
	c = db.cursor()
	c.execute("SELECT R.PLAYER, COUNT(*) FROM RELATION R GROUP BY R.PLAYER HAVING R.PLAYER = '" + player + "'")
	tmp = c.fetchone()
	return tmp

#Returns the number of played games.  Use [] operator to access the intern of tuple
#Tuple order [0] player's name, [1] winned
def getWinnedPerPlayer(db, player):
	c = db.cursor()
	c.execute("SELECT G.WINNER, COUNT(*) FROM GAME G GROUP BY G.WINNER HAVING G.WINNER = '" + player + "'")
	tmp = c.fetchone()
	return tmp

#Returns all score for players with percentual of winned. In DESC order. So just result[n] to check the first n. Be carefull if n > len(result). Use [] operator to access the intern of tuple.
#This could be CPU-heavy in some low level hardware, so use the getAllScore() one if you don't need ratio.
#The tuple order is [0] player's name, [1] how much winner, [2] how much played, [3] winned ratio in percentual (Could needs cast to float)
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

#Use this to pass the db object to functions
db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="TEST")
print getAllScoresPercentual(db)
