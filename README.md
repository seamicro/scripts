SeaMicro Scripts
=======


get_support_data.py
===

Collect tech support detail and other information useful for TAC in troubleshooting issues.

```
usage: get_support_data.py [-t] <chassis_hostname/ip>
-t / tar and gzip output
```


get_server_macs.py
===

Collects mac addresses from the servers in a chassis. Does not work against 3.3.

```
usage: ./get_server_macs.py [-n 0/1] <chassis_hostname> <server spec>
```
