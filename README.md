# Release 2.0
The latest release of the Polycraft Tournament Manager includes major updates to our POGO task design. 
Please see this change log for changes in the POGO task.

HUGA Task update coming soon.

## Key Updates
### Release 1.3
* New Environment variable PAL_FPS to set game speed frames per second. This can increase your agent's actions per second and greatly decrease training time. By default, this is set to 20 and the maximum is 1000. However, depending on the machine, you may not get the expected frames per second. The frames per second will also depend on what commands you are using. Some commands take 1 frame to perform and others take 2.
### Release 1.2
* New Environment variable SENSE_SCREEN_FORMAT to set default image compression format. This can directly affect performance on different systems when the agent calls SENSE_SCREEN. Default is PNG, but on many systems PNG compression can take many ms to process. When this process takes more than 50ms it can slow down game performance if called on every action.  It is recommended to test different options to increase performance. Options include: {"PNG", "BMP", "JPEG", "JPG", "WBMP", "GIF"}.
* New HUGA lvl 0 novelties
    * Wall and floor textures are now randomly picked between 32 different variations to give training diversity and better distinctions between walls and floors for visual agents.
    * Pathways in walls are now randomly moved around and there will be between 3 and 5 pathways total.
### Release 1.1
* config.py (new file) now contains key configurations necessary to launch tournaments. These configurations can be edited through command line arguments, enabling other scripts to "git pull" & execute this code without having to make edits to any files.
* Game JSONs are now read from a directory containing a "Tournament" of game JSONs. 
    * JSON zips of 10, 100, & 1000 game tournaments __will be provided separately__. Usage instructions will be attached.
    * JSONs must adhere to a strict naming convention of _\*\_Gxxxx\_*.json_ where XX indicates the game number. 
    * Tournaments are played in game order from least to greatest
* Log Files are created for all STDOUT/STDERR messages across three threads. They are saved in PolycraftAIGym/Logs/:
    * PAL_log contains all of the output from the PAL (Polycraft) thread
    * Agent_log contains all printed messages from the AI Agent
    * Debug_log contains messages generated by the LaunchTournament.py script (main thread)
* New setup folder includes UNIX commands for installing all system dependencies & an updated requirements.txt correctly includes all necessary packages to run this script

# Installation:
## 1. Ubuntu
1. If you haven't already, pull this branch of the repository to your work directory:
    `git clone -b release_1.3 --single-branch https://github.com/StephenGss/pal.git`
1. For a fresh install:
    * navigate to polycraft/pal/setup/ and execute `./setup_linux_shortened.sh` (user will need sudo permissions to wget JAVA).
    * We have also provided our current setup scripts in that folder (they include a few additional packages enabling us to upload tournament results to SQL) for your reference.
2. For a pre-existing environment, review the apt-get commands in _setup_linux_shortened.sh_ and execute as-needed.
3. pip install all requirements. We recommend using a package manager like conda
   * `conda create -name pal_manager python=3.8 # or use your favorite venv`
   * `cd polycraft/pal/ && python -m pip install -r requirements.txt`
4. unzip and move to a known location the zipped tournament JSONs. We recommend testing the setup with a VIRGIN No Novelty variant

##### Possible issues
* The last command, `./gradlew runclient` may fail with the following as part of the error message:
	`Could not determine java version from '#.#.#'.`
    * Solution: Run `sudo update-alternatives --config java`
	* Choose the option with jdk-8
* The last command, `./gradlew runclient` may fail with the following as part of the error message:
	`Process 'command '/usr/lib/jvm/java-8-openjdk-amd64/bin/java'' finished with non-zero exit value 1`
	* Check the stack trace for mention of `Can't connect to X11 window server using 'localhost:0.0' as the value of the DISPLAY variable.`
	* Agents that will use SENSE_SCREEN must have systems with video cards or have the xvfb package installed. Please see 
	* Other agents may be able to run on these systems, but solutions to this issue are based on your local configuration.


## 2. Windows
* Key dependency: Java JDK 8
	* https://www.oracle.com/java/technologies/javase/javase-jdk8-downloads.html
	* Or as appropriate with Oracle
	* You may have to sign in and create an account.
* Get Git: https://git-scm.com/downloads
	* Download and install with all defaults
* Clone repo (if repo is not already cloned): 
	* Navigate to target folder for installing Polycraft AI Lab
	* Run command prompt/PowerShell
	* git clone https://github.com/StephenGss/PAL.git
* Pull updates (if repo is already cloned):

# Launching & Running:
The main program is found in the PolycraftAIGym folder, called `LaunchTournament.py`

A key release update has created a new file, `config.py` containing all config variables necessary 
for program execution (previously, these were variables simply declared in this file)

These variables can be edited directly in that file. However, LaunchTournament.py can also take in command line 
arguments to adjust the defaults.

These parameters must be adjusted for each user's system to enable the Tournament Manager to run. Please read carefully
the sections below on parameter details and adjust to match your folder structure. 

After setting configs, please adjust runtime settings by:
1. Changing to PolycraftAIGym as the work directory: <br> `cd /path/to/polycraft/pal/PolycraftAIGym` 
2. If your Operating System is __Windows__, Modify PAL/PolycraftAIGym/LaunchTournament.py's 
if __name__ == __main__(): function (found at the very bottom) as follows:<br>
    * pal = LaunchTournament('WIN')
    * passing in "UNIX" (default) will run the _UNIX version of the agent command and 
    PAL command in the CONFIG file as well as tweak the expectations for line endings to not have carriage returns
3. To execute: <br>
`python LaunchTournament.py {-h, -i, etc}` (run the manager, optionally passing in flags listed below)

### Setting Config Variables

Below is an exhaustive list of variables defined in config.py and their associated CLI flag to override their values (where applicable).

Critical Parameters requiring edits before runtime are:
* AGENT_COMMAND/AGENT_COMMAND_UNIX
* PAL_COMMAND/PAL_COMMAND_UNIX
* AGENT_DIRECTORY
* GAMES_FOLDER
    * Note: please use one of the pre-created tournaments (after unzipping them). 
    The script reads through this folder in a random order and looks for a specific naming pattern for each game JSON to sort them appropriately and 
    will raise a ValueError if the pattern is not found.
* GAME_COUNT 

| Parameter  | CLI flag | Comments |
|-----------|--------------------------|--------------|
|MAX_STEP_COST      | N/A (see file)           | Maximum step cost before a game is ended - set to 1,000,000 |
|PAL_COMMAND        | N/A (see file)          | Windows command to execute the polycraft client               |
|PAL_COMMAND_UNIX   | N/A (see file)        | Linux command to run polycraft. |
|MAX_TIME           | `-i <time>` | maximum time in seconds for a given game (default: 300)|
|TOURNAMENT_ID      | `-t <name>` | name of the tournament |
|AGENT_DIRECTORY    | `-d <../agent/>` | work directory where AGENT_COMMAND_UNIX gets executed |
|AGENT_COMMAND_UNIX | `-x <bash cmd>` | command necessary to launch the Agent AI |
|AGENT_COMMAND      | `-x <windows cmd>` | -x modifies both parameters (OS-agnostic) |
|AGENT_ID           | `-a <agent_name>` | name of agent |
|GAME_COUNT         | `-c <count>`        | number of games to be played. If count > number of games available in the games folder, all games are played.
|GAMES_FOLDER       | `-g <games/>` | location of folder containing tournament JSONs. |

__NOTE__: the PAL_COMMAND_UNIX must be adjusted away from default to run on a computer with a graphics card & display attached. Please 
see the related comment in the config.py file, as the appropriate UNIX command (`./gradlew runclient`).

### Running with CLI Commands 
Here is an example of running the manager with flags passed:

`>> cd /path/to/polycraft/pal/PolycraftAIGym`<br>
`>> python LaunchTournament.py -t "Tournament1" -a "My_Agent" -d "../agents/my_agent_folder/"`<br>
    `... -x "./launch_my_agent.sh" -g "../path/to/tournament/jsons/" -c 10 -i 600`

Will launch a tournament named _"Tournament1"_ using _"My_Agent"_ found in _"../agents/my_agent_folder/"_ executed with
_"launch_my_agent.sh"_ playing the first _10_ games (sorted by the name of the JSON - see below) found in
folder _"../path/to/tournament/jsons/"_ with 600 seconds of time per game.


## Interacting with Polycraft AI Lab, platform independent
* Run PAL -> PolycraftAIGym -> testSocket.py
	* Python is available at python.org. It is not required to run or connect to PAL, but it is required to run the demo script.
	* The python console will accept user input.
	* Send "START" to put PAL in a state where it can receive communications
		* Wait for the Polycraft window to change to a plain field
	* Send "RESET domain ../available_levels/pogo_nonov.json
		* Or other level as needed. See Tasks and Novelties
	* Send API sense commands or action commands. Such as:
		* "SENSE_ALL NONAV" to get information about the player's environment
		* "MOVE W" to move forward
		* "BREAK_BLOCK" to break the block immediately in front of the player
		* Many more commands described in Polycraft Bot API section

# Polycraft Bot API
The Polycraft World AI API consists of 28 total different API commands at Release 1.5.0 on 5.4.2020. These commands are broken down into SYSTEM commands, DEV commands, and GAME commands. The GAME commands are further divided into MOVE commands, SENSE commands, INTERACT commands.
## SYSTEM commands: (2 total)
* **START**  
	* no args ever used | called once to start tournaments
* **RESET** domain ../available_tests/pogo_nonov.json
	* the base pogo experiment
* **RESET** domain ../available_tests/hg_nonov.json
	* the base hunter-gatherer experiment
* The following function on the cloud virtual machines for the test harness:
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_1/trial_1/hg_1.1.json
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_1/trial_1000/hg_1.1000.json
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_100/trial_1/hg_100.1.json
	* **RESET** -d ../dry-run/hunger-gatherer/tournament_100/trial_1000/hg_100.1000.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_1/trial_1000/pogo_1.1.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_1/trial_1000/pogo_1.1000.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_100/trial_1000/pogo_100.1.json
	* **RESET** -d ../dry-run/pogo-creation/tournament_100/trial_1000/pogo_100.1000.json
		* -d (domain) path to .json novelty transform 
		* called 1,000 times per tournament to start a new trial
		* different tournaments will run using cloned TA2 agents on different cloud machines
		* novelty will be pre-set in the .jsons and not generated at run-time

## DEV commands: (4 total)
* Dev commands must be enabled by setting a client virtual machine argument: "-Ddev=True" Details on setting this outside of a development environment are still being worked out, as solutions are fickle and system dependent. Please contact us if you need these commands.
* **CHAT** "Hello world."
* **CHAT** /give @p minecraft:stick
	* not cuurently used in evaluation Tournaments, but active for debugging/training/development
* The following function on the cloud virtual machine for the test harness.
	* **CREATE_NOVELTY_VARIATIONS** -d ../available_tests/hg_2.X.json -s 42 -i 60
	* **CREATE_NOVELTY_VARIATIONS** -d ../ available_tests/pogo_2.X.json -s -37489 -i 10
		* Novelty generators for level zero (rearranging objects) are not included currently but will be soon
		* not used in DRY-RUN Tournaments, but provides agents in training a simple way to try out different seeds and different intensities during training within the same tournament
		* -d (domain) path to .json novelty transform -s (seed) arbitrary INT -i (intensity) INT 0-100
		* generates novelty at run time for training purposes
* **SPEED** 30
	* not used in DRY-RUN Tournaments, but sets the game speed in ticks per sec (default 20)
* **TELEPORT** 20 4 21 90 0
	* not to be used in DRY-RUN Tournaments, but allows setting player location and view direction.
	* Parameters: [x] [y] [z] [yaw] [pitch]

## GAME commands - MOVE commands: (7 total)
* **SMOOTH_MOVE** w
* **SMOOTH_MOVE** a
* **SMOOTH_MOVE** d
* **SMOOTH_MOVE** x
	* moves 1 meter forward (w), left (a), right (d) or back (x) continuously
* **SMOOTH_MOVE** q
* **SMOOTH_MOVE** e
* **SMOOTH_MOVE** z
* **SMOOTH_MOVE** c
	* moves sqrt (2) distance diagonally with (q,e,z,c)
* **MOVE** w
	* parameters: w,a,d,x, or q,e,z,c as in SMOOTH_MOVE (does not interpolate during move)
* **SMOOTH_TURN** 15
	* alters player's horizontal facing direction (yaw) in 15-degree increments
* **TURN** -15
	* alters player's horizontal facing direction (yaw) in 15-degree increments (no interpolation)
* **SMOOTH_TILT** 90
* **SMOOTH_TILT** FORWARD
* **SMOOTH_TILT** DOWN
* **SMOOTH_TILT** UP
	* alters player's vertical facing direction (pitch) in 15-degree increments
	* three higher level commands set player looking forward (0) or down (-90) or up (90)
* **TILT** -90
	* alters player's vertical facing direction (pitch) in 15-degree increments (no interpolation)
	* also can be parameterized with FORWARD, DOWN and UP
* **TP_TO** 20,4,21 
	* as in TELEPORT without adjusting yaw and pitch
* **TP_TO** 20,4,21 2
	* as in teleport without adjusting yaw and pitch, but with an offset straight backwards
	* offset must yield allowable move_to location or command fails
* **TP_TO** 7101
	* teleports to the location of an entity with entity_ID "7101"

## GAME commands - SENSE commands: (8 total)
* **CHECK_COST**
	* returns the stepCost incurred since the last RESET command
* **REPORT_BLOCK** 0 6 2
	* special call for hg domain for denser rewards | reports whether a floor block is special or not
	* params: [0 = normal block, 1 = macguffin, 2 = target] [x][z]
* **REPORT_NOVELTY**
	* indicates that you have detected novelty with optional parameters | [-l novelty level]
	* [-c confidence interval 0f:100f] [-g game novelty was detected] [-m user-defined message]
* **SENSE_INVENTORY**
	* returns contents of player inventory in .json format
* **SENSE_LOCATIONS**
	* returns senseable world environment (blocks, entities and locations) as .json
* **SENSE_RECIPES**
	* Returns the list of recipes available in the experiment
* **SENSE_SCREEN**
	* Returns pixels sent to the display output window, in the form of a string listing an array of integers
* **SENSE_ALL**
* **SENSE_ALL NONAV**
	* returns inventory, recipe and location information in .json | NONAV parameters omits information which is not needed for agents that do not navigate the world

## GAME commands - INTERACT commands: (9 total)

* **SELECT_ITEM** polycraft:wooden_pogo_stick
	* sets a specific item from your inventory in your hand as the active item (e.g. tool or block)
* **USE**
	* to open doors
	* unlock safes
	* etc.
* **BREAK_BLOCK**
	* breaks block directly in front of player with selected item
	* selected item and block type yield stepCost of action
* **CRAFT** 1 minecraft:log 0 0 0
	* note that CRAFT must be followed by a "1"
	* crafts 4 Planks
* **CRAFT** 1 minecraft:planks 0 minecraft:planks 0
	* crafts 4 Sticks 
* **CRAFT** 1 minecraft:planks minecraft:planks 0 minecraft:planks minecraft:stick 0 0 minecraft:stick  0
	* crafts a Wooden Axe 
* **CRAFT** 1 minecraft:planks minecraft:stick minecraft:planks minecraft:planks 0 minecraft:planks 0 minecraft:planks 0
	* crafts a Tree Tap
* **CRAFT** 1 minecraft:stick minecraft:stick minecraft:stick minecraft:planks minecraft:stick minecraft:planks 0 polycraft:sack_polyisoprene_pellets 0
	* crafts a Wooden Pogo Stick
* **COLLECT**
	* collect available items from container blocks or inventories
* **PLACE \[item name\]**
	* will be added after dry-run. NOT in release 1.5.0
* **PLACE_TREE_TAP**
	* calls PLACE_BLOCK polycraft:tree_tap (and processes extra rules)
* **PLACE_CRAFTING_TABLE**
	* calls PLACE_BLOCK minecraft:crafting_table  (and processes extra rules)
* **PLACE_MACGUFFIN**
	* calls PLACE_BLOCK polycraft:macguffin (and processes extra rules)
* **DELETE \[item name\]**
	* Deletes the item in player's inventory
* **TRADE \[entity id\] \[item 1\] \[qty\] \[item 2\] \[qty\] \[item 3\] \[qty\] \[item 4\] \[qty\] \[item 5\] \[qty\]
	* Trade with trader entities
* **INTERACT \[entity id\]** 
	* Interact with an entity. Ex. sense the recipes available for a trader agent
