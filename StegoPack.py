from os.path import getsize
import numpy as np
import imageio

validChars = set("abcdefghijklmnopqrstuvwxyz_-.0123456789!âêîôûãõáéíóúàèìòùñç \\/")

def loadBinaryFile(filename):
    with open(filename, "rb") as f:
        return f.read()

def saveBinaryFile(data, filename):
    with open(filename, "wb+") as f:
        f.write(data)

def formatBytes(b):
    count = 0
    while b > 1024:
        count += 1
        b /= 1024

    unit = ["", "K", "M", "G", "T"]
    return "{:.1f} {}B".format(b, unit[count])

class Image:
    def __init__(self, filename):
        self.filename = filename
        self.data = imageio.imread(filename).astype(np.uint8)
        self.dataSize = getsize(filename)

        self.height, self.width = self.data.shape[:2]
        self.pixels = self.height * self.width

        self.storageL0 = (self.pixels * 3) // 8
        self.storageL1 = (self.pixels * 3) * 2 // 8
        self.storageL2 = (self.pixels * 3) * 4 // 8

        self._cur = 0

    def saveFile(self, filename):
        imageio.imwrite(filename, self.data)

    def printInfo(self):
        print("'{}' has file size {} and".format(self.filename, formatBytes(self.dataSize)), end=" ")
        print("dimensions {}x{} ({} pixels)".format(self.height, self.width, self.pixels))
        
        print("Payload storage capacities (including payload header):")
        print("  Level 0: up to {}".format(formatBytes(self.storageL0)))
        print("  Level 1: {} to {}".format(formatBytes(self.storageL0+1), formatBytes(self.storageL1)))
        print("  Level 2: {} to {}".format(formatBytes(self.storageL1+1), formatBytes(self.storageL2)))

    def hasPayload(self):
        for testLevel in [0, 1, 2]:
            self._cur = 0
            
            encoding, level, filenameSize = self.__readNextBytes(3, testLevel)
            if not all([encoding == 0, level == testLevel, 0 <= filenameSize <= 255]): continue

            try:
                filename = self.__readNextBytes(filenameSize, testLevel)
                filename = filename.decode("UTF-8")

                assert all(c in validChars for c in filename.lower())

                return filename, testLevel
            except:
                continue

        return None, None

    def __readNextBytes(self, n, level):
        # lvl stp mask ite
        #  0   1    1   8
        #  1   2    3   4
        #  2   4   15   2
        step = 2**level
        mask = (2**(2**level))-1
        ite = 2**(3-level)
        
        decodedBytes = bytearray()
        byte = 0
        while len(decodedBytes) < n:
            i = self._cur // (self.width * 3)
            j = (self._cur % (self.width * 3)) // 3
            k = self._cur % 3

            byte <<= step
            byte |= self.data[i,j,k] & mask

            self._cur += 1
            if self._cur % ite == 0:
                decodedBytes.append(byte)
                byte = 0

        return decodedBytes

    def decodePayload(self, payloadLevel=None):
        if not payloadLevel:
            _, payloadLevel = self.hasPayload()

        payload = Payload()
        payload.level = payloadLevel

        self._cur = 0

        payload.encoding, payload.level, payload.filenameSize = self.__readNextBytes(3, payloadLevel)
        payload.filename = self.__readNextBytes(payload.filenameSize, payloadLevel).decode("UTF-8")
        payload.dataSize = int.from_bytes(self.__readNextBytes(4, payloadLevel), byteorder="big", signed=False)
        payload.data = self.__readNextBytes(payload.dataSize, payloadLevel)

        return payload

    def encodePayload(self, payload):
        packedPayload = payload.pack()

        # lvl stp mask
        #  0   1    1
        #  1   2    3
        #  2   4   15
        step = 2**payload.level
        mask = (2**(2**payload.level))-1

        cur = 0
        for byte in range(len(packedPayload)):
            for bit in range(8-step, -1, -step):
                # 0: [7, 6, 5, 4, 3, 2, 1, 0], 1: [6, 4, 2, 0], 2: [4, 0]
                bits = (packedPayload[byte] >> bit) & mask

                i = cur // (self.width * 3)
                j = (cur % (self.width * 3)) // 3
                k = cur % 3

                # print("Encoding '{}' into {}: {:>3} {:>8} -> {:>3} {:>8}" \
                #       .format(bin(bits&mask)[2:].zfill(step), (i,j,k),
                #               self.data[i,j,k], bin(self.data[i,j,k])[2:],
                #               (self.data[i,j,k]&(255-mask))|bits, bin((self.data[i,j,k]&(255-mask))|bits)[2:]))

                self.data[i,j,k] &= 0b11111111 - mask
                self.data[i,j,k] |= bits

                cur += 1

        return self.data

class Payload:
    def __init__(self, filename=None):
        if filename:
            self.filename = filename
            self.data = loadBinaryFile(filename)

            self.encoding = 0
            self.level = 0
            self.filenameSize = len(filename)
            self.dataSize = len(self.data)

            self.packedSize = 3 + self.filenameSize + 4 + self.dataSize

    def saveFile(self):
        saveBinaryFile(self.data, self.filename)

    def printInfo(self):
        print("'{}' needs {} of payload storage.".format(self.filename, formatBytes(self.packedSize)))

    def pack(self):
        self.header = bytearray([self.encoding, self.level, self.filenameSize])
        self.header += bytearray(self.filename, "UTF-8")
        self.header += self.dataSize.to_bytes(4, byteorder="big", signed=False)

        # comp-encoding + comp-lvl + filename-size + FILENAME + data-size + DATA
        #       1b      +    1b    +       1b      + FILENAME +     4b    + DATA

        return self.header + self.data