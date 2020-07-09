from os.path import getsize
import numpy as np
import imageio
import hashlib
import os

validChars = set("abcdefghijklmnopqrstuvwxyz_-.0123456789!âêîôûãõáéíóúàèìòùñç ")

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
        # Replace output file extension to '.png' if it isn't already
        if not filename.lower().endswith(".png"):
            if "." in filename:
                filename = ".".join(filename.split(".")[:-1])
            filename += ".png"

        imageio.imwrite(filename, self.data)

    def printInfo(self):
        print("'{}' has file size {} and".format(self.filename, formatBytes(self.dataSize)), end=" ")
        print("dimensions {}x{} ({} pixels).".format(self.width, self.height, self.pixels))
        
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

                assert len(filename) > 0
                assert all(c in validChars for c in filename.lower())

                return filename, testLevel
            except:
                continue

        return None

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

    def decodePayload(self, verbose=True):
        if not self.hasPayload():
            raise ValueError("No payload found in '{}'.".format(self.filename))

        payloadFilename, payloadLevel = self.hasPayload()

        if verbose: print("File '{}' found encoded as L{}!\nDecoding...".format(payloadFilename, payloadLevel))

        self._cur = 0

        # Reading payload header
        payload = Payload()
        payload.encoding, payload.level, payload.filenameSize = self.__readNextBytes(3, payloadLevel)
        payload.filename = self.__readNextBytes(payload.filenameSize, payloadLevel).decode("UTF-8")
        hashRead = self.__readNextBytes(hashlib.sha256().digest_size, payloadLevel)
        payload.dataSize = int.from_bytes(self.__readNextBytes(4, payloadLevel), byteorder="big", signed=False)
        
        # Reading data
        payload.data = self.__readNextBytes(payload.dataSize, payloadLevel)
        assert hashRead == hashlib.sha256(payload.data).digest(), "Payload integrity check failed. File might be corrupted."

        return payload

    def encodePayload(self, payload, verbose=True):
        if payload.dataSize > self.storageL2:
            raise ValueError("Payload '{}' too big to encode into '{}'.".format(payload.filename, self.filename))

        if payload.dataSize <= self.storageL0:
            payloadLevel = 0
        elif payload.dataSize <= self.storageL1:
            payloadLevel = 1
        else:
            payloadLevel = 2

        if verbose: print("Encoding '{}' into '{}' using L{}...".format(payload.filename, self.filename, payloadLevel))

        packedPayload = payload.getBytes(payloadLevel)

        # lvl stp mask
        #  0   1    1
        #  1   2    3
        #  2   4   15
        step = 2**payloadLevel
        mask = (2**(2**payloadLevel))-1

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
            self.filename = os.path.split(filename)[-1]

            if len(self.filename) > 255:
                raise ValueError("Payload filename is too long! (Max 255, is {})".format(len(self.filename)))

            self.data = loadBinaryFile(filename)

            self.encoding = 0
            self.filenameSize = len(self.filename)
            self.dataSize = len(self.data)

    def saveFile(self, path=""):
        saveBinaryFile(self.data, os.path.join(path, self.filename))

    def printInfo(self):
        packedSize = 3 + self.filenameSize + hashlib.sha256().digest_size + 4 + self.dataSize
        print("'{}' needs {} of payload storage.".format(self.filename, formatBytes(packedSize)))

    def getBytes(self, payloadLevel):
        # Encoding payload header (at least 41 bytes)

        # comp-encoding + comp-lvl + filename-size + FILENAME + data-hash + data-size +  DATA
        #       1B      +    1B    +       1B      + [1-255]B +    32B    +     4B    + [1-?]B

        header = bytearray([self.encoding, payloadLevel, self.filenameSize])
        header += bytearray(self.filename, "UTF-8")
        header += hashlib.sha256(self.data).digest()
        header += self.dataSize.to_bytes(4, byteorder="big", signed=False)

        return header + self.data

# Standalone execution
if __name__ == "__main__":
    from time import time
    from sys import argv

    # Help info
    if len(argv) != 2 and len(argv) != 4:
        prog = argv[0]

        print("Usage:")
        print("  python3 {} (imageFilename)".format(prog))
        print("    > Get info about file storage capacity and check if there's a payload")
        print("  python3 {} (imageFilename) (payloadFilename) (outputFilename)".format(prog))
        print("    > Store payload into image and output a new PNG image")
        
        exit()

    # File info / decoding
    if len(argv) == 2:
        filename = argv[1]

        image = Image(filename)
        image.printInfo()

        t0 = time()
        try:
            payload = image.decodePayload()
        except ValueError as e:
            print(e)
            exit()

        t1 = time()

        payload.saveFile()
        print("Saved to '{}'! Took {:.2f}s".format(payload.filename, t1-t0))

    # File encoding
    if len(argv) == 4:
        imgInputFilename, payloadFilename, imgOutputFilename = argv[1:]

        image = Image(imgInputFilename)
        image.printInfo()

        payload = Payload(payloadFilename)
        payload.printInfo()

        t0 = time()
        image.encodePayload(payload)
        t1 = time()

        image.saveFile(imgOutputFilename)
        print("Saved to '{}'! Took {:.2f}s.".format(imgOutputFilename, t1-t0))