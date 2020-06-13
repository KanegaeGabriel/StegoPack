from time import time
from sys import argv
import numpy as np
import imageio
import os

validChars = set("abcdefghijklmnopqrstuvwxyz_-.0123456789!âêîôûãõáéíóúàèìòùñç ")

def fileExists(filename):
    return os.path.isfile(filename)

def loadBinaryFile(filename):
    with open(filename, "rb") as f:
        return f.read()

def saveBinaryFile(data, filename):
    with open(filename, "wb+") as f:
        f.write(data)

def intToBytes(integer):
    # return integer.to_bytes(4, byteorder="big", signed=False)
    return bytearray([(integer & 0xFF000000) >> 24, (integer & 0xFF0000) >> 16,
                      (integer & 0xFF00) >> 8, (integer & 0xFF)])

def bytesToInt(b):
    # return int.from_bytes(b, byteorder="big", signed=False)
    return (b[0] << 24) + (b[1] << 16) + (b[2] << 8) + (b[3])

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
        self.dataSize = os.path.getsize(filename)

        self.height, self.width = self.data.shape[:2]
        self.pixels = self.height * self.width

        self.storageL0 = (self.pixels * 3) // 8
        self.storageL1 = (self.pixels * 3) * 2 // 8
        self.storageL2 = (self.pixels * 3) * 4 // 8

        self._cur = 0

    def printInfo(self):
        print("'{}' has file size {} and".format(self.filename, formatBytes(self.dataSize)), end="")
        print("dimensions {}x{} ({} pixels)".format(self.height, self.width, self.pixels))
        
        print("Payload storage capacities (including payload header):")
        print("    Level 0: up to {}".format(formatBytes(self.storageL0)))
        print("    Level 1: {} to {}".format(formatBytes(self.storageL0+1), formatBytes(self.storageL1)))
        print("    Level 2: {} to {}".format(formatBytes(self.storageL1+1), formatBytes(self.storageL2)))

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

    def decodePayload(self, payloadLevel):
        payload = Payload()
        payload.level = payloadLevel

        self._cur = 0

        payload.encoding, payload.level, payload.filenameSize = self.__readNextBytes(3, payloadLevel)
        payload.filename = self.__readNextBytes(payload.filenameSize, payloadLevel).decode("UTF-8")
        payload.dataSize = bytesToInt(self.__readNextBytes(4, payloadLevel))
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

    def pack(self):
        self.header = bytearray([self.encoding, self.level, self.filenameSize])
        self.header += bytearray(self.filename, "UTF-8")
        self.header += intToBytes(self.dataSize)

        # comp-encoding + comp-lvl + filename-size + FILENAME + data-size + DATA
        #       1b      +    1b    +       1b      + FILENAME +     4b    + DATA

        return self.header + self.data

def main():
    if len(argv) != 2 and len(argv) != 4:
        prog = argv[0]
        print("Usage:")
        print("  python3 {} (imageFilename)".format(prog))
        print("    > Get info about file storage capacity and check if there's a payload")
        print("  python3 {} (imageFilename) (payloadFilename) (outputFilename)".format(prog))
        print("    > Store payload into image and output a new PNG image")
        return

    if len(argv) == 2:
        filename = argv[1]

        if not fileExists(filename):
            print("File '{}' not found. Exiting...".format(filename))
            return

        try:
            imgInput = Image(filename)
        except ValueError:
            print("File '{}' is not a valid image file! Exiting...".format(filename))
            return

        imgInput.printInfo()

        payloadFilename, payloadLevel = imgInput.hasPayload()
        if payloadFilename:
            print("File '{}' found encoded as L{}!".format(payloadFilename, payloadLevel))
            # print("File '{}' found encoded as L{}! Decode? (y/n)".format(payloadFilename, payloadLevel), end=" ")
            # if not input().lower().startswith("y"):
            #     return

            print("Decoding...")
            
            t0 = time()

            payload = imgInput.decodePayload(payloadLevel)
            saveBinaryFile(payload.data, payload.filename)
            
            print("Saved to '{}'! Took {:.2f}s".format(payload.filename, time()-t0))
        else:
            print("No payload detected in '{}'!".format(imgInput.filename))
            return
    
    if len(argv) == 4:
        imgInputFilename, payloadFilename, imgOutputFilename = argv[1:]

        if not imgOutputFilename.lower().endswith(".jpg"):
            imgOutputFilename = ".".join(imgOutputFilename.split(".")[:-1]) + ".png"
            return
        
        for filename in [imgInputFilename, payloadFilename]:
            if not fileExists(filename):
                print("File '{}' not found. Exiting...".format(filename))
                return
        if len(payloadFilename) > 255:
            print("File '{}' has a filename that's too long! ({})".format(payloadFilename, len(payloadFilename)))
            return

        try:
            imgInput = Image(imgInputFilename)
        except ValueError:
            print("File '{}' is not a valid image file! Exiting...".format(imgInputFilename))
            return

        imgInput.printInfo()

        payload = Payload(payloadFilename)
        print("'{}' needs {} of payload storage.".format(payload.filename, formatBytes(payload.packedSize)))

        if payload.dataSize > imgInput.storageL2:
            print("Can't encode '{}' into '{}'.".format(payload.filename, imgInput.filename))
            return

        if payload.dataSize <= imgInput.storageL0:
            print("Encoding using L0...")
            payload.level = 0
        elif payload.dataSize <= imgInput.storageL1:
            print("Encoding using L1...")
            payload.level = 1
        else:
            print("Encoding using L2...")
            payload.level = 2

        t0 = time()

        imgOutput = imgInput.encodePayload(payload)
        imageio.imwrite(imgOutputFilename, imgOutput)

        print("Payload '{}' encoded to '{}',".format(payloadFilename, imgInputFilename), end="")
        print("result saved as '{}'! Took {:.2f}s.".format(imgOutputFilename, time()-t0))

if __name__ == "__main__":
    main()