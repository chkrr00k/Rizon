import random
from datetime import datetime, timedelta
import time
import MySQLdb

random.seed()

away_last = 0

BADMIN_CHAN = "#example" # Must be lowercase
SCOREFILE = "~/unobot/unoscores.txt"
INACTIVE_TIMEOUT = 3

### DATABASE SETTINGS
DB_PASSWORD = "unopass"
DB_HOST = "localhost"
DB_USER = "unobot"
DB_NAME = "TEST"

STRINGS = {
    'ALREADY_STARTED': '\x0FGame already started by \x02%s\x02! Type ".ujoin" to join!',
    'GAME_STARTED': '\x0FIRC-UNO started by \x02%s\x02 - Type ".ujoin" to join!',
    'GAME_STOPPED': '\x0FGame stopped.',
    'CANT_STOP': '\x0F\x02%s\x02 is the game owner, you can\'t stop it! To force stop the game, please wait \x02%s seconds\x02!',
    'DEALING_IN': '\x0FDealing \x02%s\x02 into the game as player \x02#%s\x02!',
    'JOINED': '\x0FDealing \x02%s\x02 into the game as player \x02#%s\x02!',
    'ENOUGH': '\x0FThere are enough players, type \x02.deal\x02 to start!',
    'NOT_STARTED': '\x0FGame not started, type \x02.uno\x02 to start!',
    'NOT_ENOUGH': '\x0FNot enough players to deal yet.',
    'NEEDS_TO_DEAL': '\x0F\x02%s\x02 needs to deal.',
    'ALREADY_DEALT': '\x0FAlready dealt.',
    'ON_TURN': '\x0FIt\'s \x02%s\'s\x02 turn.',
    'DONT_HAVE': '\x0FYou don\'t have that card or it doesn\'t play, \x02%s\x02!',
    'DOESNT_PLAY': '\x0FYou don\'t have that card or it doesn\'t play, \x02%s\x02!',
    'UNO': '\x0F\x0304UNO! \x02%s\x02 has ONE card left!\x03',
    'WIN': '\x0FWe have a winner! \x02%s\x02 beats \x02%d\x02 player(s) in a game that took \x02%s\x02 seconds!',
    'DRAWN_ALREADY': '\x0FYou\'ve already drawn, either \x02.pass\x02 or \x02.play\x02!',
    'DRAWS': '\x0F\x02%s\x02 draws a card',
    'DRAWN_CARD': '\x0FDrawn card: \x02%s\x02',
    'DRAW_FIRST': '\x0F\x02%s\x02, you need to draw first!',
    'PASSED': '\x0F\x02%s\x02 passed!',
    'NO_SCORES': '\x0FNo scores yet',
    'TOP_CARD': '\x0F\x02%s\'s\x02 turn. Top Card: \x02%s\x02',
    'YOUR_CARDS': '\x0FYour cards: \x02%s\x02',
    'NEXT_START': '\x0FNext: ',
    'NEXT_PLAYER': '\x0F\x02%s\x02 (\x02%s\x02 cards)',
    'D2': '\x0F\x02%s\x02 draws two and is skipped!',
    'CARDS': '\x0FCards: \x02%s\x02',
    'WD4': '\x0F\x02%s\x02 draws four and is skipped!',
    'SKIPPED': '\x0F\x02%s\x02 is skipped!',
    'REVERSED': '\x0FOrder reversed!',
    'GAINS': '\x0F\x02%s\x02 gains %s points!',
    'SCORE_ROW': '\x0F%s: \x02#%s %s\x02 (\x02%s\x02 points, \x02%s\x02 games, \x02%s\x02 won, \x02%.2f\x02 points per game, \x02%.2f\x02 percent wins)',
    'GAME_ALREADY_DEALT': 'Game has already been dealt, please wait until game is over or stopped.',
    'PLAYER_COLOR_ENABLED': '\x0FHand card colors \x02\x0309enabled\x03\x02! Format: <COLOR>/[<CARD>].  Example: R/[D2] is a red Draw Two.',
    'PLAYER_COLOR_DISABLED': '\x0FHand card colors \x02\x0304disabled\x03\x02!',
    'DISABLED_PCE': '\x0FHand card colors are \x02\x0304disabled\x03\x02 for \x02%s\x02. To enable, \x02.pce-on\x02',
    'ENABLED_PCE': '\x0FHand card colors are \x02\x0309enabled\x03\x02 for \x02%s\x02. To disable, \x02.pce-off\x02',
    'PCE_CLEARED': '\x0FAll players\' hand card colors settings are reset by \x02%s\x02.',
    'PLAYER_LEAVES': '\x0FPlayer \x02%s\x02 has left the game.',
    'OWNER_CHANGE': '\x0FOwner \x02%s\x02 has left the game. New owner is \x02%s\x02.',
}

# List of all Uno thread (or game). One for each channel (Not sure, could be one for each player(?))
unos = {}
# If an update is imminent (it's used to update the game when no one is playing)
update_imminent = False

# Notify the Admin (or the bot's owner) about all games has ended and update is possible
def onGameEnd(jenni):
    if update_imminent:
        for uno in unos.values():
            if not uno.dealt:
                jenni.msg(BADMIN_CHAN, "\x02\x0304Nick, all games have finished. You may now update.")


class UnoBot:
    def __init__(self, channel):
    	# Name of the current channel
        self.CHANNEL = channel
        # Coloured cards number
        self.colored_card_nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'R', 'S', 'D2']
        # Special scores of cards
        self.special_scores = {'R' : 20, 'S' : 20, 'D2' : 20, 'W' : 50, 'WD4' : 50}
        # Colours name
        self.colors = 'RGBY'
        # Special cards name
        self.special_cards = ['W', 'WD4']
        # Players name (Dictionary)
        self.players = dict()
        # Owners name (Dictionary) TODO what is this?
        self.owners = dict()
        self.players_pce = dict()  # Player color enabled hash table
        # Players orders in the game
        self.playerOrder = list()
        # If game is started (Then it becomes owner (?))
        self.game_on = False
        # Number of the current player (it's used to extract the player's info on their turn)
        self.currentPlayer = 0
        # Current top card
        self.topCard = None
        # Probably the order in witch is played but i'm not sure TODO understan what is this
        self.way = 1
        # If the current player has drawn i guess (TODO?)
        self.drawn = False
        # Address of the saved file (TODO remove this)
        self.scoreFile = SCOREFILE
        # List of the current deck of cards
        self.deck = list()
        #Probably the current scores (TODO descover this)
        self.prescores = list()
        # If the owner has dealt
        self.dealt = False
        # Current time for duration(?) TODO understand what is this
        self.lastActive = datetime.now()
        # Whatever this is it's (minutes = 3) [TODO check what is timedelta]
        self.timeout = timedelta(minutes=INACTIVE_TIMEOUT)

	
    def start(self, jenni, owner):
        owner = owner
        if self.game_on:
            jenni.msg(self.CHANNEL, STRINGS['ALREADY_STARTED'] % self.game_on)
        else:
            self.lastActive = datetime.now()
	    self.dealt = False
            self.game_on = owner
            self.deck = list()
            jenni.msg(self.CHANNEL, STRINGS['GAME_STARTED'] % owner)
            self.players = dict()
            self.players[owner] = list()
            self.playerOrder = [owner]
            if self.players_pce.get(owner, 0):
                self.noticeUser(jenni, owner, STRINGS['ENABLED_PCE'] % owner)

    def stop(self, jenni, input):
        nickk = (input.nick)
        tmptime = datetime.now()
        if nickk == self.game_on or tmptime - self.lastActive > self.timeout:
            jenni.msg(self.CHANNEL, STRINGS['GAME_STOPPED'])
            self.game_on = False
            self.dealt = False
            onGameEnd(jenni)
        elif self.game_on:
            jenni.msg(self.CHANNEL, STRINGS['CANT_STOP'] % (self.game_on, self.timeout.seconds - (tmptime - self.lastActive).seconds))

    def join(self, jenni, input):
        #print dir(jenni.bot)
        #print dir(input)
        nickk = (input.nick)
        if self.game_on:
            if not self.dealt:
                if nickk not in self.players:
                    self.players[nickk] = list()
                    self.playerOrder.append(nickk)
                    self.lastActive = datetime.now()
                    if self.players_pce.get(nickk, 0):
                        self.noticeUser(jenni, nickk, STRINGS['ENABLED_PCE'] % nickk)
                    if self.deck:
                        for i in xrange(0, 7):
                            self.players[nickk].append(self.getCard())
                        jenni.msg(self.CHANNEL, STRINGS['DEALING_IN'] % (nickk, self.playerOrder.index(nickk) + 1))
                    else:
                        jenni.msg(self.CHANNEL, STRINGS['JOINED'] % (nickk, self.playerOrder.index(nickk) + 1))
                        if len (self.players) == 2:
                            jenni.msg(self.CHANNEL, STRINGS['ENOUGH'])
            else:
                jenni.msg(self.CHANNEL, STRINGS['GAME_ALREADY_DEALT'])
        else:
            jenni.msg(self.CHANNEL, STRINGS['NOT_STARTED'])

    def deal(self, jenni, input):
        nickk = (input.nick)
        if not self.game_on:
            jenni.msg(self.CHANNEL, STRINGS['NOT_STARTED'])
            return
        if len(self.players) < 2:
            jenni.msg(self.CHANNEL, STRINGS['NOT_ENOUGH'])
            return
        if nickk != self.game_on:
            jenni.msg(self.CHANNEL, STRINGS['NEEDS_TO_DEAL'] % self.game_on)
            return
        if len(self.deck):
            jenni.msg(self.CHANNEL, STRINGS['ALREADY_DEALT'])
            return
        self.startTime = datetime.now()
        self.lastActive = datetime.now()
        self.deck = self.createnewdeck()
        for i in xrange(0, 7):
            for p in self.players:
                self.players[p].append(self.getCard ())
        self.topCard = self.getCard()
        while self.topCard.lstrip(self.colors) in 'R S D2 W WD4':
            self.topCard = self.getCard()
        self.currentPlayer = 1
        self.cardPlayed(jenni, self.topCard)
        self.showOnTurn(jenni)
        self.dealt = True

    def play(self, jenni, input):
        nickk = (input.nick)
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            jenni.msg(self.CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        tok = [z.strip() for z in str(input).upper().split(' ')]
        if len(tok) != 3:
            return
        searchcard = str()
        if tok[1] in self.special_cards and tok[2] in self.colors:
            searchcard = tok[1]
        elif tok[1] in self.colors:
            searchcard = (tok[1] + tok[2])
        else:
            jenni.msg(self.CHANNEL, STRINGS['DOESNT_PLAY'] % self.playerOrder[self.currentPlayer])
            return
        if searchcard not in self.players[self.playerOrder[self.currentPlayer]]:
            jenni.msg(self.CHANNEL, STRINGS['DONT_HAVE'] % self.playerOrder[self.currentPlayer])
            return
        playcard = (tok[1] + tok[2])
        if not self.cardPlayable(playcard):
            jenni.msg(self.CHANNEL, STRINGS['DOESNT_PLAY'] % self.playerOrder[self.currentPlayer])
            return

        self.drawn = False
        self.players[self.playerOrder[self.currentPlayer]].remove(searchcard)

        pl = self.currentPlayer

        self.incPlayer()
        self.cardPlayed(jenni, playcard)

        if len(self.players[self.playerOrder[pl]]) == 1:
            jenni.msg(self.CHANNEL, STRINGS['UNO'] % self.playerOrder[pl])
        elif len(self.players[self.playerOrder[pl]]) == 0:
            jenni.msg(self.CHANNEL, STRINGS['WIN'] % (self.playerOrder[pl], (len(self.players) - 1), (datetime.now() - self.startTime)))
            self.gameEnded(jenni, self.playerOrder[pl])
            return

        self.lastActive = datetime.now()
        self.showOnTurn(jenni)

    def draw(self, jenni, input):
        nickk = (input.nick)
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            jenni.msg(self.CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if self.drawn:
            jenni.msg(self.CHANNEL, STRINGS['DRAWN_ALREADY'])
            return
        self.drawn = True
        jenni.msg(self.CHANNEL, STRINGS['DRAWS'] % self.playerOrder[self.currentPlayer])
        c = self.getCard()
        self.players[self.playerOrder[self.currentPlayer]].append(c)
        self.lastActive = datetime.now()
        self.noticeUser(jenni, nickk, STRINGS['DRAWN_CARD'] % self.renderCards (nickk, [c], 0))

    # this is not a typo, avoiding collision with Python's pass keyword
    def passs(self, jenni, input):
        nickk = (input.nick)
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            jenni.msg(self.CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if not self.drawn:
            jenni.msg(self.CHANNEL, STRINGS['DRAW_FIRST'] % self.playerOrder[self.currentPlayer])
            return
        self.drawn = False
        jenni.msg(self.CHANNEL, STRINGS['PASSED'] % self.playerOrder[self.currentPlayer])
        self.incPlayer()
        self.lastActive = datetime.now()
        self.showOnTurn(jenni)

	#TODO remove this method for the MySQL one
    def top10(self, jenni, input):
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
        nickk = (input.nick)
        lines = (format(getAllScoreForBestN(db, 10)))
        for line in lines:
                jenni.msg(nickk, str(line))
        db.close()

    def createnewdeck(self):
        ret = list()

        for i in range(2):
            for a in self.colored_card_nums:
                for b in self.colors:
                    if i > 0 and a == '0':
                        continue
                    ret.append(b + a)

        for a in self.special_cards:
            for i in range(4):
                ret.append(a)

        if len(self.playerOrder) > 4:
            ret *= 2

        random.shuffle(ret)

        return ret

    def getCard(self):
        ret = self.deck[0]
        self.deck.pop(0)
        if not self.deck:
            self.deck = self.createnewdeck()
        return ret

    def showOnTurn(self, jenni):
        jenni.msg(self.CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))
        self.noticeUser(jenni, self.playerOrder[self.currentPlayer], STRINGS['YOUR_CARDS'] % self.renderCards(self.playerOrder[self.currentPlayer], self.players[self.playerOrder[self.currentPlayer]], 0))
        msg = STRINGS['NEXT_START']
        tmp = self.currentPlayer + self.way
        if tmp == len(self.players):
            tmp = 0
        if tmp < 0:
            tmp = len(self.players) - 1
        arr = list()
        while tmp != self.currentPlayer:
            arr.append(STRINGS['NEXT_PLAYER'] % (self.playerOrder[tmp], len(self.players[self.playerOrder[tmp]])))
            tmp = tmp + self.way
            if tmp == len(self.players):
                tmp = 0
            if tmp < 0:
                tmp = len(self.players) - 1
        msg += ' - '.join(arr)
        self.noticeUser(jenni, self.playerOrder[self.currentPlayer], msg)

    def showCards(self, jenni, user):
        user = user
        if not self.game_on or not self.deck:
            return
        msg = STRINGS['NEXT_START']
        tmp = self.currentPlayer + self.way
        if tmp == len(self.players):
            tmp = 0
        if tmp < 0:
            tmp = len(self.players) - 1
        arr = list()
        k = len(self.players)
        while k > 0:
            arr.append(STRINGS['NEXT_PLAYER'] % (self.playerOrder[tmp], len(self.players[self.playerOrder[tmp]])))
            tmp = tmp + self.way
            if tmp == len(self.players):
                tmp = 0
            if tmp < 0:
                tmp = len(self.players) - 1
            k-=1
        msg += ' - '.join(arr)
        if user not in self.players:
            self.noticeUser(jenni, user, msg)
        else:
            self.noticeUser(jenni, user, STRINGS['YOUR_CARDS'] % self.renderCards(user, self.players[user], 0))
            self.noticeUser(jenni, user, msg)

    def renderCards(self, nick, cards, is_chan):
        nickk = nick
        if nick:
            nickk = (nick)
        ret = list()
        for c in sorted(cards):
            if c in ['W', 'WD4']:
                sp = str()
                if not is_chan and self.players_pce.get(nickk, 0):
                    sp = ' '
                ret.append('[' + c + ']' + sp)
                continue
            if c[0] == 'W':
                c = c[-1] + '*'
            t = '\x03\x03'
            if c[0] == 'B':
                t += '12'
            elif c[0] == 'Y':
                t += '08'
            elif c[0] == 'G':
                t += '09'
            elif c[0] == 'R':
                t += '04'
            if not is_chan:
                if self.players_pce.get(nickk, 0):
                    t += '%s/ [%s]  ' % (c[0], c[1:])
                else:
                    t += '[%s]' % c[1:]
            else:
                t += '(%s) [%s]' % (c[0], c[1:])
            t += "\x03\x03"
            ret.append(t)
        return ''.join(ret)

    def cardPlayable(self, card):
        if card[0] == 'W' and card[-1] in self.colors:
            return True
        if self.topCard[0] == 'W':
            return card[0] == self.topCard[-1]
    	return (card[0] == self.topCard[0]) or (card[1] == self.topCard[1])

    def cardPlayed(self, jenni, card):
        if card[1:] == 'D2':
            jenni.msg(self.CHANNEL, STRINGS['D2'] % self.playerOrder[self.currentPlayer])
            z = [self.getCard(), self.getCard()]
            self.noticeUser(jenni, self.playerOrder[self.currentPlayer], STRINGS['CARDS'] % self.renderCards(self.playerOrder[self.currentPlayer], z, 0))
            self.players[self.playerOrder[self.currentPlayer]].extend (z)
            self.incPlayer()
        elif card[:2] == 'WD':
            jenni.msg(self.CHANNEL, STRINGS['WD4'] % self.playerOrder[self.currentPlayer])
            z = [self.getCard(), self.getCard(), self.getCard(), self.getCard()]
            self.noticeUser(jenni, self.playerOrder[self.currentPlayer], STRINGS['CARDS'] % self.renderCards(self.playerOrder[self.currentPlayer], z, 0))
            self.players[self.playerOrder[self.currentPlayer]].extend(z)
            self.incPlayer()
        elif card[1] == 'S':
            jenni.msg(self.CHANNEL, STRINGS['SKIPPED'] % self.playerOrder[self.currentPlayer])
            self.incPlayer()
        elif card[1] == 'R' and card[0] != 'W':
            jenni.msg(self.CHANNEL, STRINGS['REVERSED'])
            if len(self.players) > 2:
                self.way = -self.way
                self.incPlayer()
                self.incPlayer()
            else:
                self.incPlayer()
        self.topCard = card

    def gameEnded(self, jenni, winner):
        try:
            score = 0
            for p in self.players:
                for c in self.players[p]:
                    if c[0] == 'W':
                        score += self.special_scores[c]
                    elif c[1] in [ 'S', 'R', 'D' ]:
                        score += self.special_scores[c[1:]]
                    else:
                        score += int(c[1])
            jenni.msg(self.CHANNEL, STRINGS['GAINS'] % (winner, score))
            self.saveScores(self.players.keys(), winner, score, (datetime.now() - self.startTime).seconds)
        except Exception, e:
            print 'Score error: %s' % e
        self.players = dict()
        self.playerOrder = list()
        self.game_on = False
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.dealt = False
        # Trigger event
        onGameEnd(jenni)


    def incPlayer(self):
        self.currentPlayer = self.currentPlayer + self.way
        if self.currentPlayer == len(self.players):
            self.currentPlayer = 0
        if self.currentPlayer < 0:
            self.currentPlayer = len(self.players) - 1

    def saveScores(self, players, winner, score, time):
        try:
            saveScores(players, winner, score, time)
        except Exception, e:
            print 'Failed to saveon SQL db %s' % e

    # Custom added functions ============================================== #
    def rankings(self, rank_type):
        from copy import copy
        self.prescores = list()
        try:
            f = open(self.scoreFile, 'r')
            for l in f:
                t = l.replace('\n', '').split(' ')
                if len(t) < 4: continue
                self.prescores.copy(append (t))
                if len(t) == 4: t.append(0)
            f.close()
        except: pass
        if rank_type == "ppg":
            self.prescores = sorted(self.prescores, lambda x, y: cmp((y[1] != '0') and (float(y[3]) / int(y[1])) or 0, (x[1] != '0') and (float(x[3]) / int(x[1])) or 0))
        elif rank_type == "pw":
            self.prescores = sorted(self.prescores, lambda x, y: cmp((y[1] != '0') and (float(y[2]) / int(y[1])) or 0, (x[1] != '0') and (float(x[2]) / int(x[1])) or 0))
        elif rank_type == "pts":
            self.prescores = sorted(self.prescores, key=lambda x: x[1], reverse=True)

    def showTopCard_demand(self, jenni):
        if not self.game_on or not self.deck:
            return
        jenni.say(STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

    def leave(self, jenni, input):
        nickk = (input.nick)
        self.remove_player(jenni, nickk)

    def rename_player(self, jenni, oldnick, newnick):
        if not self.game_on:
            return

        user = self.players.get(oldnick, None)
        if user is not None:
            self.players[newnick] = self.players[oldnick]
            del self.players[oldnick]
            self.playerOrder[self.playerOrder.index(oldnick)] = newnick

            try:
                self.players_pce[newnick] = self.players_pce[oldnick]
                del self.players_pce[oldnick]
            except KeyError:
                # PCE not set
                pass


    def remove_player(self, jenni, nick):
        if not self.game_on:
            return

        user = self.players.get(nick, None)
        if user is not None:
            numPlayers = len(self.playerOrder)

            self.playerOrder.remove(nick)
            del self.players[nick]

            if self.way == 1 and self.currentPlayer == numPlayers - 1:
                self.currentPlayer = 0
            elif self.way == -1:
                if self.currentPlayer == 0:
                    self.currentPlayer = numPlayers - 2
                else:
                    self.currentPlayer -= 1

            jenni.msg(self.CHANNEL, STRINGS['PLAYER_LEAVES'] % nick)
            if numPlayers == 2 and self.dealt or numPlayers == 1:
                jenni.msg(self.CHANNEL, STRINGS['GAME_STOPPED'])
                self.game_on = None
                self.dealt = None
                onGameEnd(jenni)
                return

            if self.game_on == nick:
                self.game_on = self.playerOrder[0]
                jenni.msg(self.CHANNEL, STRINGS['OWNER_CHANGE'] % (nick, self.playerOrder[0]))

            if self.dealt:
                jenni.msg(self.CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

    def enablePCE(self, jenni, nick):
        nickk = nick
        if not self.players_pce.get(nickk, 0):
            self.players_pce.update({ nickk : 1})
            self.noticeUser(jenni, nickk, STRINGS['PLAYER_COLOR_ENABLED'])
        else:
            self.noticeUser(jenni, nickk, STRINGS['ENABLED_PCE'] % nickk)

    def disablePCE(self, jenni, nick):
        nickk = nick
        if self.players_pce.get(nickk, 0):
            self.players_pce.update({ nickk : 0})
            self.noticeUser(jenni, nickk, STRINGS['PLAYER_COLOR_DISABLED'])
        else:
            self.noticeUser(jenni, nickk, STRINGS['DISABLED_PCE'] % nickk)

    def isPCEEnabled(self, jenni, nick):
        nickk = nick
        if not self.players_pce.get(nickk, 0):
            self.noticeUser(jenni, nickk, STRINGS['DISABLED_PCE'] % nickk)
        else:
            self.noticeUser(jenni, nickk, STRINGS['ENABLED_PCE'] % nickk)

    def PCEClear(self, jenni, nick):
        nickk = nick
        if not self.owners.get(nickk, 0):
            self.players_pce.clear()
            jenni.msg(self.CHANNEL, STRINGS['PCE_CLEARED'] % nickk)

    def unostat(self, jenni, input):
        text = input.group().split()

        if len(text) != 3:
            jenni.reply("Invalid input for stats command. Try '.unostats ppg 10' to show the top 10 ranked by points per game. You can also show rankings by percent-wins 'pw'.")
            return

        if text[1] in ['pw', 'ppg', 'pts']:
            #self.rankings(text[1])
            self.rank_assist(jenni, input, text[2], text[1])

        #if not self.prescores:
        #    jenni.reply(STRINGS['NO_SCORES'])

    def rank_assist(self, jenni, input, nicknum, ranktype):
        nickk = (input.nick).lower()
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
        ord = {"pw":"RATIO", "ppg":"POINT_PER_GAME", "pts":"SCORE"}
        if nicknum.isdigit():
            s = int(nicknum)
            allScore = getAllScoreForBestN(db, s, ord[ranktype])
        else:
            allScore = getPlayerStats(db, nicknum, ord[ranktype])
        for z in allScore:
        	jenni.msg(nickk, STRINGS['SCORE_ROW'] % (ranktype, int(z[0]), z[1], z[6], z[3], z[2], z[4], z[5]))
        db.close()

    def noticeUser(self, jenni, user, message):
        prefix = ""
        for game in unos.values():
            if game == self:
                continue
            if game.game_on and user in game.players:
                prefix = "[%s] " % self.CHANNEL
                break
        jenni.notice(user, "%s%s" % (prefix, message))


def _replyUpdate(jenni, input):
    jenni.msg(input.sender, "Bot is about to restart for an update. " \
                            "Please try again later.")

def uno(jenni, input):
    if input.sender[0] != '#':
        return
    if update_imminent: return _replyUpdate(jenni, input)

    unobot = unos[input.sender]
    unobot.start(jenni, input.nick)
uno.commands = ['uno']
uno.priority = 'low'
uno.thread = False
uno.rate = 0

def unostop(jenni, input):
    if input.sender[0] != '#':
        return

    unobot = unos[input.sender]
    unobot.stop(jenni, input)
unostop.commands = ['unostop']
unostop.priority = 'low'
unostop.thread = False
unostop.rate = 0

def ujoin(jenni, input):
    if input.sender[0] != '#':
        return

    unobot = unos[input.sender]
    unobot.join(jenni, input)
ujoin.commands = ['ujoin', 'uj']
ujoin.priority = 'low'
ujoin.thread = False
ujoin.rate = 0

def deal(jenni, input):
    if input.sender[0] != '#':
        return
    if update_imminent: return _replyUpdate(jenni, input)

    unobot = unos[input.sender]
    unobot.deal(jenni, input)
deal.commands = ['deal']
deal.priority = 'low'
deal.thread = False
deal.rate = 0

def play(jenni, input):
    if input.sender[0] != '#':
        return

    unobot = unos[input.sender]
    unobot.play(jenni, input)
play.commands = ['play', 'p']
play.priority = 'low'
play.thread = False
play.rate = 0

def draw(jenni, input):
    if input.sender[0] != '#':
        return

    unobot = unos[input.sender]
    unobot.draw(jenni, input)
draw.commands = ['draw', 'd', 'dr']
draw.priority = 'low'
draw.thread = False
draw.rate = 0

def passs(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.passs(jenni, input)
passs.commands = ['pass', 'pa']
passs.priority = 'low'
passs.thread = False
passs.rate = 0

#TODO change with MySQL function
def unotop10(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.top10(jenni, input)
unotop10.commands = ['unotop10']
unotop10.priority = 'low'
unotop10.thread = False
unotop10.rate = 0

def show_user_cards(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.showCards(jenni, input.nick)
show_user_cards.commands = ['cards', 'c']
show_user_cards.priority = 'low'
show_user_cards.thread = False
show_user_cards.rate = 0

def top_card(jenni, input):
    if not (input.sender).startswith('#'):
        return
    
    unobot = unos[input.sender]
    unobot.showTopCard_demand(jenni)
top_card.commands = ['top', 'topcard', 'topcards']
top_card.priority = 'low'
top_card.thread = False
top_card.rate = 0

def leave(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.leave(jenni, input)
leave.commands = ['leave']
leave.priority = 'low'
leave.thread = False
leave.rate = 0

def doJoin(jenni, input):
    if input.nick == jenni.config.nick:
        # We've joined a channel! Let's create a uno object for it
        unos[input.sender] = UnoBot(input.sender)
doJoin.event = 'JOIN'
doJoin.rule = '.*'
doJoin.priority = 'low'
doJoin.thread = False
doJoin.rate = 0

def doPart(jenni, input):
    # Remove folks parting midgame
    unos[input.sender].remove_player(jenni, (input.nick))
    # Or remove the game object if we're the one parting
    if input.nick == jenni.config.nick:
        del unos[input.sender]
doPart.event = 'PART'
doPart.rule = '.*'
doPart.priority = 'low'
doPart.thread = False
doPart.rate = 0

def doQuit(jenni, input):
    # Remove folks quitting midgame
    for unobot in unos.values():
        unobot.remove_player(jenni, (input.nick))
doQuit.event = 'QUIT'
doQuit.rule = '.*'
doQuit.priority = 'low'
doQuit.thread = False
doQuit.rate = 0

def doKick(jenni, input):
    # Remove folks getting kicked midgame
    unos[input.sender].remove_player(jenni, (input.args[1]))
doKick.event = 'KICK'
doKick.rule = '.*'
doKick.priority = 'low'
doKick.thread = False
doKick.rate = 0

def doNick(jenni, input):
    # Rename folks that change their nicks midgame
    for unobot in unos.values():
        unobot.rename_player(jenni, input.nick, input.group(0))
doNick.event = 'NICK'
doNick.rule = '.*'
doNick.priority = 'low'
doNick.thread = False
doNick.rate = 0

def unostats(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.unostat(jenni, input)
unostats.commands = ['unostats']
unostats.priority = 'low'
unostats.thread = False
unostats.rate = 0

def uno_help(jenni, input):
    nick = input.group(2)
    txt = 'Check the following link to know how to play UNO with me: https://uno.kthx.at'
    jenni.msg(input.sender,txt)
uno_help.commands = ['uno-help', 'unohelp', 'help']
uno_help.priority = 'low'
uno_help.thread = False
uno_help.rate = 0

def uno_pce_on(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.enablePCE(jenni, input.nick)
uno_pce_on.commands = ['pce-on']
uno_pce_on.priority = 'low'
uno_pce_on.thread = False
uno_pce_on.rate = 0

def uno_pce_off(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.disablePCE(jenni, input.nick)
uno_pce_off.commands = ['pce-off']
uno_pce_off.priority = 'low'
uno_pce_off.thread = False
uno_pce_off.rate = 0

def uno_ispce(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.isPCEEnabled(jenni, input.nick)
uno_ispce.commands = ['pce']
uno_ispce.priority = 'low'
uno_ispce.thread = False
uno_ispce.rate = 0

def uno_pce_clear(jenni, input):
    if input.sender[0] != '#':
        return
    
    unobot = unos[input.sender]
    unobot.PCEClear(jenni, input.nick)
uno_pce_clear.commands = ['.pce-clear']
uno_pce_clear.priority = 'low'
uno_pce_clear.thread = False
uno_pce_clear.rate = 0

#

def active_unos(jenni, input):
    if not input.sender.lower() == BADMIN_CHAN:
        return
    running = 0
    started = 0
    for uno in unos.values():
        if uno.game_on:
            if uno.dealt:
                running += 1
            else:
                started += 1
    msg = "No games currently running."
    if running or started:
        msg = "%s games are currently in-progress, while %s games are undealt." % (running, started)
    jenni.msg(input.sender, msg)
active_unos.commands = ['unos']
active_unos.priority = 'low'
active_unos.thread = False
active_unos.rate = 0

def schedule_update(jenni, input):
    if not input.sender.lower() == BADMIN_CHAN:
        return
    global update_imminent
    update_imminent = True
    jenni.msg(input.sender, "Update scheduled.")
schedule_update.commands = ['schedule']
schedule_update.priority = 'low'
schedule_update.thread = False
schedule_update.rate = 0

def unschedule_update(jenni, input):
    if not input.sender.lower() == BADMIN_CHAN:
        return
    global update_imminent
    update_imminent = False
    jenni.msg(input.sender, "Update unscheduled.")
unschedule_update.commands = ['unschedule']
unschedule_update.priority = 'low'
unschedule_update.thread = False
unschedule_update.rate = 0

def evaluate(jenni, input):
    if not input.sender.lower() == BADMIN_CHAN:
        return
    jenni.msg(input.sender, str(eval(str(input.split(None, 1)[1]), globals(), locals())))
evaluate.commands = ['uploadstats']
evaluate.priority = 'high'
evaluate.thread = True
evaluate.rate = 0

if __name__ == '__main__':
	print "All systems online"


#############################COSTUM##LIBS################################
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

def saveScores(players, winner, score, time):
	### DATABASE SETTINGS
	print players, winner, score, time
	DB_PASSWORD = "unopass"
	DB_HOST = "localhost"
	DB_USER = "unobot"
	DB_NAME = "TEST"
	if winner not in players:
		raise IOError
	db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
	for player in players:
		if not checkExisitingPlayer(db, player):
			insertNewPlayer(db, player)
	
#	updatePlayerScore(db, winner, score)
	id = addGame(db, time, winner, score)
	addPlayersToGame(db, players, time, id)
	db.close()

#SQL QUERIES PART

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
    
def getAllScores(db, order):
	if order not in ["RATIO", "SCORE", "POINT_PER_GAME"]:
		raise IOError
	c = db.cursor()
	c.execute("""SELECT * FROM ( SELECT @rownum := @rownum + 1 AS RANK, t.* FROM (SELECT WINNED.WINNER, WINNED.WINNED, PLAYED.PLAYED,(WINNED.SCORE/PLAYED.PLAYED) AS POINT_PER_GAME, (WINNED.WINNED/PLAYED.PLAYED*100) AS RATIO, WINNED.SCORE
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
        ORDER BY """ + order + """ DESC) t , (SELECT @rownum := 0) r) AS c
	""")
	tmp = c.fetchall()
	return tmp
	
def getPlayerStats(db, player, order):
	if order not in ["RATIO", "SCORE", "POINT_PER_GAME"]:
		raise IOError
	c = db.cursor()

	c.execute("""SELECT * FROM ( SELECT @rownum := @rownum + 1 AS RANK, t.* FROM (SELECT WINNED.WINNER, WINNED.WINNED, PLAYED.PLAYED,(WINNED.SCORE/PLAYED.PLAYED) AS POINT_PER_GAME, (WINNED.WINNED/PLAYED.PLAYED*100) AS RATIO, WINNED.SCORE
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
        ORDER BY """ + order + """ DESC) t , (SELECT @rownum := 0) r) AS c WHERE c.WINNER = \"""" + player + "\"")
	tmp = c.fetchall()

	return tmp

# Consider using LIMIT instead
def getAllScoreForBestN(db, number, order):
	result = getAllScores(db, order)
	if len(result) <= number:
		return result
	else:
		return result[:number]
    
def format(inTuple):
	result = list()
	for tup in inTuple:
		result.append("%d %s, Winned: %d, Played: %d, Point per game %.2f, Ratio: %.2f/n" % (tup[0], tup[1], tup[2], tup[3], tup[4], tup[5]))
	return result
