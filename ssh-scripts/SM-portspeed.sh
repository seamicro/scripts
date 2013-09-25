#!/bin/sh

# Have issues with this script? Send any questions, comments, or complaints to andrew.mander@amd.com. I'm not a developer so please forgive some of the horrendous code below.

# Description: Sets the port speed of individual fabric endpoints (NICs) - currently only does eth0. Tested on CentOS 6.x - not guaranteed to work elsewhere.

# Dependencies: A SeaMicro chassis, Net Cat (NC).

# Global Variables
APP='SM-portspeed.sh'
GETMAC="/tmp/getmac.out"
IPADDR=""
LOCALHOST=`hostname`
MACLIST="/tmp/maclist.out"
ME=`id | cut -f2 -d'(' | cut -f1 -d')'`
NC="/usr/bin/nc"
PINGME='andrew.mander@amd.com'
SPEEDS="/tmp/speeds.out"
# Fabric Rates
FASTETHERNOIPG="0x00000199"
FASTETHER="0x00140199"
GIGETHER="0x00141000"

# SeaMicro Chassis Login - not sure why password is specified since it can't be passed via standard SSH.
USER="admin"
PASS="seamicro"

## Functions below

# Checks to see if SSH is up on the other end
checkPort () {
	$NC -vz $HOST 22 2>&1 > /dev/null	
}

# Interface report - comes back with interface stats
intReport () {
	echo -e "\n100Mbps Interfaces: `grep -vi "offset\|mask\|---" $SPEEDS | grep -i "$FASTETHERNOIPG\|$FASTETHER" | wc -l`"
	echo -e "1000Mbps Interfaces: `grep -vi "offset\|mask\|---" $SPEEDS | grep -i "$GIGETHER" | wc -l`"
	echo -e "Other: `grep -i FAB_ETH_TX_RATE_LIMIT $SPEEDS | grep -vi "offset\|mask\|---\|$FASTETHERNOIPG\|$FASTETHER\|$GIGETHER" | wc -l `\n"
}

# Checking to see if net cat is executable and warns then exits if it isn't
if [[ ! -x $NC ]]; then
	echo "WARNING: /usr/bin/nc not executable." 
	exit 1
fi

# Checking the number of command arguments. If equal to or greater than 3, it moves on. If not, you see this:
if [[ $# < 3 ]]; then
	echo -e "\n[ Usage Example: ]"
        echo -e "\n$APP <chassis IP> <show/edit> <server ID (0-63) or all> <edit only: port speed - 100 or 1000 (mb/s)>\n"
        exit 1
fi

# Converting input variables into human readable ones.
HOST="$1"
SHOWEDIT="$2"
SERVER="$3"
SPEED="$4"

# Show the current port speed
if [[ "$SHOWEDIT" = "show" ]]; then
	if [[ "$SERVER" = "all" ]]; then
		SMOBID="0-511"
	elif ! [[ "$SERVER" -lt 0 || "$SERVER" -gt 63 ]]; then
		# The fabric mapping below for eth0. Starts at server 0 and goes up to server 63
		set 2 10 66 74 450 458 130 138 386 394 194 202 322 330 258 266 26 18 90 82 474 466 154 146 410 402 218 210 346 338 282 274 34 42 98 106 482 490 162 170 418 426 226 234 354 362 290 298 58 50 122 114 506 498 186 178 442 434 250 242 378 370 314 306
		SERVEROFFSET=$(($SERVER+1))
		SMOBID=`echo ${!SERVEROFFSET}`
	else
		echo -e "\nThe server target variable is not valid - please specify 'all' or a server ID from 0-63."
		echo -e "\nExample: \"$APP $1 show all\""
		echo ""
		exit 1
	fi

# Checking to see if the remote host responds to an SSH connection
	checkPort
	if ! [[ $? = "0" ]]; then
		echo -e "\nI tried connecting to: $HOST via SSH (port 22) but it failed. Please investigate.\n"
		exit 1
	fi

# Logging into the chassis and displaying the port speed. Converting the hex values to something human readable
	echo -e "\nConnecting to SERVER: $SERVER, Fabric Node ID: $SMOBID" | tee $SPEEDS
	ssh -l $USER $HOST "en ; unhide debug ; debug smob peek node $SMOBID regAddr 100a" >> $SPEEDS
	grep -vi "Connecting\|offset\|mask\|---" $SPEEDS | sed "s/$GIGETHER/LINK RATE: 1000 Mbps/g;s/FASTETHERNOIPG/LINK RATE: 100 Mbps - Non-IPG/g;s/$FASTETHER/LINK RATE: 100 Mbps/g"
	intReport
		exit 0

# Edit the current port speed
	elif [[ "$SHOWEDIT" = "edit" ]]; then
		echo -e "\nEntering 'EDIT' mode...\n"
	else
		echo  -e "\nPlease enter a valid option - 'show' or 'edit'."
		exit 1
fi

# Need to know the proposed port speed
if [[ "$SPEED" = "100" ]]; then
	echo "You selected: 100Mb/s"
	#USERMASK="199" -- OLD non-IPG mode
	USERMASK="140199"
elif [[ "$SPEED" = "1000" ]]; then
	echo "You selected: 1000Mb/s"
	USERMASK="141000"
else
	echo -e "\nPlease enter a valid rate variable - 100 or 1000."
	echo -e "\nExample: \"$APP $1 edit 53 100\""
	echo -e "(The example above sets server53's NIC to 100Mbps)\n" 
exit 1
fi 

# Scope of the edits
if [[ "$SERVER" = "all" ]]; then
	SMOBID="0-511"
elif ! [[ "$SERVER" -lt 0 || "$SERVER" -gt 63 ]]; then
	# The fabric mapping below. 
	set 2 10 66 74 450 458 130 138 386 394 194 202 322 330 258 266 26 18 90 82 474 466 154 146 410 402 218 210 346 338 282 274 34 42 98 106 482 490 162 170 418 426 226 234 354 362 290 298 58 50 122 114 506 498 186 178 442 434 250 242 378 370 314 306
	SERVEROFFSET=$(($SERVER+1))
	SMOBID=`echo ${!SERVEROFFSET}`
else	
	echo -e "\nScope unknown. Exiting."
	exit 1
fi

#Logging into the chassis to make the changes.
echo -e "\nConnecting to SERVER: $SERVER, Fabric Node ID: $SMOBID" | tee $SPEEDS
checkPort
ssh -l $USER $HOST "en ; unhide debug ; debug smob poke node $SMOBID regAddr 100a value $USERMASK ; debug smob peek node $SMOBID regAddr 100a" > $SPEEDS
grep -vi "offset\|mask\|---" $SPEEDS | sed "s/$GIGETHER/LINK RATE: 1000 Mbps/g;s/$FASTETHERNOIPG/LINK RATE: 100 Mbps - Non-IPG/g;s/$FASTETHER/LINK RATE: 100 Mbps/g"
