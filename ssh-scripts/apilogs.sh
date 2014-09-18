#!/bin/sh

# Questions? Comments? Suggestions? Email: andrew.mander@amd.com if you want to know how any of this works. My apologies to professional software developers for this abomination.

# Description: Helps end users look at the API logs on an AMD Seamicro SM15000 chassis, running > 3.5.0.0 firmware.

# Dependencies: Needs netcat, and a chassis with SSH keys set

# Variables below

CHASSIS="$1"
DATE=`date +%H:%M:%S`
LOGLOCATION="/var/log/rest_api_history.log"
OPTION="$2"
OUTPUTDIR="/dev/shm"
NC="/usr/bin/nc"
SHOWALLOUT="$OUTPUTDIR/$CHASSIS-RESTAPILOG-$DATE.out"

# Precheck Functions

# Checks to see if SSH is up on the other end
checkPort () {
        $NC -vz -w 5 $CHASSIS 22 2>&1 > /dev/null
        if ! [[ $? = "0" ]]; then
                echo -e "\nI tried connecting to: $CHASSIS via SSH (port 22) but it failed. Please investigate.\n"
                exit 1
        fi
}

# Checking to see if net cat is executable and warns then exits if it isn't
if [[ ! -x $NC ]]; then
        echo "WARNING: /usr/bin/nc not executable."
        exit 1
fi

# Directory checking
if [ ! -d "$OUTPUTDIR" ]; then
	echo "$OUTPUTDIR does not exist! Please modify the output directory."
	exit 1
fi

# Checking the number of command arguments. If equal to or greater than 2, it moves on. If not, you see this:
if [[ $# < 2 ]]; then
        echo -e "\n[ Usage Example: ]"
        echo -e "\n$APP <chassis IP> <showall/tail>\n"
        exit 1
fi

if [ $OPTION != "showall" -a $OPTION != "tail" ] ; then
	echo -e "\nPlease choose \"showall\" or \"tail\""
	exit 1
fi

# Checking to see if the chassis is live
checkPort

# Executing
if [[ $OPTION = "showall" ]]; then
	echo "The log output can be extensive so this may take time. We're going to save it to: $SHOWALLOUT."
	ssh -l root $CHASSIS "hostname ; cat $LOGLOCATION" > $SHOWALLOUT
	echo -e "Log output retrieved and placed into $SHOWALLOUT."
	exit 0
elif [[ $OPTION = "tail" ]]; then
	echo -e "Showing the live output via \"tail\". Saving output to $SHOWALLOUT.\n*** PRESS CTRL-C TO EXIT ***"
	ssh -l root $CHASSIS "hostname ; tail -f $LOGLOCATION" | tee $SHOWALLOUT
else
	echo "Not sure what happened."
	exit 1
fi
