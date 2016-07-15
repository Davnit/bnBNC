from Bouncer import BouncerServer

print("bnBNC - Battle.net Bouncer")
print("   v0.1 Alpha - by Pyro")
print("--------------------------")
print("WARNING! This software has no access restrictions. It is essentially an open proxy.")
print("         It is highly recommended to not have this software running on the open internet.")
print("--------------------------")

server = BouncerServer(6112)
server.run()
