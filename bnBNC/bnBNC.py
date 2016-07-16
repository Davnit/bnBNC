from Bouncer import BouncerServer
from Config import UserDB

print("bnBNC - Battle.net Bouncer")
print("   v0.1 Alpha - by Pyro")
print("--------------------------")
print("WARNING! This software has limited access restrictions.")
print("         It is highly recommended to not have this software running on the open internet.")
print("--------------------------")

db = UserDB("users.txt")
print("<CONFIG> User database: {0} users.".format(db.count()))

server = BouncerServer(db, 6112)
server.run()
