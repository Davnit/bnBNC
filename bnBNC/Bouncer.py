from socket import *
from threading import Thread

from BNCS import *
from DataBuffers import *

from Daemons import ServerCleanupDaemon

class BouncerServer():
    def __init__(self, userDB, port=6112):
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)

        self.db = userDB
        self.clients = {}

        self.cleanup = ServerCleanupDaemon(self, 60)
       
    # Returns the next available client key
    def getNextKey(self, dic):
        i = 1
        while i in dic:
            if (dic[i] is None):
                break
            else: i += 1
        return i

    def run(self):
        self.socket.bind(('localhost', self.port))
        self.socket.listen()

        self.clients.clear()

        print("<Server> Server started. Listening for incoming clients...")
        while 1:
            sock, addr = self.socket.accept()
            
            pair = ClientPair(self.getNextKey(self.clients))
            pair.server = self

            pair.control = ProxyClient(sock, addr)
            pair.control.pair = pair

            self.clients[pair.id] = pair
            print("<{0}> Connected from {1}".format(pair.getClientID(), addr))
            pair.control.start()

class ClientPair():
    def __init__(self, id):
        self.id = id

        self.server = None      # The BouncerServer this client belongs to
        self.control = None     # The client issuing commands
        self.remote = None      # The host to proxy data to

    def getClientID(self):
        return "New Client" if self.id == -1 else "Client {0}".format(self.id)

    def isControlConnected(self):
        return (self.control is not None) and (self.control.isConnected)

    def isRemoteConnected(self):
        return (self.remote is not None) and (self.remote.isConnected)


class ProxyClient(Thread):
    def __init__(self, sock, addr):
        Thread.__init__(self)
        self.pair = None

        self.client = sock
        self.address = addr

        self.isConnected = True
        self.isAuthed = False

    def getClientID(self):
        return "Unknown Client" if self.pair is None else self.pair.getClientID()

    def close(self):
        self.isConnected = False
        self.client.close()

    # Sends a control packet to the client
    def sendControlMessage(self, command, params):
        if params is not None:
            command += " " + params

        # Packet contents
        wt = DataWriter()
        wt.writeString(command)

        # Attach header
        pak = BNCSPacket(0xef)
        pak.setData(wt.data)

        self.client.send(pak.buildPacket())

    def checkAuth(self, action):
        if self.pair.server.db is None or self.isAuthed:
            return True
        else:
            self.sendControlMessage(action, "FAIL Not authorized")
            print("<{0}> Attempted unauthorized action: {1}".format(self.getClientID(), action))
            self.close()
            return False

    # Handles a control packet from the client
    def handleControlPacket(self, packet):
        rd = DataReader(packet.data)
        
        cmd = rd.readString().split(' ')

        if (cmd[0] == "LOGIN"):       # Login request
            if len(cmd) < 3:
                self.sendControlMessage("LOGIN", "FAIL Invalid request")
            else:
                if self.pair.server.db is None:
                    # No authentication enabled
                    self.sendControlMessage("LOGIN", "OK")
                    self.isAuthed = True
                else:
                    if self.pair.server.db.validatePassword(cmd[1], cmd[2]):
                        self.sendControlMessage("LOGIN", "OK")
                        self.isAuthed = True
                    else:
                        self.sendControlMessage("LOGIN", "FAIL Incorrect password")
            
            if self.isAuthed:
                print("<{0}> Logged in as: {1}".format(self.getClientID(), cmd[1]))
            else:
                self.close()

            return

        # All other actions require login
        if not self.checkAuth(cmd[0]):
            return

        if (cmd[0] == "CONNECT"):   # Request for new connection
            server = ''
            port = 6112

            # Remote server
            if len(cmd) > 1 and len(cmd[1]) > 0: 
                server = cmd[1]
            else:
                self.sendControlMessage("CONNECT", "FAIL No server specified")
            
            # Remote port (optional)
            if len(cmd) > 2 and len(cmd[2]) > 0: port = int(cmd[2])

            remote = BnetClient()
            remote.pair = self.pair
            self.pair.remote = remote

            remote.connect(server, port)
            print("<{0}> Requested connection to server: {1}".format(self.getClientID(), server))

            if remote.isConnected:
                self.sendControlMessage("CONNECT", "OK " + remote.socket.getpeername()[0])
                remote.start()  # Start receiving data
                print("<{0}> Connection successful.".format(self.getClientID()))
            else:
                print("<{0}> Connection failed.".format(self.getClientID()))

        elif (cmd[0] == "DISCONNECT"):  # Request for disconnection
            if self.pair.isRemoteConnected():
                self.pair.remote.close()
        else:
            print("<{0}> Unrecognized command: {1}".format(self.getClientID(), cmd[0]))

    # Informs the control client that the remote server connection has been closed.
    def informDisconnect(self, message):
        self.sendControlMessage("DISCONNECT", message)
        self.pair.remote = None

    def run(self):
        while self.isConnected:
            packet = None

            try:
                packet = receiveBncsPacket(self.client)
            except: self.isConnected = False

            if packet is not None:
                if packet.packetID == 0xef:
                    # Handle control packets
                    self.handleControlPacket(packet)
                else:
                    # Forward the packet if connection is established
                    if self.pair.isRemoteConnected():
                        self.pair.remote.sendPacket(packet)

        print("<{0}> Disconnected".format(self.getClientID()))
        if self.pair.isRemoteConnected():
            self.pair.remote.close()

