#!/usr/bin/env python


import datetime, getopt, getpass, os, re, sys, tarfile
try:
	import paramiko

except ImportError:
	print >>sys.stderr, "Please install the paramiko python module - 'pip install paramiko'"
	sys.exit(1)

hostname = ''
output_filenames = []

commands = ('show logging', 'show console', 'enable;show version', 'enable;show tech-support detail', 'enable;show inventory', 'enable;show redundancy')

def usage():
	print """usage: %s [-t] <chassis_hostname/ip> 
-t / tar and gzip output
""" % sys.argv[0]
	sys.exit(1)

try:
	options, args = getopt.getopt(sys.argv[1:], 'htpu:')
except getopt.error:
	usage()

tar = False
prompt_for_password = False
username = "admin"     # factory default username
password = "Egr03G"  # factory default password

for o,a in options: 
	if o == '-h':
	        usage()
	if o == '-t':
		tar = True
	if o == '-p':
		prompt_for_password = True
	if o == '-u':
		username = a

if args and len(args) == 1:
	[hostname] = args
else:
	usage()

if not hostname:
	usage()

if prompt_for_password:
	password = getpass.getpass("Password for %s@%s:" % (username, hostname))

if hostname == '-':
	lines = sys.stdin.readlines()
else:
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
	try:
		ssh.connect(hostname, username=username, password=password)
	except paramiko.AuthenticationException as ex:
		print >>sys.stderr, "Could not connect: %s" % ex
		sys.exit(1)
	except paramiko.BadAuthenticationType as ex:
		print >>sys.stderr, "The remote host doesn't allow password authentication: %s" % ex
		sys.exit(1)
	now = datetime.datetime.now()

	for command in commands:
		print "Executing '%s'" % command
		dir = "%s-%s" % (hostname, re.sub(':', '.', now.isoformat()))
		stdin, stdout, stderr = ssh.exec_command(command)
		try:
			os.mkdir(dir)
		except OSError, e:
			if e.errno == 17: # directory already exists...
				pass
			else:
				print >>sys.stderr, "Oops, problem creating output directory!"
				print >>sys.stderr, e.errno
				raise
		fn = "%s/%s" % (dir, re.sub('[\s+\W+]', '_', command))
		f = open(fn, 'w')
		f.write(stdout.read())
		output_filenames.append(fn)
		f.close()
		
	ssh.close()
	if tar:
		t = tarfile.open('%s-support-data.tar.gz' % dir, mode="w:gz")
		t.add(dir)	
		t.close()
		try:
			for (root, dirs, files) in os.walk(dir):
				[ os.unlink(os.path.join(root, f)) for f in files ]	
				[ os.rmdir(os.path.join(root, d)) for d in dirs ]
			os.rmdir(root)
		except OSError, e:
			print >>sys.stdderr, "Wrote tarball, but could not clean up working files. Sorry boss!"
			print e
			sys.exit(1)

print >>sys.stderr, "Wrote to ", output_filenames
