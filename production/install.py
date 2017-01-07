import MySQLdb
### DATABASE SETTINGS
DB_PASSWORD = "unopass"
DB_HOST = "localhost"
DB_USER = "unobot"
DB_NAME = "TEST"

ROOT_DB_USER = "root"
ROOT_DB_PASS = "__insert_Password_Here__"

#Use this to db
#db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)

    
def install():
    db = MySQLdb.connect(host=DB_HOST, user=ROOT_DB_USER, passwd=ROOT_DB_PASSWORD)
    print "creating database " + DB_NAME
    createDatabase(db)
    print "creating user " + DB_USER
    createUser(db)
    print "granting user " + DB_USER
    grantPermissions(db)
    db.close()
    print "creating tables"
    db = MySQLdb.connect(host=DB_HOST, user=ROOT_DB_USER, passwd=ROOT_DB_PASSWORD, db=DB_NAME)
    createTables(db)
    db.close()
    print "success!"

def createDatabase(db):
    try:
        c = db.cursor()
        c.execute("CREATE DATABASE " + DB_NAME)
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error in creating database"
        print e

def createUser(db):
    try:
        c = db.cursor()
        c.execute("CREATE USER '" + DB_USER + "' IDENTIFIED BY '" + DB_PASSWORD + "'")
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error in creating user"
        print e

def grantPermissions(db):
    try:
        c = db.cursor()
        c.execute("GRANT SELECT ON "+ DB_NAME + ".* TO '" + DB_USER + "'")
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error while granting SELECT to user"
        print e
    try:
        c = db.cursor()
        c.execute("GRANT INSERT ON "+ DB_NAME + ".* TO '" + DB_USER + "'")
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error while granting INSERT to user"
        print e
        
def createTables():
    try:
        c = db.cursor()
        c.execute("""CREATE TABLE PLAYERS(NAME VARCHAR(200) NOT NULL PRIMARY KEY)""")
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error while creating table PLAYERS"
        print e
        return
    try:
        c = db.cursor()
        c.execute("""CREATE TABLE RELATION(
	PLAYER VARCHAR(200) NOT NULL REFERENCES PLAYERS,
	DURATION INT NOT NULL REFERENCES GAME.DURATION,
	ID INT NOT NULL REFERENCES GAME.ID,
	PRIMARY KEY (PLAYER, DURATION, ID))""")
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error while creating table RELATION"
        print e
        return
    try:
        c = db.cursor()
        c.execute("""CREATE TABLE GAME(
	WINNER VARCHAR(200) NOT NULL REFERENCES PLAYERS,
	DURATION INT NOT NULL,
	ID INT NOT NULL UNIQUE,
	SCORE INT NOT NULL,
	PRIMARY KEY (DURATION, ID))""")
        db.commit()
    except Exception as e:
        db.rollback()
        print "Error while creating table GAME"
        print e
        return

install()
    
