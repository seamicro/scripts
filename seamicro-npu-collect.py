#!/usr/bin/python

import getopt
import re
import sys
import paramiko

latancy = { }
nic_number = ''
hostname = ''
server_spec = ''
server_num = 0


# Default options
#------
SMuser = 'admin'
SMpassword = 'seamicro'
#------


#pre populate dict
for i in range(0,512):
     latancy[i] = 0


def usage():
     print """usage: %s <chassis_hostname>""" % sys.argv[0]
     sys.exit(1)


try:
     options, args = getopt.getopt(sys.argv[1:], 'n:')
except getopt.error:
     usage()


if args:
     [hostname] = args
else:
     usage()


if not (hostname):
     usage()


ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy())
ssh.load_system_host_keys()
ssh.connect(hostname, username=SMuser, password=SMpassword)




#print Timestamp from chassis
stdin, stdout, stderr = ssh.exec_command('en;show clock')
print stdout.readlines()[0].strip()


#start a counter for the number of loops have been run
sequencenum = 0


#print the header
#for i in range(0,512):
#     print str(i) + ",",

regAddrs = ["51b2","51b5","51b8","51bb","51b3","51c1"]


for i in regAddrs:
     #Start by clearing the counters on the chassis
     cmd1="en;unhide debug;debug smob peek node 0-511 regAddr " + i + " | include MAX"
     stdin, stdout, stderr = ssh.exec_command(cmd1)


     lines = stdout.readlines()
     for line in lines:
          line = line.strip()
          line = re.sub('\s+', ' ', line)
          latancy[server_num] = (latancy[server_num] + (int(line.split()[2],0) / 0x13848))
          server_num = server_num + 1
     server_num=0


for line in latancy.items():
     print str(line[1]) + ",",


print ""




#Gather NPU stats
stdin, stdout, stderr = ssh.exec_command('en;unhide debug;debug npu dump-queue start 0 count 600')
lines = stdout.readlines()
for line in lines:
     print line,
