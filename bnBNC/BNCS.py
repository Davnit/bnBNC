from struct import *
from threading import *
from socket import *

from DataBuffers import *

chatEventIds = {
    0x01: "ShowUser",
    0x02: "UserJoin",
    0x03: "UserLeave",
    0x04: "Whisper",
    0x05: "Talk",
    0x06: "Broadcast",
    0x07: "Channel",
    0x09: "UserFlags",
    0x0A: "WhisperSent",
    0x0D: "ChannelFull",
    0x0E: "ChannelDoesNotExist",
    0x0F: "ChannelRestricted",
    0x12: "Info",
    0x13: "Error",
    0x17: "Emote"
}

def receiveBncsPacket(client):
    # Receive 4 byte header
    inc = client.recv(4)
    if not inc: raise Exception()

    if len(inc) == 1 and inc[0] == 0x01:
        # Protocol selector, return
        return None
    elif inc[0] == 0xff and len(inc) == 4:
        # Valid packet header
        packet = BNCSPacket(inc[0:4])

        if (packet.length > 4):
            # Receive the rest of the packet
            while (not packet.isCompletePacket()):
                inc = client.recv(packet.getNeededData())
                if not inc: raise Exception()

                # Do not use setData() here, to preserve the header-specified length
                packet.data += inc

        return packet
    else:
        return None

def getChatEventName(eventId):
    if eventId in chatEventIds:
        return chatEventIds[eventId]
    else:
        return "Unknown"

def buildEventPacket(event):
    dw = DataWriter()
    dw.writeInt32(event.eventID)
    dw.writeInt32(event.flags)
    dw.writeInt32(event.ping)
    dw.writeRaw(bytes(12))
    dw.writeString(event.user)
    dw.writeString(event.text)

    pak = BNCSPacket(0x0f)
    pak.setData(dw.data)
    return pak

def buildUserPacket(user):
    dw = DataWriter()
    dw.writeInt32(0x01)
    dw.writeInt32(user.flags)
    dw.writeInt32(user.ping)
    dw.writeRaw(bytes(12))
    dw.writeString(user.name)
    dw.writeString(user.statstring)

    pak = BNCSPacket(0x0f)
    pak.setData(dw.data)
    return pak

class BNCSPacket():
    def __init__(self, header):
        if type(header) is bytes and len(header) == 4:
            self.packetID = header[1]
            self.length = unpack('<H', header[2:4])[0]
        else:
            self.packetID = header
            self.length = 4

        self.data = b''

    # Sets the packet content and updates the length parameter
    #  Only use this when creating a new packet, not when receiving one.
    def setData(self, newData):
        self.data = newData
        self.length = len(newData) + 4

    # Returns if the packet has been completely received
    def isCompletePacket(self):
        return self.getNeededData() == 0

    # Returns the amount of data (in bytes) needed to complete the packet.
    def getNeededData(self):
        return self.length - len(self.data) - 4

    # Returns a byte array containing the packet header and content
    def buildPacket(self):
        self.length = len(self.data) + 4

        dw = DataWriter()
        dw.writeByte(0xff)              # Packet header: 0xff
        dw.writeByte(self.packetID)     # Packet ID
        dw.writeInt16(self.length)      # Packet length (incl. header)
        dw.writeRaw(self.data)          # Packet data
        return dw.data

class ChatEvent():
    def __init__(self, packet):
        dr = DataReader(packet.data)

        self.eventID = dr.readInt32()
        self.flags = dr.readInt32()
        self.ping = dr.readInt32()
        dr.readRaw(12)
        self.user = dr.readString()
        self.text = dr.readString()

    def toString(self):
        return "[{0}] <{1}> {2}".format(getChatEventName(self.eventID), self.user, self.text)

class ChatUser():
    def __init__(self, event):
        self.name = event.user
        self.statstring = event.text
        self.ping = event.ping
        self.flags = event.flags

class BnetClient(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.pair = None

        self.server = ''
        self.port = -1
        self.isConnected = False

        self.resetChatState()

    def getClientID(self):
        return "Unknown Client" if self.pair is None else self.pair.getClientID()

    def resetChatState(self):
        self.enterChat = None
        self.channelJoin = None
        self.channelOrder = []
        self.channelList = {}

    def close(self):
        self.isConnected = False
        self.socket.close()

    def sendPacket(self, packet):
        try:
            if type(packet) is BNCSPacket:
                self.socket.send(packet.buildPacket())
            else:
                self.socket.send(packet)
        except:
            self.isConnected = False
            self.close()

    def connect(self, server, port):
        self.server = server
        self.port = port

        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.connect((server, port))
        except: return

        self.isConnected = True
        self.sendPacket(bytes(b'\x01'))       # Protocol selector 0x01
        
        self.resetChatState()

    def sendResume(self, client):
        if client is None: return

        client.sendPacket(self.enterChat)
        client.sendPacket(buildEventPacket(self.channelJoin))
        
        for name in self.channelOrder:
            if name in self.channelList:
                client.sendPacket(buildUserPacket(self.channelList[name]))

    def run(self):
        while self.isConnected: 
            packet = None

            try:
                packet = receiveBncsPacket(self.socket)
            except: self.isConnected = False

            if packet is not None:
                if (self.pair is not None) and self.pair.isControlConnected():
                    # Forward all data to the control client
                    self.pair.control.sendPacket(packet)
                else:
                    # Echo ping requests
                    if packet.packetID == 0x25:
                        self.sendPacket(packet)

                # Cache chat events for resume
                if packet.packetID == 0x0a:
                    self.resetChatState()
                    self.enterChat = packet

                elif packet.packetID == 0x0f:
                    e = ChatEvent(packet)
                    if e.eventID == 0x07:   # join channel
                        self.channelJoin = e
                        self.channelOrder.clear()
                        self.channelList.clear()
                    else:
                        usr = ChatUser(e)
                        if e.eventID in [ 0x01, 0x02 ]: # show user / join
                            self.channelOrder.append(usr.name)
                            self.channelList[usr.name] = usr
                        elif e.eventID == 0x09:         # flag update
                            if usr.name in self.channelList:
                                self.channelList[usr.name].flags = usr.flags
                        elif e.eventID == 0x03:         # user leave
                            if usr.name in self.channelList:
                                self.channelList[usr.name] = None
                            if usr.name in self.channelOrder:
                                self.channelOrder.remove(usr.name)

        print("<{0}> Disconnected from BNET".format(self.getClientID()))
        if self.pair.isControlConnected():
            self.pair.control.informDisconnect(None)