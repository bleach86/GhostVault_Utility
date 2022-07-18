import sqlite3, json

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("ghostzap.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        self.tableList = []
        for i in tables:
            self.tableList.append(i[0])

        if 'settings' not in self.tableList:
            self.initSettings()
        if 'jobs' not in self.tableList:
            self.initJobs()

    def initSettings(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE settings (
                                   cliPath text,
                                   extKey text,
                                   stealthAddr text,
                                   walletName
                                )""")

        with self.conn:
            self.cursor.execute(
                """INSERT INTO settings VALUES (:cliPath, :extKey, :stealthAddr, :walletName)""",
                {'cliPath': '', 'extKey': None, 'walletName': None, 'stealthAddr': None})


    def initJobs(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE jobs (
                                   type integer,
                                   maxZap real,
                                   currentZapAmount real,
                                   gvrMode integer,
                                   lastZap integer,
                                   nextZap integer,
                                   isActive integer,
                                   zapPub real,
                                   zapAnon real,
                                   txid text,
                                   txidAnon text,
                                   jobID text
                                )""")


    def getCliPath(self):
        self.cursor.execute("""SELECT * FROM settings""")
        cliPath = self.cursor.fetchone()[0]
        return cliPath

    def setCliPath(self, path):
        with self.conn:
            self.cursor.execute("""UPDATE settings SET cliPath=:cliPath""", {"cliPath": path})


    def getExtKey(self):
        self.cursor.execute("""SELECT * FROM settings""")
        extKey = self.cursor.fetchone()[1]
        return extKey

    def setExtKey(self, key):
        with self.conn:
            self.cursor.execute("""UPDATE settings SET extKey=:extKey""", {"extKey": key})


    def getStealthAddr(self):
        self.cursor.execute("""SELECT * FROM settings""")
        stealthAddr = self.cursor.fetchone()[2]
        return stealthAddr

    def setStealthAddr(self, stealthAddr):
        with self.conn:
            self.cursor.execute("""UPDATE settings SET stealthAddr=:stealthAddr""", {"stealthAddr": stealthAddr})


    def getWalletName(self):
        self.cursor.execute("""SELECT * FROM settings""")
        cliPath = self.cursor.fetchone()[3]
        return cliPath

    def setWalletName(self, name):
        with self.conn:
            self.cursor.execute("""UPDATE settings SET walletName=:walletName""", {"walletName": name})


    def isJob(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        existing = self.cursor.fetchall()
        if len(existing) < 1:
            return False
        else:
            return True


    def newJob(self, type, maxZap, currentZapAmount, gvrMode, lastZap, nextZap, isActive, zapPub, zapAnon, jobID):
        if not self.isJob(type):
            with self.conn:
                self.cursor.execute("""INSERT INTO jobs VALUES (:type, :maxZap, :currentZapAmount, :gvrMode, :lastZap, :nextZap, :isActive, :zapPub, :zapAnon, :txid, :txidAnon, :jobID)""",
                                    {'type': type, 'maxZap': maxZap, 'currentZapAmount': currentZapAmount, 'gvrMode': gvrMode,
                                     'lastZap': lastZap, 'nextZap': nextZap, 'isActive': isActive, 'zapPub': zapPub, 'zapAnon': zapAnon, 'txid': None, 'txidAnon': None, 'jobID': jobID})

    def removeJob(self, type):
        with self.conn:
            self.cursor.execute(f"""DELETE from jobs WHERE type=:type""", {"type": type})

    def getJobs(self):
        self.cursor.execute("""SELECT * FROM jobs""")
        existing = self.cursor.fetchall()
        return existing

    def getMaxZap(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        maxZap = self.cursor.fetchone()[1]
        return maxZap

    def setMaxZap(self, type, maxZap):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET maxZap=:maxZap WHERE type=:type""", {"maxZap": maxZap, "type": type})


    def getCurrentZapAmount(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        currentZap = self.cursor.fetchone()[2]
        return currentZap

    def setCurrentZapAmount(self, type, currentZapAmount):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET currentZapAmount=:currentZapAmount WHERE type=:type""", {"currentZapAmount": currentZapAmount, "type": type})

    def getGvrMode(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        gvrMode = self.cursor.fetchone()[3]
        return gvrMode

    def setGvrMode(self, type, gvrMode):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET gvrMode=:gvrMode WHERE type=:type""", {"gvrMode": gvrMode, "type": type})


    def getLastZap(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        lastZap = self.cursor.fetchone()[4]
        return lastZap

    def setLastZap(self, type, lastZap):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET lastZap=:lastZap WHERE type=:type""", {"lastZap": lastZap, "type": type})


    def getNextZap(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        nextZap = self.cursor.fetchone()[5]
        return nextZap

    def setNextZap(self, type, nextZap):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET nextZap=:nextZap WHERE type=:type""", {"nextZap": nextZap, "type": type})


    def getIsActive(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        isActive = self.cursor.fetchone()[6]
        return isActive

    def setIsActive(self, type, isActive):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET isActive=:isActive WHERE type=:type""", {"isActive": isActive, "type": type})

    def getTxid(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        txid = self.cursor.fetchone()[9]
        return txid

    def setTxid(self, type, txid):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET txid=:txid WHERE type=:type""", {"txid": txid, "type": type})

    def getTxidAnon(self, type):
        self.cursor.execute("""SELECT * FROM jobs WHERE type=:type""", {'type': type})
        txid = self.cursor.fetchone()[10]
        return txid

    def setTxidAnon(self, type, txid):
        with self.conn:
            self.cursor.execute("""UPDATE jobs SET txidAnon=:txidAnon WHERE type=:type""", {"txidAnon": txid, "type": type})
