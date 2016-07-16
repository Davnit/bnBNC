from struct import *
from threading import *
from socket import *

from DataBuffers import DataWriter

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

class BnetClient(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.pair = None

        self.server = ''
        self.port = -1
        self.isConnected = False

    def getClientID(self):
        return "Unknown Client" if self.pair is None else self.pair.getClientID()

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

        print("<{0}> Disconnected from BNET".format(self.getClientID()))
        if self.pair.isControlConnected():
            self.pair.control.informDisconnect(None)