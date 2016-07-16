from Bouncer import BouncerServer
from Config import UserDB, IPList

print("bnBNC - Battle.net Bouncer")
print("   v0.1 Alpha - by Pyro")
print("--------------------------")
print("WARNING! This software has limited access restrictions.")
print("         It is highly recommended to not have this software running on the open internet.")
print("--------------------------")

db = UserDB("users.txt")
if db.count() == 0:
    print("<CONFIG> WARNING! No user database is defined. Logins will not be required.")
else:
    print("<CONFIG> User database: {0} users.".format(db.count()))

whitelist = IPList("whitelist.txt")
if whitelist.count() == 0:
    print("<CONFIG> WARNING! No IP whitelist is defined. All connections will be accepted.")
else:
    print("<CONFIG> IP whitelist: {0} IPs".format(whitelist.count()))

server = BouncerServer(db, whitelist, 6112)
server.run()
