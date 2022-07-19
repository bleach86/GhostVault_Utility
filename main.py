import time, sys, os, platform, util, getpass, json, random, secrets
from datetime import datetime, timedelta
from database import Database as db

VERSION = "v0.2"
WALLETPASSWORD = None
MINZAP = 0.1
MINTIME = int(60*30) # 30 minutes Int to insure whole number
MAXTIME = int(60*60*2.5) # 2.5 hours Int to insure whole number

system = platform.system()

def isValidCLI():
    cliPath = db().getCliPath()

    if cliPath == '':
        if system == 'Linux':
            desktopPath = os.path.expanduser("~/.config/ghost-desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"
        elif system == 'Windows':
            desktopPath = os.path.expanduser("~/AppData/Roaming/Ghost Desktop/ghostd/unpacked/")
            cliBin = "ghost-cli.exe"
        elif system == 'Darwin':
            desktopPath = os.path.expanduser("~/Library/Application Support/Ghost Desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"

        if not os.path.isdir(desktopPath):
            if os.path.isfile("ghost-cli"):
                db().setCliPath(f"{os.getcwd()}")
                return True
            else:
                print("ERROR: CLI binary not found!")
                sys.exit()
        dirs = [name for name in os.listdir(desktopPath) if os.path.isdir(os.path.join(desktopPath, name))]
        if dirs == []:
            if os.path.isfile(cliBin):
                db().setCliPath(f"{os.getcwd()}")
                return True
            else:
                print("ERROR: CLI binary not found!")
                sys.exit()
        newest = f"{desktopPath}{max(dirs)}/{cliBin}"

        if os.path.isfile(newest):
            db().setCliPath(newest)
            return True
        else:
            print("ERROR: CLI binary not found!")
            sys.exit()
    else:
        if system == 'Linux':
            desktopPath = os.path.expanduser("~/.config/ghost-desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"
        elif system == 'Windows':
            desktopPath = os.path.expanduser("~/AppData/Roaming/Ghost Desktop/ghostd/unpacked/")
            cliBin = "ghost-cli.exe"
        elif system == 'Darwin':
            desktopPath = os.path.expanduser("~/Library/Application Support/Ghost Desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"

        if desktopPath in cliPath:
            dirs = [name for name in os.listdir(desktopPath) if os.path.isdir(os.path.join(desktopPath, name))]
            newest = f"{desktopPath}{max(dirs)}/{cliBin}"

            if newest != cliPath:
                db().setCliPath(newest)
                print(f"Updating to newest CLI binary...")
                return True
            else:
                if os.path.isfile(cliPath):
                    return True
        else:
            if os.path.isfile(cliPath):
                return True
            else:
                print("ERROR: CLI binary not found!")
                sys.exit()


def checkConnection():
    try:
        util.callrpc_cli(db().getCliPath(), "getblockchaininfo")
        return True
    except Exception as e:
        print(e)
        return False


def checkWallet():
    wallet = db().getWalletName()

    if wallet == None:
        while True:
            newWallet = input(f"Enter the name of the wallet you want to use: ")

            if newWallet == '':
                try:
                    util.callrpc_cli(db().getCliPath(), f"-rpcwallet={newWallet} getwalletinfo")
                    print(f"You have chose top use the Default Wallet.")
                    db().setWalletName(newWallet)
                    return True
                except:
                    print('Invalid wallet name, please try again.')
                    continue
            elif newWallet == "Default Wallet":
                try:
                    util.callrpc_cli(db().getCliPath(), f"-rpcwallet={newWallet} getwalletinfo")
                    print(f"You have chose top use the Default Wallet.")
                    db().setWalletName(newWallet)
                    return True
                except:
                    try:
                        util.callrpc_cli(db().getCliPath(), f"-rpcwallet={''} getwalletinfo")
                        print(f"You have chose to use the Default Wallet.")
                        db().setWalletName("")
                        return True
                    except:
                        print('Invalid wallet name, please try again.')
                        continue
            else:
                try:
                    util.callrpc_cli(db().getCliPath(), f"-rpcwallet={newWallet} getwalletinfo")
                    print(f"You have chose to use {newWallet}.")
                    db().setWalletName(newWallet)
                    return True
                except:
                    print('Invalid wallet name, please try again.')
                    continue
    else:
        try:
            util.callrpc_cli(db().getCliPath(), f"-rpcwallet={wallet} getwalletinfo")
            return True
        except:
            print(f"ERROR: Valid wallet not found!")
            sys.exit()


def isEncrypted():
    encryptionStatus = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getwalletinfo")

    if 'encryptionstatus' in encryptionStatus:
        if encryptionStatus['encryptionstatus'] == "Unencrypted":
            return False
        else:
            return True
    return False


def getWalletPassword():
    global WALLETPASSWORD

    walletPass = getpass.getpass(prompt='Enter the wallet password: ')
    try:
        util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} walletpassphrase {walletPass} 1")
        WALLETPASSWORD = walletPass
    except:
        print(f"Invalid password! Please try again later.")
        sys.exit()


def unlockWallet():
    if isEncrypted():
        if not WALLETPASSWORD:
            getWalletPassword()
        try:
            util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} walletpassphrase {WALLETPASSWORD} 2")
        except:
            print(f"Invalid password! Please try again later.")
            sys.exit()


def zapFromAnon(amount):
    unlockWallet()
    spendAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewaddress '' false false true")
    keyIndex = random.randint(0, 499)
    unlockWallet()
    stakeAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} deriverangekeys {keyIndex} {keyIndex} {db().getExtKey()}")[0]
    script = json.dumps({'recipe': 'ifcoinstake', 'addrstake': stakeAddr, 'addrspend': spendAddr})
    unlockWallet()
    scriptHex = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} buildscript '{script}'")['hex']

    output = json.dumps([{"address": "script", "amount": amount, "script": scriptHex, "subfee": True}])

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} sendtypeto 'anon' 'ghost' '{output}'")
    return txid


def zapFromPublic(amount, gvr=False, inputs=[]):
    unlockWallet()
    spendAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewaddress '' false false true")
    keyIndex = random.randint(0, 499)
    unlockWallet()
    stakeAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} deriverangekeys {keyIndex} {keyIndex} {db().getExtKey()}")[0]
    unlockWallet()
    unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")

    if inputs == []:
        inputTotal = 0
        for i in unspent:
            if 'coldstaking_address' in i:
                continue
            inputs.append({"tx": i['txid'], "n": i['vout']})
            inputTotal += i['amount']
            if inputTotal >= amount:
                break

        if inputTotal < amount:
            print(f"Not enough inputs!")
            sys.exit()

    script = json.dumps({'recipe': 'ifcoinstake', 'addrstake': stakeAddr, 'addrspend': spendAddr})
    unlockWallet()
    scriptHex = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} buildscript '{script}'")['hex']

    output = []
    if gvr:
        jobID = db().getJobs()[0][11]
        gvrAddr(jobID, spendAddr)
        zapPart = amount
        while zapPart > 0:
            if zapPart >= 1500:
                output.append({"address": "script", "amount": 1500, "script": scriptHex, "subfee": True})
                zapPart -= 1500
            else:
                output.append({"address": "script", "amount": round(zapPart, 8), "script": scriptHex, "subfee": True})
                break
    else:
        output.append({"address": "script", "amount": amount, "script": scriptHex, "subfee": True})

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} sendtypeto 'ghost' 'ghost' '{json.dumps(output)}' '' '' 5 1 false '{json.dumps({'inputs': inputs})}'")
    return txid


def convertAnonToPublic(amount):
    if not db().getStealthAddr():
        unlockWallet()
        newAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewstealthaddress")
        db().setStealthAddr(newAddr)
    stealthAddr = db().getStealthAddr()

    output = json.dumps([{"address": stealthAddr, "amount": amount, "subfee": True}])

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(),
                            f"-rpcwallet={db().getWalletName()} sendtypeto 'anon' 'ghost' '{output}'")
    return txid


def convertPublicToAnon(amount):
    if not db().getStealthAddr():
        unlockWallet()
        newAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewstealthaddress")
        db().setStealthAddr(newAddr)
    stealthAddr = db().getStealthAddr()

    unlockWallet()
    unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")
    inputTotal = 0
    inputs = []

    for i in unspent:
        if 'coldstaking_address' in i:
            continue
        inputs.append({"tx": i['txid'], "n": i['vout']})
        inputTotal += i['amount']
        if inputTotal >= amount:
            break

    if inputTotal < amount:
        print(f"Not enough inputs!")
        sys.exit()

    output = json.dumps([{"address": stealthAddr, "amount": amount, "subfee": True}])

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(),
                            f"-rpcwallet={db().getWalletName()} sendtypeto 'ghost' 'anon' '{output}' '' '' 5 1 false '{json.dumps({'inputs': inputs})}'")
    return txid


def getAvailableAnon():
    trustedAnon = getBalances()['mine']['anon_trusted']
    return trustedAnon


def getAvailablePublic():
    available = 0
    unlockWallet()
    unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")

    for i in unspent:
        if 'coldstaking_address' in i:
            continue
        available += i['amount']

    available = float(round(available, 8))
    return available


def getBalances():
    unlockWallet()
    balance = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getbalances")
    return balance


def getExtKey():
    extKey = db().getExtKey()

    if not extKey or not isValidExtKey(extKey):
        print(f"Extended public key not found!")
        while True:
            key = input(f"Please enter the Extended public key for your GhostVault\nKEY: ")

            if not isValidExtKey(key):
                print(f'Not a valid Extended Public Key. Please try again.')
            else:
                db().setExtKey(key)
                print(f"Key successfully set.")
                return db().getExtKey()
    else:
        return extKey


def isValidExtKey(key):
    validateAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} validateaddress {key}")

    if not validateAddr['isvalid']:
        return False
    elif 'isextkey' not in validateAddr or not validateAddr['isextkey']:
        return False
    elif validateAddr['isextkey']:
        return True

def clear():
    if system == "Windows":
        os.system('cls')
        print(f"GhostVault Utility {VERSION}")
    else:
        os.system('clear')
        print(f"GhostVault Utility {VERSION}")


def zapLog(logType, logMsg):
    with open("zap.log", "a") as f:
        f.write(f"{datetime.now()} {logType}: {logMsg}\n")


def gvrAddr(jobID, addr):
    with open(f"{jobID}_GVR_Addresses.txt", "a") as f:
        f.write(f"{addr}\n")


def setJob(jobType):
    clear()
    print(f"Job Setup\n\n")
    jobID = secrets.token_urlsafe(4)

    if jobType in [1, 2, 4, 5]:
        while True:
            print(f"GVR Mode will ensure that your zaps are done in multiples of 20k.\n")
            ans = input(f"Would you like to enable GVR mode y/N: ")
            ans = ans.lower()

            if ans == "" or ans == "n":
                print(f"Normal mode Active.")
                gvr = False
                break
            elif ans == "y":
                print("GVR Mode Active")
                print(f"Addresses used for GVR zaps will be logged {os.getcwd()}/{jobID}_GVR_Addresses.txt")
                gvr = True
                break
            else:
                print("Invalid Response.")
                input("Press Enter to continue...")

    if jobType <= 3:
        if jobType == 1:
            totalZap = getAvailablePublic() + getAvailableAnon()
            if totalZap < MINZAP:
                print(f"Balance too low to zap!")
                sys.exit()
            print(f"Setting job {jobID} to zap {totalZap} GHOST from Public and Anon...")
            db().newJob(1, totalZap, 0, gvr, 0, 0, 1, getAvailablePublic(), getAvailableAnon(), jobID)

        elif jobType == 2:
            totalZap = getAvailablePublic()
            if totalZap < MINZAP:
                print(f"Balance too low to zap!")
                sys.exit()
            print(f"Setting job {jobID} to zap {totalZap} GHOST from Public..")
            db().newJob(2, totalZap, 0, gvr, 0, 0, 1, getAvailablePublic(), 0, jobID)

        elif jobType == 3:
            totalZap = getAvailableAnon()
            if totalZap < MINZAP:
                print(f"Balance too low to zap!")
                sys.exit()
            print(f"Setting job {jobID} to zap {totalZap} GHOST from Anon..")
            db().newJob(3, totalZap, 0, gvr, 0, 0, 1, 0, getAvailableAnon(), jobID)
    elif jobType <= 6 and jobType >= 4:

        if jobType == 4:
            while True:
                print(f"Available Public: {getAvailablePublic()}")
                print("\n")
                ans = input(f"Please enter the amount of Public Ghost you would like to zap: ")

                try:
                    ans = round(float(ans), 8)
                except:
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                    continue

                if ans < MINZAP:
                    print(f"Amount is too low to zap!")
                    input("Press Enter to continue...")

                elif ans > getAvailablePublic():
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                elif ans <= getAvailablePublic():
                    zapPub = ans
                    break

            while True:
                print(f"Available Anon: {getAvailableAnon()}")
                print("\n")
                ans = input(f"Please enter the amount of Anon Ghost you would like to zap: ")

                try:
                    ans = round(float(ans), 8)
                except:
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                    continue

                if ans < MINZAP:
                    print(f"Amount is too low to zap!")
                    input("Press Enter to continue...")

                elif ans > getAvailableAnon():
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                elif ans <= getAvailableAnon():
                    zapAnon = ans
                    break
            totalZap = round(zapAnon + zapPub, 8)
            print(f"Setting job {jobID} to zap {totalZap} Ghost from Public and Anon")
            db().newJob(4, totalZap, 0, gvr, 0, 0, 1, zapPub, zapAnon, jobID)

        elif jobType == 5:
            while True:
                print(f"Available Public: {getAvailablePublic()}")
                print("\n")
                ans = input(f"Please enter the amount of Public Ghost you would like to zap: ")

                try:
                    ans = round(float(ans), 8)
                except:
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                    continue

                if ans < MINZAP:
                    print(f"Amount is too low to zap!")
                    input("Press Enter to continue...")

                elif ans > getAvailablePublic():
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                elif ans <= getAvailablePublic():
                    zapPub = ans
                    break

            totalZap = round(zapPub, 8)
            print(f"Setting job {jobID} to zap {totalZap} Ghost from Public")
            db().newJob(5, totalZap, 0, gvr, 0, 0, 1, zapPub, 0, jobID)

        elif jobType == 6:
            while True:
                print(f"Available Anon: {getAvailableAnon()}")
                print("\n")
                ans = input(f"Please enter the amount of Anon Ghost you would like to zap: ")

                try:
                    ans = round(float(ans), 8)
                except:
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                    continue

                if ans < MINZAP:
                    print(f"Amount is too low to zap!")
                    input("Press Enter to continue...")

                if ans > getAvailableAnon():
                    print("Invalid Response.")
                    input("Press Enter to continue...")
                elif ans <= getAvailableAnon():
                    zapAnon = ans
                    break

            totalZap = round(zapAnon, 8)
            print(f"Setting job {jobID} to zap {totalZap} Ghost from Anon")
            db().newJob(6, totalZap, 0, gvr, 0, 0, 1, 0, zapAnon, jobID)


def processJobs():
    jobs = db().getJobs()
    if jobs == []:
        print(f"No active jobs found.")
        return

    for job in jobs:
        jobType = job[0]
        maxZap = job[1]
        currentZapAmount = job[2]
        gvr = job[3]
        lastZap = job[4]
        nextZap = job[5]
        isActive = job[6]
        zapPub = job[7]
        zapAnon = job[8]
        jobID = job[11]
        timeNow = int(time.time())
        nextTime = random.randint(MINTIME, MAXTIME)
        balance = getBalances()
        pendingAnon = balance['mine']['anon_immature'] + balance['mine']['anon_untrusted_pending']
        leftToZap = maxZap - currentZapAmount

        availableAnon = getAvailableAnon()
        availablePublic = getAvailablePublic()

        txn = db().getTxid(jobType)
        txAnon = db().getTxidAnon(jobType)

        if txn and not checkUnspent(txn):
            print(f"UTXO not yet confirmed. Retrying in 5 minutes...")
            zapLog("PENDWAIT", f"jobID: {jobID} Waiting on {pendingAnon} pending Public Ghost")
            db().setNextZap(jobType, int(timeNow + 300))
            return
        if txAnon and not checkUnspent(txAnon, True) and pendingAnon > 0:
            print(f"UTXO not yet confirmed. Retrying in 5 minutes...")
            zapLog("PENDWAIT", f"jobID: {jobID} Waiting on {pendingAnon} pending ANON Ghost")
            db().setNextZap(jobType, int(timeNow + 300))
            return

        if not isActive:
            print(f"Removing inactive job!")
            db().removeJob(jobType)
            return

        if jobType in [1, 4, 3, 6]:
            if leftToZap < availableAnon:
                availableAnon = leftToZap
            if lastZap == 0:
                if availablePublic >= MINZAP and jobType in [1, 4]:
                    print(f"Sending {zapPub} Ghost to Anon from Public.")
                    txid = convertPublicToAnon(zapPub)
                    zapLog("P2A", f"jobID: {jobID} Sent {zapPub} GHOST to ANON from PUBLIC\nTXID: {txid}")
                    db().setTxidAnon(jobType, txid)
                    db().setLastZap(jobType, timeNow)
                    db().setNextZap(jobType, int(timeNow+nextTime))
                    print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                elif availablePublic < MINZAP and gvr or jobType in [3, 6] and gvr:
                    if availableAnon >= 20001:
                        print(f"Sending 20,001 Ghost to Public from Anon.")
                        txid = convertAnonToPublic(round(float(20001), 8))
                        zapLog("A2P", f"jobID: {jobID} Sent 20001 GHOST to PUBLIC from ANON\nTXID: {txid}")
                        db().setTxid(jobType, txid)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon >= 20000:
                        print(f"Sending {availableAnon} Ghost to Public from Anon.")
                        txid = convertAnonToPublic(round(float(availableAnon), 8))
                        zapLog("A2P", f"jobID: {jobID} Sent {availableAnon} GHOST to PUBLIC from ANON\nTXID: {txid}")
                        db().setTxid(jobType, txid)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon < 20000 and availableAnon >= 1500:
                        print(f"Zapping 1500 Ghost from Anon.")
                        txid = zapFromAnon(round(float(1500), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped 1500 GHOST from ANON\nTXID: {txid}")
                        db().setTxidAnon(jobType, txid)
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + 1500)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon < 20000 and availableAnon < 1500:
                        print(f"Zapping {availableAnon} Ghost from Anon.")
                        txid = zapFromAnon(round(float(availableAnon), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped {availableAnon} GHOST from ANON\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availableAnon)
                        zapLog("ZAPALL", f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()
                    elif pendingAnon >= MINZAP and leftToZap > 0:
                        print(f"Waiting on {pendingAnon} pending ANON Ghost")
                        zapLog("PENDWAIT", f"jobID: {jobID} Waiting on {pendingAnon} pending ANON Ghost")
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")

                elif availablePublic < MINZAP and not gvr or jobType in [3, 6] and not gvr:
                    if availableAnon >= 1500:
                        print(f"Zapping 1500 Ghost from Anon.")
                        txid = zapFromAnon(round(float(1500), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped 1500 GHOST from ANON\nTXID: {txid}")
                        db().setTxidAnon(jobType, txid)
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + 1500)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon < 1500:
                        print(f"Zapping {availableAnon} Ghost from Anon.")
                        txid = zapFromAnon(round(float(availableAnon), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped {availableAnon} GHOST from ANON\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availableAnon)
                        zapLog("ZAPALL", f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()
                    elif pendingAnon >= MINZAP and leftToZap > 0:
                        print(f"Waiting on {pendingAnon} pending ANON Ghost")
                        zapLog("PENDWAIT", f"jobID: {jobID} Waiting on {pendingAnon} pending ANON Ghost")
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
            else:

                if gvr and nextZap <= timeNow:
                    if txn:
                        unlockWallet()
                        unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")
                        for i in unspent:
                            if i['txid'] == txn:
                                inputs = [{'tx': txn, 'n': i['vout']}]
                                amount = i['amount']
                                break
                        print(f"Zapping {amount} Ghost from Public.")
                        txid = zapFromPublic(round(float(amount), 8), True, inputs)
                        zapLog("ZAP", f"jobID: {jobID} Zapped {amount} GHOST from PUBLIC\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + amount)
                        db().setTxid(jobType, None)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")

                    elif availableAnon >= 20001:
                        print(f"Sending 20,001 Ghost to Public from Anon.")
                        txid = convertAnonToPublic(round(float(20001), 8))
                        zapLog("A2P", f"jobID: {jobID} Sent 20001 GHOST to PUBLIC from ANON\nTXID: {txid}")
                        db().setTxidAnon(jobType, None)
                        db().setTxid(jobType, txid)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon >= 20000:
                        print(f"Sending {availableAnon} Ghost to Anon from Public.")
                        txid = convertAnonToPublic(round(float(availableAnon), 8))
                        zapLog("A2P", f"jobID: {jobID} Sent {availableAnon} GHOST to PUBLIC from ANON\nTXID: {txid}")
                        db().setTxidAnon(jobType, None)
                        db().setTxid(jobType, txid)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon < 20000 and availableAnon >= 1500:
                        print(f"Zapping 1500 Ghost from Anon.")
                        txid = zapFromAnon(round(float(1500), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped 1500 GHOST from ANON\nTXID: {txid}")
                        db().setTxidAnon(jobType, txid)
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + 1500)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon < 20000 and availableAnon < 1500 and availableAnon > MINZAP:
                        print(f"Zapping {availableAnon} Ghost from Anon.")
                        txid = zapFromAnon(round(float(availableAnon), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped {availableAnon} GHOST from ANON\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availableAnon)
                        zapLog("ZAPALL", f"jobID: {jobID} Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()
                    elif pendingAnon >= MINZAP:
                        print(f"Waiting on {pendingAnon} pending ANON Ghost")
                        zapLog("PENDWAIT", f"jobID: {jobID} Waiting on {pendingAnon} pending ANON Ghost")
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")

                elif not gvr and nextZap <= timeNow:
                    if availableAnon >= 1500:
                        print(f"Zapping 1500 Ghost from Anon.")
                        txid = zapFromAnon(round(float(1500), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped 1500 GHOST from ANON\nTXID: {txid}")
                        db().setTxidAnon(jobType, txid)
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + 1500)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availableAnon < 1500 and availableAnon > MINZAP:
                        print(f"Zapping {availableAnon} Ghost from Anon.")
                        txid = zapFromAnon(round(float(availableAnon), 8))
                        zapLog("ZAPANON", f"jobID: {jobID} Zapped {availableAnon} GHOST from ANON\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availableAnon)
                        zapLog("ZAPALL", f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()
                    elif pendingAnon >= MINZAP:
                        print(f"Waiting on {pendingAnon} pending ANON Ghost")
                        zapLog("PENDWAIT", f"jobID: {jobID} Waiting on {pendingAnon} pending ANON Ghost")
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + 300))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    else:
                        print(f"Job complete")
                        db().removeJob(jobType)
                        sys.exit()

        elif jobType in [2, 5]:
            if lastZap == 0 or nextZap <= timeNow:
                if leftToZap < availablePublic:
                    availablePublic = leftToZap
                if availablePublic >= MINZAP and gvr:
                    if availablePublic >= 20001:
                        print(f"Zapping 20001 Ghost from Public.")
                        txid = zapFromPublic(round(float(20001), 8), True)
                        zapLog("ZAP", f"jobID: {jobID} Zapped 20001 GHOST from PUBLIC\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availablePublic)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availablePublic >= 20000:
                        print(f"Zapping {availablePublic} Ghost from Public.")
                        txid = zapFromPublic(round(float(availablePublic), 8), True)
                        zapLog("ZAP", f"jobID: {jobID} Zapped {availablePublic} GHOST from PUBLIC\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availablePublic)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availablePublic < 20000 and availablePublic >= 1500:
                        print(f"Zapping 1500 Ghost from Public.")
                        txid = zapFromPublic(round(float(1500), 8))
                        zapLog("ZAP", f"jobID: {jobID} Zapped 1500 GHOST from PUBLIC\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + 1500)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availablePublic < 20000 and availablePublic < 1500:
                        print(f"Zapping {availablePublic} Ghost from Public.")
                        txid = zapFromAnon(round(float(availablePublic), 8))
                        zapLog("ZAP", f"jobID: {jobID} Zapped {availablePublic} GHOST from PUBLIC\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availablePublic)
                        zapLog("ZAPPUB", f"jobID: {jobID} Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()

                elif availablePublic >= MINZAP and not gvr:
                    if availablePublic >= 1500:
                        print(f"Zapping 1500 Ghost from Public.")
                        txid = zapFromPublic(round(float(1500), 8))
                        zapLog("ZAP", f"jobID: {jobID} Zapped 1500 GHOST from ANON\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + 1500)
                        db().setLastZap(jobType, timeNow)
                        db().setNextZap(jobType, int(timeNow + nextTime))
                        print(f"Zap progress: {round(db().getCurrentZapAmount(jobType) / maxZap * 100, 2)}%")
                    elif availablePublic < 1500:
                        print(f"Zapping {availablePublic} Ghost from Public.")
                        txid = zapFromPublic(round(float(availablePublic), 8))
                        zapLog("ZAP", f"jobID: {jobID} Zapped {availablePublic} GHOST from ANON\nTXID: {txid}")
                        db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + availablePublic)
                        zapLog("ZAPPUB", f"jobID: {jobID} Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Sucsessfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()
                else:
                    print(f"Job complete")
                    db().removeJob(jobType)


def checkUnspent(txid, anon=False):
    if anon:
        unlockWallet()
        unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspentanon")
    elif not anon:
        unlockWallet()
        unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")

    for i in unspent:
        if i['txid'] == txid:
            return True
    return False


def menu():
    while True:
        clear()
        print(f"Task Selection.\n\n")
        print(f"1: Zap All PUB+ANON")
        print(f"2: Zap All PUB")
        print(f"3: Zap All ANON")
        print(f"4: Zap Part PUB+ANON")
        print(f"5: Zap Part PUB")
        print(f"6: Zap Part ANON")
        print("\n")
        print(f"Available Public: {getAvailablePublic()}")
        print(f"Available Anon: {getAvailableAnon()}")
        wallet = db().getWalletName()
        if wallet == "":
            wallet = "[Default Wallet]"
        print(f"Current Wallet: {wallet}")
        print("\n")
        print(f"7: Change Wallet")
        print(f"8: Set new Extended Public Key")
        print(f"9: Exit")
        print("\n")
        ans = input(f"Please enter the number of the task you would like to start: ")

        if ans == '1':
            setJob(int(ans))
            break
        elif ans == '2':
            setJob(int(ans))
            break
        elif ans == '3':
            setJob(int(ans))
            break
        elif ans == '4':
            setJob(int(ans))
            break
        elif ans == '5':
            setJob(int(ans))
            break
        elif ans == '6':
            setJob(int(ans))
            break
        elif ans == '7':
            db().setWalletName(None)
            checkWallet()
            if isEncrypted():
                print(f"Encrypted wallet found!")
                getWalletPassword()
        elif ans == '8':
            db().setExtKey(None)
            getExtKey()
        elif ans == '9':
            print(f"Goodbye")
            sys.exit()
        else:
            print("Invalid Response.")
            input("Press Enter to continue...")
    startJob()


def startJob():
    while True:
        job = db().getJobs()
        if job == []:
            print(f"No active jobs found")
            sys.exit()
        processJobs()
        job = db().getJobs()
        if job == []:
            print(f"No active jobs found")
            sys.exit()
        print(f"Next action at: {str(datetime.fromtimestamp(job[0][5]))}")

        sleepTime = job[0][5]-time.time()

        if sleepTime > 0:
            time.sleep(sleepTime)


def start():
    print(f"GhostVault Utility {VERSION}\n")
    print(f"Initializing GhostVault Utility...")
    print(f"Checking for CLI binary...")
    if isValidCLI():
        print(f"CLI binary found!")
    print(f"Checking connection to ghostd...")
    if checkConnection():
        print(f"ghostd connected!")
    else:
        print(f"Failed to connect to ghostd!")
        sys.exit()
    print(f"Checking for valid wallet...")
    if checkWallet():
        wallet = db().getWalletName()
        if wallet == "":
            wallet = "[Default Wallet]"
        print(f"Valid wallet {wallet} found!")
    if isEncrypted():
        print(f"Encrypted wallet found!")
        getWalletPassword()
    else:
        print(f'Wallet not encrypted.')
    print(f"Checking for GhostVault extended key...")
    if getExtKey():
        print("Extended Key found!")

    job = db().getJobs()
    if job != []:
        percent = round(job[0][2] / job[0][1] * 100, 2)
        print(f"Job {job[0][11]} found: {percent}% of the way zapped.")
        while True:
            ans = input(f"Would you like to resume this job? Y/n ")
            if ans.lower() == 'y' or ans == '':
                print('Resuming job...')
                startJob()
                break
            elif ans.lower() == 'n':
                db().removeJob(job[0][0])
                menu()
                break
            else:
                print("Invalid Response.")
                input("Press Enter to continue...")
    else:
        menu()


if __name__ == '__main__':
    start()