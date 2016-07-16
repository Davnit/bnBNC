from struct import *

class DataReader():
    def __init__(self, data):
        self.data = data

        self.position = 0

    def length(self):
        return len(self.data)

    # Reads a single byte
    def readByte(self):
        b = self.data[self.position]
        self.position += 1
        return b

    # Reads a fixed-length byte array (VOID, BYTE[])
    def readRaw(self, length):
        b = self.data[self.position:self.position + length]
        self.position += length
        return b

    # Reads a 16-bit integer (WORD)
    def readInt16(self):
        s = unpack('<H', self.data[self.position:self.position + 2])[0]
        self.position += 2
        return s

    # Reads a 32-bit integer (DWORD)
    def readInt32(self):
        i = unpack('<L', self.data[self.position:self.position + 4])[0]
        self.position += 4
        return i

    # Reads a 64-bit integer (FILETIME)
    def readInt64(self):
        l = unpack('<Q', self.data[self.position:self.position + 8])[0]
        self.position += 8
        return l

    # Reads a null-terminated string
    def readString(self):
        idx = self.position
        while idx < self.length():
            if self.data[idx] == 0x00:
                break
            idx += 1
        s = self.data[self.position:idx].decode("ISO-8859-1")
        self.position = idx + 1
        return s

class DataWriter():
    def __init__(self):
        self.data = b''

    def length(self):
        return len(self.data)

    # Writes a single byte
    def writeByte(self, value):
        self.data += bytes([value])

    # Writes an array of bytes (VOID, BYTE[])
    def writeRaw(self, value):
        self.data += value

    # Writes a 16-bit integer (WORD)
    def writeInt16(self, value):
        self.writeRaw(pack('<H', value))

    # Writes a 32-bit integer (DWORD)
    def writeInt32(self, value):
        self.writeRaw(pack('<L', value))

    # Writes a 64-bit integer (FILETIME)
    def writeInt64(self, value):
        self.writeRaw(pack('<Q', value))

    # Writes a UTF-8 encoded null-terminated string
    def writeString(self, value):
        self.writeRaw(value.encode("utf-8"))
        self.writeByte(0x00)

