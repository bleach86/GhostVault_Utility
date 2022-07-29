# GhostVault_Utility
Zap Utility for GhostVault

***
Getting Started
***

 
Prerequisites 

- ghost-desktop v2.0.11 or better [Link](https://github.com/ghost-coin/ghost-desktop/releases/latest)

or

-ghost-core v0.21.1.10 or better [Link](https://github.com/ghost-coin/ghost-core/releases/latest)

- GhostVault v1.2 or better [Link](https://github.com/ghost-coin/GhostVault)

***
Setting config. For ghost-qt only
***

Start by starting ghost-qt and make sure it is fully synced with the ghost network. 

Once synced, click on `Settings` on the menu bar, then select `Options...`

In the options window, on the bottom left click the button that says `Open Configuration File`.

In the file it opens, add the line `server=1` then save and exit.

Now close ghost-qt and then relaunch it.
***

How to run the software
***

Start by downloading and extracting the [Latest Release](https://github.com/ghost-coin/GhostVault_Utility/releases/latest)


Start your ghost wallet and make sure it is synced with the ghost network.

On Windows or Mac, you can just click the executable, GZU.exe or GZU.app,  to launch. 

When you click on the executable, and a cmd window will open with the GZU running in it.

On Linux, a terminal window may not open when clicked. If this is the case you will need to open a terminal then either navigate to the folder with the executable in it, or you will need to drag the executable into the terminal window.

If you wish to navigate using the cd command, it would look as follows if you extracted the zip into the Downloads directory. 

```
cd ~/Downloads/GhostVault_Utility-linux/
```

Then you would run it by doing the following.

```
./GZU
```

![alt text](https://github.com/bleach86/GhostVault_Utility/blob/main/images/first_run.png?raw=true)

Now that GZU is running, it will locate the ghost-cli binary and check that ghostd is running. If that is all good, it will ask you to input the name of the wallet that you want to use.

The name is case sensitive and must match the name exactly.

If you use the wallet called Default Wallet, you can either leave the name blank or enter `Default Wallet`.

This can be changed later.

If the wallet that you choose is encrypted, you will be prompted for your password. The password is stored in RAM only, and must be re-entered each time you launch GZU.

![alt text](https://github.com/bleach86/GhostVault_Utility/blob/main/images/pubkey.png?raw=true)

After you enter the correct password, you will be prompted for the extended public key for your GhostVault.

To get the extended public key (pubkey), start by logging into your GhostVault using Putty or on a new terminal window.

Once logged in, navigate to the GhostVault directory as follows.

```
cd ~/GhostVault/
```

Now check that you are in GhostVault v1.2 or later 

```
python3 ghostVault.py status
```

If you are not up to date, update GhsotVault using the update command.

```
python3 ghostVault.py update
```

If your pubkey was generated in GhostVault version prior to 1.2 or if you are not sure, generate a new on with the following command.

```
python3 ghostVault.py newextkey
```

This may take a few minutes as it is generating the keys.

If you have previously generated keys using GhostVault v1.2 or later, then you can do the following.

```
python3 ghostVault.py showextkey
```

Once you get the key, paste it into GZU.

![alt text](https://github.com/bleach86/GhostVault_Utility/blob/main/images/menu.png?raw=true)

You will now be presented with the Task Selection Menu.

The amounts listed as available do not include currently staking coins. If you wish to zap them, you must first unzap them.

Options 1-3 are the same as options 4-6.
The difference being that in options 1-3 it will zap the entire applical balance, whereas with options 4-6 you will be able to choose the amount of the applicable ballance that will be zapped.

When you choose a zap option, it will ask you if you want to use GVR mode. 

If you select to use GVR mode, then your zaps will be broken into multiples of 20k so that they are eligible for GVR.

Every new zap will be in a new staking address. There will be a file generated with each GVR compatible address for that zap job in it.

For the purpose of zapping, you muse ensure that you have one extra ghost per vet. So if you have 5 vets, you would need to have 100,000 Ghost plus and additional 5 Ghost for a total of 100,005.

If you have less than 1 extra per vet, then your zapps run the risk of being lower than 20k after fees.

If you choose not to use GVR mode, then your zapps are broken up into groups of 1500 Ghost.

Options 1 and 3 are the most preferred ways to zap as that is the most secure.

When using options 1 or 3 all of the coins that you choose to zap from public are first send to ANON. Then all zaps are done from ANON except for GVR zaps of 20001, they will be sent to back to public first, then zapped from there.

All zapps will have a random amount of time between them of up to 2.5 hours.

This means that the entire zap process can take many hours or even days depending on which mode used and the amount being zapped.

Since this takes so long, you are able to stop the GZU at any time, and restart it later. It will remember where it left off and pick up from there.

Your ghost wallet and GZU need to be running throughout the entire zap process.

Option 7 is for securely and privately unstaking coins. The GZU will unstake coins by sending them to anon in by grouping all staking coins on the same address together. There will be a random time up to 2.5 hours between unstake transactions.
