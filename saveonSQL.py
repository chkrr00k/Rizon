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
		
def addGame(db, duration, winner):
	ID = _getIDnumber(db)
	try:
		c = db.cursor()
		c.execute("INSERT INTO GAME(WINNER, DURATION, ID) VALUE('" + winner + "'," + str(duration) + "," + str(ID) + ")")
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
	

def saveScores(players, winner, score, time):
	db = MySQLdb.connect(host="localhost", user="root", passwd="caldazzo", db="TEST")
	for player in players:
		if not checkExisitingPlayer(db, player):
			insertNewPlayer(db, player)
	id = addGame(db, 12, winner)
	addPlayersToGame(db, players, 12, id)

players = ["Alguem", "chkrr00k", "Audi"]
saveScores(players, "Alguem", 1, 1)

