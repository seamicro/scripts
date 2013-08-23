#!/usr/bin/python


# Server  NIC   Vlan  DDNSName     IP              MAC            #VDisks  Status
# ---------------------------------------------------------------------------------
# 100   0      -   -                  10.74.1.100     0022.991f.0310  2      up   
# 100   1      -   -                  10.74.0.16      0022.991f.0311  -      -    

import getopt, pprint, re, sys
import paramiko

macs = { }
nic_number = ''
hostname = ''
server_spec = ''

def usage():
	print """usage: %s [-n 0/1] <chassis_hostname> <server spec>""" % sys.argv[0]
	sys.exit(1)


def reformat_mac( mac ):
	mac = re.sub('\W', '', mac)
	chars = [ c for c in mac ]
	chars.insert(2, ':')
	chars.insert(5, ':')
	chars.insert(8, ':')
	chars.insert(11, ':')
	chars.insert(14, ':')
	mac = ''.join(chars)
	return mac

try:
	options, args = getopt.getopt(sys.argv[1:], 'n:')
except getopt.error:
	usage()

for o,a in options: 
	if o == '-n':
	        nic_number = a

if args and len(args) == 2:
	[hostname, server_spec] = args
else:
	usage()

if not (hostname or server_spec):
	usage()

if hostname == '-':
	lines = sys.stdin.readlines()
else:
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
	ssh.connect(hostname, username='admin', password='seamicro')
	stdin, stdout, stderr = ssh.exec_command('show server summary %s' % server_spec)
	lines = stdout.readlines()
	ssh.close()

lines = filter(lambda x: not (x.startswith('-') or x.startswith('Server')), lines)

for line in lines:
	# get rid of extra spaces to make splitting easier.
	line = line.strip()
	line = re.sub('not assigned', 'not_assigned', line)
	line = re.sub('\s+', ' ', line)
	
#	32      0      -     not assigned    0022.9939.0402  1	   down 

#	(id, nic, vlan, name, ip, mac, n_vdisks, status) = re.split('\s+', line)
#	print re.split('\s+', line)
#	(id, nic, name, ip, mac, n_vdisks, status) = re.split('\s+', line)
	try:
		(id, nic, ip, mac, n_vdisks, status) = re.split('\s+', line)
	except ValueError as e:
		(id, nic, vlan, ddnsname, ip, mac, n_vdisks, status) = re.split('\s+', line)
	id = int(id)
	# if we're looking for a specific nic, ignore ones that are not it.
	if nic_number and nic_number != nic: continue
	mac = reformat_mac(mac)
	
	if macs.has_key(id):
		if mac not in macs[id]:
			macs[id].append(mac)
	else:
		macs[id] = [ mac ]

for id, mac in sorted(macs.items()):
	print id, mac[0]

