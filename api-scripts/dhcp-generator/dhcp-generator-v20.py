"""
Simple script to query SM15K for server MACs and insert into DHCP server.

Reworked original dhcp-generator script to use python-seamicroclient & API 2.0
"""
#!/usr/bin/python

import sys
import argparse
import netaddr
from seamicroclient.v2 import client


COBBLER_SYSTEM_TEMPLATE = ("sudo cobbler system add \
			--name %(name)s \
			--mac %(macAddr)s \
			--ip-address %(ip_address)s \
			--netmask %(netmask)s \
			--gateway %(gateway)s \
			--hostname %(name)s \
			--dns-name %(name)s  \
			--profile %(profile)s \
			--interface eth0")
ISC_DHCP_TEMPLATE = ("host %(name)s \
		  { fixed-address \
		  %(ip_address)s; \
		  hardware ethernet \
		  %(macAddr)s;}")


def main():
    """."""
    args = parse_command_line_arguments()

    sm15k_chassis = client.Client(args.username, args.password, args.chassis)
    servers = sm15k_chassis.servers.list()
    server_nic_dict = {s.id:{"macAddr":s.nic['0']['macAddr']}
                        for s in servers}

    if args.cobbler:
        template = COBBLER_SYSTEM_TEMPLATE
    if args.dhcpd:
        template = ISC_DHCP_TEMPLATE

    for line in render_template(server_nic_dict, args, template):
        print line


def parse_command_line_arguments():
    """Parse."""

    parser = argparse.ArgumentParser(description='''Generate commands for
                                     cobbler and configuration lines for isc-dhcpd
                                     from SeaMicro MAC addresses.''')

    parser.add_argument('chassis',
        help='The SeaMicro chassis hostname, in format http://myhostname/v2.0.')

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

    parser.add_argument('--first-ip', action='store', type=netaddr.IPAddress,
        default='192.168.1.100',
        help='''The IP that should be assigned to the first server.
        Subsequent servers will increment by one.''')

    parser.add_argument('--base-name', action='store', default='server-',
        help='''The base name for servers.
        Each server will have the ccard number appended.''')

    args = parser.parse_args()

    if args.cobbler and args.cobbler_profile == None:
        print >>sys.stderr, "You must indicate what cobbler profile \
               you want to associate your systems with."
        parser.print_help()
        sys.exit(1)

    return args


def render_template(server_nic_dict, args, template):
    """Build template from server nic data."""
    commands = []
    network = netaddr.IPNetwork('%s/%s' % (args.first_ip, args.netmask))

    if args.gateway == None:
        args.gateway = netaddr.IPAddress(network.first + 1)

    subnets = list(network.subnet(network.prefixlen))

    for server_id, server in server_nic_dict.items():
        ccard = int(server_id.split('/')[0])
        hostname = args.base_name + str(ccard)
        ip_address = args.first_ip + ccard

        for subnet in subnets:
            if ip_address not in subnet:
                print >>sys.stderr, "The number of servers found do not fit \
                in the IP range provided. \
                Either change the first-ip option, or use a larger subnet mask."
                sys.exit(1)

        server['name'] = hostname
        server['ip_address'] = ip_address
        server['gateway'] = args.gateway
        server['netmask'] = args.netmask

        if args.cobbler_profile:
            server['profile'] = args.cobbler_profile

        commands.append(template % server)
    return commands


if __name__ == "__main__":
    main()
