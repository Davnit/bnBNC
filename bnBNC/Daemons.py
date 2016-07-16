import time

from threading import *
from BNCS import BNCSPacket

class ServerCleanupDaemon(Thread):
    def __init__(self, server, interval):
        Thread.__init__(self)
        self.setDaemon(True)
        
        self.server = server
        self.interval = interval
        self.start()

    def runOnce(self):
        for i, c in self.server.clients.items():
            if (c is not None) and (not c.isControlConnected()):
                self.server.clients[i] = None

        for i, r in self.server.remotes.items():
            if (r is not None) and (not r.remote.isConnected):
                self.server.remotes[i] = None

    def run(self):
        while 1:
            self.runOnce()
            time.sleep(self.interval)

class RemoteKeepAliveDaemon(Thread):
    def __init__(self, server, interval):
        Thread.__init__(self)
        self.setDaemon(True)

        self.server = server
        self.interval = interval
        self.start()

    def runOnce(self):
        pak = BNCSPacket(0x00)
        for ri in self.server.remotes.values():
            ri.remote.sendPacket(pak)

    def run(self):
        while 1:
            self.runOnce()
            time.sleep(self.interval)
