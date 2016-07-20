# bnBNC
A bouncer/proxy for classic Battle.net written in Python 3.5.

Accepts connections from clients and proxies their connection to a classic Battle.net server. Connections to the servers are maintained even when the client itself is not connected to the proxy. The client's channel state is updated when the connection is resumed.

The proxy is not 100% transparent, and is not compatible with a SOCKS proxy.

## Running the server
The proxy requires an installation of Python 3.5.
On Windows, just run the bnBNC.bat file.

On any operating system (Windows included) run the following command from the bnBNC directory.
> python bnBNC.py

The proxy runs on port 6112, which is the standard BNCS port.

## Security
**This software lets a user send data to an any host reachable from your computer.** It's highly recommended to not have this software running on the open internet.

### IP Whitelist
Restricts connections to a pre-defined set of IP addresses.

To use, create a file called "whitelist.txt" in the base directory and place one IP per line.

### Account authentication
Requires connecting clients to specify a username and password (independent from their Battle.net credentials).

To use, create a file called "users.txt" in the base directory. Each line in this file should have the following format:
> \<username\> \<MD5 hash of password\>

*Example:*
> TestUser e99a18c428cb38d5f260853678922e03


## Connection negotiation
When a client connects, the following exchange must take place before any data will be proxied.

### If authentication is enabled, the following must be done FIRST.
> C->S "LOGIN \<username\> \<password encoded in base64\>"

> S->C "LOGIN OK"

### To request a new connection
> C->S "CONNECT \<remote server\> \<remote port\>"

> S->C "CONNECT OK"

> S->C "CLIENTID \<#\>" (used for resuming)

### To resume an existing connection (only available when authentication is enabled)
> C->S "RESUME \<client ID\>"

> S->C "RESUME OK"

### To terminate a connection
> While connected, send:

> S->C "DISCONNECT"
