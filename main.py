import time, sys, os, platform, util, getpass, json, random, secrets
from datetime import datetime, timedelta
from database import Database as db

VERSION = "v0.2"
WALLETPASSWORD = None
MINZAP = 0.1
MINTIME = int(60*30)  # 30 minutes Int to insure whole number
MAXTIME = int(60*60*2.5)  # 2.5 hours Int to insure whole number

system = platform.system()

def isValidCLI():
    cliPath = db().getCliPath()

    if cliPath == '':
        if system == 'Linux':
            desktopPath = os.path.expanduser("~/.config/ghost-desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"
        elif system == 'Windows':
            desktopPath = os.path.expanduser("~\\AppData\\Roaming\\Ghost Desktop\\ghostd\\unpacked\\")
            cliBin = "ghost-cli.exe"
        elif system == 'Darwin':
            desktopPath = os.path.expanduser("~/Library/Application Support/Ghost Desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"

        if not os.path.isdir(desktopPath):
            if os.path.isfile("ghost-cli") or os.path.isfile("ghost-cli.exe"):
                if system == 'Windows':
                    db().setCliPath(f"{os.getcwd()}\\ghost-cli.exe")
                else:
                    db().setCliPath(f"{os.getcwd()}/ghost-cli")
                return True
            else:
                input("ERROR: CLI binary not found! Press Enter to exit.")
                sys.exit()
        dirs = [name for name in os.listdir(desktopPath) if os.path.isdir(os.path.join(desktopPath, name))]
        if dirs == []:
            if os.path.isfile(cliBin):
                db().setCliPath(f"{os.getcwd()}")
                return True
            else:
                input("ERROR: CLI binary not found! Press Enter to exit.")
                sys.exit()
        newest = f"{desktopPath}{max(dirs)}/{cliBin}"
        if system == 'Windows':
            newest = f"{desktopPath}{max(dirs)}\\{cliBin}"

        if os.path.isfile(newest):
            db().setCliPath(newest)
            return True
        else:
            input("ERROR: CLI binary not found! Press Enter to exit.")
            sys.exit()
    else:
        if system == 'Linux':
            desktopPath = os.path.expanduser("~/.config/ghost-desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"
        elif system == 'Windows':
            desktopPath = os.path.expanduser("~\\AppData\\Roaming\\Ghost Desktop\\ghostd\\unpacked\\")
            cliBin = "ghost-cli.exe"
        elif system == 'Darwin':
            desktopPath = os.path.expanduser("~/Library/Application Support/Ghost Desktop/ghostd/unpacked/")
            cliBin = "ghost-cli"

        if desktopPath in cliPath:
            dirs = [name for name in os.listdir(desktopPath) if os.path.isdir(os.path.join(desktopPath, name))]
            newest = f"{desktopPath}{max(dirs)}/{cliBin}"
            if system == 'Windows':
                newest = f"{desktopPath}{max(dirs)}\\{cliBin}"

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
                input("ERROR: CLI binary not found! Press Enter to exit.")
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
            input(f"ERROR: Valid wallet not found! Press Enter to exit.")
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
        input(f"Invalid password! Please try again later. Press Enter to exit")
        sys.exit()


def unlockWallet():
    if isEncrypted():
        if not WALLETPASSWORD:
            getWalletPassword()
        try:
            util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} walletpassphrase {WALLETPASSWORD} 2")
        except:
            input(f"Invalid password! Please try again later. Press Enter to exit")
            sys.exit()


def getStealthAddr():
    if not db().getStealthAddr():
        unlockWallet()
        newAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewstealthaddress")
        db().setStealthAddr(newAddr)
    stealthAddr = db().getStealthAddr()
    return stealthAddr


def zapFromAnon(amount):
    unlockWallet()
    spendAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewaddress '' false false true")
    keyIndex = random.randint(0, 999)
    unlockWallet()
    stakeAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} deriverangekeys {keyIndex} {keyIndex} {db().getExtKey()}")[0]
    script = '{\\"recipe\\": \\"ifcoinstake\\", \\"addrstake\\": ' +  '\\"' + f'{stakeAddr}' + '\\", \\"addrspend\\": \\"' + f'{spendAddr}' + '\\"}'
    unlockWallet()
    scriptHex = util.callrpc_cli(db().getCliPath(), f'-rpcwallet={db().getWalletName()} buildscript "{script}"')['hex']

    output = '[{\\"address\\": \\"script\\", \\"amount\\": ' + f'{amount}' + ', \\"script\\": ' + '\\"' + f'{scriptHex}' + '\\"' + ', \\"subfee\\": true}]'

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(), f'-rpcwallet={db().getWalletName()} sendtypeto "anon" "ghost" "{output}"')
    return txid


def zapFromPublic(amount, gvr=False, inputs=''):
    unlockWallet()
    spendAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} getnewaddress '' false false true")
    keyIndex = random.randint(0, 999)
    unlockWallet()
    stakeAddr = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} deriverangekeys {keyIndex} {keyIndex} {db().getExtKey()}")[0]
    unlockWallet()
    unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")

    if inputs == '':
        inputTotal = 0
        inputs = inputs + '{\\"changeaddress\\": \\"' + f'{getStealthAddr()}' + '\\", \\"inputs\\": ['
        for i in unspent:
            if 'coldstaking_address' in i:
                continue
            inputs += '{\\"tx\\": \\"' + f'{i["txid"]}' + '\\", ' + '\\"n\\": ' + f'{i["vout"]}' + '}, '
            inputTotal += i['amount']
            if inputTotal >= amount:
                inputs = inputs[:-2] + ']}'
                break

        if inputTotal < amount:
            input(f"Not enough inputs! Press Enter to exit.")
            sys.exit()
    script = '{\\"recipe\\": \\"ifcoinstake\\", \\"addrstake\\": ' + '\\"' + f'{stakeAddr}' + '\\", \\"addrspend\\": \\"' + f'{spendAddr}' + '\\"}'
    unlockWallet()
    scriptHex = util.callrpc_cli(db().getCliPath(), f'-rpcwallet={db().getWalletName()} buildscript "{script}"')['hex']

    output = '['
    if gvr:
        jobID = db().getJobs()[0][11]
        gvrAddr(jobID, spendAddr)
        zapPart = amount
        while zapPart > 0:
            if zapPart >= 1500:
                output += '{\\"address\\": \\"script\\", \\"amount\\": 1500, \\"script\\": \\"' + f'{scriptHex}' + '\\", \\"subfee\\": true}, '
                zapPart -= 1500
            else:
                output += '{\\"address\\": \\"script\\", \\"amount\\": ' + f'{round(zapPart, 8)}' + ', \\"script\\": \\"' + f'{scriptHex}' + '\\", \\"subfee\\": true}, '
                break
    else:
        output += '{\\"address\\": \\"script\\", \\"amount\\": ' + f'{amount}' + ', \\"script\\": \\"' + f'{scriptHex}' + '\\", \\"subfee\\": true}, '

    output = output[:-2] + ']'

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(), f'-rpcwallet={db().getWalletName()} sendtypeto "ghost" "ghost" "{output}" "" "" 5 1 false "{inputs}"')
    return txid


def convertAnonToPublic(amount):
    output = '[{\\"address\\": \\"' + f'{getStealthAddr()}' + '\\", \\"amount\\": ' + f'{amount}' + ', \\"subfee\\": true}]'

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(),
                            f'-rpcwallet={db().getWalletName()} sendtypeto "anon" "ghost" "{output}"')
    return txid


def convertPublicToAnon(amount, inputs=''):
    unlockWallet()
    unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")

    inputTotal = 0
    if inputs == '':
        inputs = '{\\"changeaddress\\": \\"' + f'{getStealthAddr()}' + '\\"inputs\\": ['
        for i in unspent:
            if 'coldstaking_address' in i:
                continue
            inputs += '{\\"tx\\": \\"' + f'{i["txid"]}' + '\\", \\"n\\": ' + f'{i["vout"]}' + '}, '
            inputTotal += i['amount']
            if inputTotal >= amount:
                inputs = inputs[:-2] + ']}'
                break

        if inputTotal < amount:
            input(f"Not enough inputs! Press Enter to exit.")
            sys.exit()

    output = '[{\\"address\\": \\"' + f'{getStealthAddr()}' + '\\", \\"amount\\": ' + f'{amount}' + ', \\"subfee\\": true}]'

    unlockWallet()
    txid = util.callrpc_cli(db().getCliPath(),
                            f'-rpcwallet={db().getWalletName()} sendtypeto "ghost" "anon" "{output}" "" "" 5 1 false "{inputs}"')
    return txid


def getAvailableAnon():
    trustedAnon = getBalances()['mine']['anon_trusted']
    return trustedAnon


def getAvailablePublic(staked=False):
    available = 0
    unlockWallet()
    unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")

    if not staked:
        for i in unspent:
            if 'coldstaking_address' in i:
                continue
            available += i['amount']
    else:
        for i in unspent:
            if 'coldstaking_address' not in i:
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
    if system == 'Windows':
        slash = '\\'
    else:
        slash = '/'

    if jobType in [1, 2, 3, 4, 5, 6]:
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
                print(f"Addresses used for GVR zaps will be logged {os.getcwd()}{slash}{jobID}_GVR_Addresses.txt")
                gvr = True
                break
            else:
                print("Invalid Response.")
                input("Press Enter to continue...")

    if jobType in [1, 2, 3]:
        if jobType == 1:
            totalZap = getAvailablePublic() + getAvailableAnon()
            if totalZap < MINZAP:
                input(f"Balance too low to zap! Press Enter to exit.")
                sys.exit()
            print(f"Setting job {jobID} to zap {totalZap} GHOST from Public and Anon...")
            db().newJob(1, totalZap, 0, gvr, 0, 0, 1, getAvailablePublic(), getAvailableAnon(), jobID)

        elif jobType == 2:
            totalZap = getAvailablePublic()
            if totalZap < MINZAP:
                input(f"Balance too low to zap! Press Enter to exit.")
                sys.exit()
            print(f"Setting job {jobID} to zap {totalZap} GHOST from Public..")
            db().newJob(2, totalZap, 0, gvr, 0, 0, 1, getAvailablePublic(), 0, jobID)

        elif jobType == 3:
            totalZap = getAvailableAnon()
            if totalZap < MINZAP:
                input(f"Balance too low to zap! Press Enter to exit.")
                sys.exit()
            print(f"Setting job {jobID} to zap {totalZap} GHOST from Anon..")
            db().newJob(3, totalZap, 0, gvr, 0, 0, 1, 0, getAvailableAnon(), jobID)
    elif jobType in [4, 5, 6]:

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
    elif jobType == 7:
        staked = getAvailablePublic(True)
        if staked <= 0:
            input(f"No coins to unstake. Press Enter to exit.")
            sys.exit()
        print(f"Setting job {jobID} to securely unzap {staked} Ghost")
        db().newJob(7, staked, 0, 0, 0, 0, 1, 0, 0, jobID)


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

        if not isActive:
            print(f"Removing inactive job!")
            db().removeJob(jobType)
            return

        if nextZap <= timeNow:
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
                        zapLog("ZAPALL", f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
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
                        zapLog("ZAPALL", f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
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
                        inputs = '{\\"changeaddress\\": \\"' + f'{getStealthAddr()}' + '\\", \\"inputs\\": ['
                        for i in unspent:
                            if i['txid'] == txn:
                                inputs += '{\\"tx\\": \\"' + f'{txn}' + '\\", \\"n\\": ' + f'{i["vout"]}' + '}]}'
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
                        zapLog("ZAPALL", f"jobID: {jobID} Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
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
                        zapLog("ZAPALL", f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
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
                        zapLog("ZAPPUB", f"jobID: {jobID} Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
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
                        zapLog("ZAPPUB", f"jobID: {jobID} Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        print(f"Successfully zapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                        db().removeJob(jobType)
                        sys.exit()
                else:
                    print(f"Job complete")
                    db().removeJob(jobType)

        elif jobType == 7:
            if lastZap == 0 or nextZap <= timeNow:
                staked = getAvailablePublic(True)

                if staked <= 0:
                    print(f"Job complete")
                    zapLog("UNZAP",
                           f"jobID: {jobID} Successfully Unzapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                    db().removeJob(jobType)
                    sys.exit()

                unlockWallet()
                unspent = util.callrpc_cli(db().getCliPath(), f"-rpcwallet={db().getWalletName()} listunspent")
                inputs = '{\\"changeaddress\\": \\"' + f'{getStealthAddr()}' + '\\", \\"inputs\\": ['
                addr = None
                amount = 0

                for i in unspent:
                    if 'coldstaking_address' in i:
                        if not addr:
                            addr = i['address']
                        if i['address'] == addr:
                            inputs += '{\\"tx\\": \\"' + f'{i["txid"]}' + '\\", \\"n\\": ' + f'{i["vout"]}' + '}, '
                            amount += i['amount']
                if not addr:
                    print(f"No staking inputs found.")
                    print(f"Job complete")
                    zapLog("UNZAP",
                           f"jobID: {jobID} Successfully Unzapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                    db().removeJob(jobType)
                    sys.exit()
                else:
                    inputs = inputs[:-2] + ']}'
                print(f"Unapping {amount} Ghost from Public.")
                txid = convertPublicToAnon(round(float(amount), 8), inputs)
                zapLog("UNZAP", f"jobID: {jobID} Unzapped {amount} GHOST from PUBLIC\nTXID: {txid}")
                db().setCurrentZapAmount(jobType, db().getCurrentZapAmount(jobType) + amount)
                db().setLastZap(jobType, timeNow)
                db().setNextZap(jobType, int(timeNow + nextTime))
                if getAvailablePublic(True) <= 0:
                    zapLog("UNZAP",
                           f"jobID: {jobID} Successfully Unzapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                    print(f"Successfully Unzapped {db().getCurrentZapAmount(jobType)} Ghost\nJob Complete!")
                    db().removeJob(jobType)
                    sys.exit()


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
        print(f"7: Secure Unzap")
        print("\n")
        print(f"Available Public: {getAvailablePublic()}")
        print(f"Available Anon: {getAvailableAnon()}")
        wallet = db().getWalletName()
        if wallet == "":
            wallet = "[Default Wallet]"
        print(f"Current Wallet: {wallet}")
        print("\n")
        print(f"8: Change Wallet")
        print(f"9: Set new Extended Public Key")
        print(f"10: Exit")
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
            setJob(int(ans))
            break
        elif ans == '8':
            db().setWalletName(None)
            db().setStealthAddr(None)
            checkWallet()
            if isEncrypted():
                print(f"Encrypted wallet found!")
                getWalletPassword()
        elif ans == '9':
            db().setExtKey(None)
            getExtKey()
        elif ans == '10':
            print(f"Goodbye")
            time.sleep(2)
            sys.exit()
        else:
            print("Invalid Response.")
            input("Press Enter to continue...")
    startJob()


def startJob():
    while True:
        job = db().getJobs()
        if job == []:
            input(f"No active jobs found. Press Enter to exit.")
            sys.exit()
        processJobs()
        job = db().getJobs()
        if job == []:
            input(f"No active jobs found. Press Enter to exit.")
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
        input(f"Failed to connect to ghostd! Press Enter to exit.")
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

