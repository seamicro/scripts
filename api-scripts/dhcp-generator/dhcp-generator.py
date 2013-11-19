#!/usr/bin/python

import sys
import argparse
import netaddr
from seamicro_api import SeaMicroAPI

HOSTNAME_FORMAT="server%d"
IP_ADDRESS_FORMAT="192.168.1.%d"
GATEWAY = "192.168.1.1"
COBBLER_SYSTEM_TEMPLATE = "sudo cobbler system add --name %(name)s --mac %(serverMacAddr)s --ip-address %(ip_address)s --netmask %(netmask)s --gateway %(gateway)s --hostname %(name)s --dns-name %(name)s  --profile %(profile)s --interface eth0"
ISC_DHCP_TEMPLATE = "host %(name)s { fixed-address %(ip_address)s; hardware ethernet %(serverMacAddr)s;}"

def func(x,y):
	"""Comparison function for use with builtin 'sorted'. Sorts the server serverId
	   in numeric order."""
	ccard_x = int(x['serverId'].split('/')[0])
	ccard_y = int(y['serverId'].split('/')[0])
	return ccard_x - ccard_y

def argparser():
	parser = argparse.ArgumentParser(description='''\
		Generate commands for cobbler and configuration lines for isc-dhcpd from SeaMicro MAC addresses.''')

	parser.add_argument('chassis',
		help='The SeaMicro chassis hostname or IP address.')

	action_group = parser.add_mutually_exclusive_group(required=True)
	action_group.add_argument('--cobbler', action='store_true',
		help='Generate cobbler "system add" commands.')

	action_group.add_argument('--dhcpd', action='store_true',
		help='Generate fixed-address lines suitable for ISC dhcpd.')

	parser.add_argument('--cobbler-profile', action='store',
		help='The cobbler profile to associate with all servers.')

	parser.add_argument('--username', action='store', default='admin',
		help='The chassis management username.')

	parser.add_argument('--password', action='store', default='seamicro',
		help='The chassis management password.')

	parser.add_argument('--domain', action='store', default='local',
		help='The DNS domain name to be supplied to all servers.')

	parser.add_argument('--netmask', action='store', default='255.255.255.0',
		help='The netmask the DHCP server should provide.')

	parser.add_argument('--gateway', action='store', type=netaddr.IPAddress,
		help='''The default gateway the DHCP server should provide.
		        If not specified, we will choose the first IP in the subnet.''')

	parser.add_argument('--first-ip', action='store', type=netaddr.IPAddress, default='192.168.1.100',
		help='The IP that should be assigned to the first server. Subsequent servers will increment by one.')

	parser.add_argument('--base-name', action='store', default='server-',
		help='The base name for servers. Each server will have the ccard number appended.')

	args = parser.parse_args()

	if args.cobbler and args.cobbler_profile == None:
		print >>sys.stderr, "You must indicate what cobbler profile you want to associate your systems with."
		parser.print_help()
		sys.exit(1)

	return args

def render_template(servers, args, template):
	commands = [ ]
	network = netaddr.IPNetwork('%s/%s' % (args.first_ip, args.netmask))

	if args.gateway == None:
		args.gateway = netaddr.IPAddress(network.first + 1)

	subnets = list(network.subnet(network.prefixlen))

	for server in servers:
		ccard = int(server['serverId'].split('/')[0])
		hostname = HOSTNAME_FORMAT % ccard
		ip_address = args.first_ip + ccard
		
		for subnet in subnets:
			if ip_address not in subnet:
				print >>sys.stderr, "The number of servers do not fit in the range provided. Either change the first-ip option, or use a larger subnet mask."
				sys.exit(1)

		server.update({ 'name': hostname, 'ip_address': ip_address, 'gateway': args.gateway, 'netmask': args.netmask })
		if args.cobbler_profile:
			server.update({ 'profile': args.cobbler_profile})

		commands.append(template % server)
	return commands

def main():
	args = argparser()

	api = SeaMicroAPI(hostname=args.chassis, verify_ssl=False)
	api.login(username=args.username, password=args.password)
	servers = api.servers_all()
	api.logout()

	server_nic_list = [ s for s in sorted(servers.values(), cmp=func) if s['serverNIC'] == '0' ]

	if args.cobbler:
		template = COBBLER_SYSTEM_TEMPLATE
	if args.dhcpd:
		template = ISC_DHCP_TEMPLATE

	for line in render_template(server_nic_list, args, template):
		print line

if __name__ == "__main__":
	main()