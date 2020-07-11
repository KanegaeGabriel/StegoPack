from os.path import getsize
import multiprocessing
import numpy as np
import imageio
import hashlib
import os

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
        
        self.width, self.height, self.channels = self.data.shape[:3]
        assert self.channels >= 3, "Only RGB images are supported. Alpha channels can exist, but will be ignored."

        self.pixels = self.width * self.height

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
        return filename

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

            encoding, level, filenameSize = self.__readNextNBytes(3, testLevel)
            if not all([encoding == 0, level == testLevel, 0 < filenameSize <= 255]): continue

            try:
                filename = self.__readNextNBytes(filenameSize, testLevel)
                filename = filename.decode("UTF-8")

                assert len(filename) == filenameSize

                return filename, testLevel
            except:
                continue

        return None, None

    def _readNBytes(self, s, n, level):
        # lvl stp mask
        #  0   1    1 
        #  1   2    3 
        #  2   4   15 
        step = 2**level
        mask = (2**(2**level)) - 1

        decoded = [0] * n
        for byte in range(n):
            for bit in range(8//step):
                cur = ((s + byte) * (8//step)) + bit

                i = cur // (self.height * 3)
                j = (cur % (self.height * 3)) // 3
                k = cur % 3
                
                decoded[byte] <<= step
                decoded[byte] |= self.data[i,j,k] & mask

        return bytearray(decoded)

    def __readNextNBytes(self, n, level):
        if n < 1000: # Read single-threaded to avoid overhead
            decoded = self._readNBytes(self._cur, n, level)
        else:
            threads = multiprocessing.cpu_count()

            # Split workload - each thread will read bytes indexed in range(s, e)
            args = []
            for t in range(threads):
                s = t * (n//threads) + min(n%threads, t)
                e = (t+1) * (n//threads) + min(n%threads, (t+1))

                args.append((self._cur + s, e-s, level))

            # Spawn parallel processes
            pool = multiprocessing.Pool()
            partsDecoded = pool.starmap(self._readNBytes, args)
            pool.close()
            pool.join()

            # Join partial results in a big array
            decoded = [i for t in partsDecoded for i in t]

        self._cur += n
        return bytearray(decoded)

    def decodePayload(self, verbose=True):
        payloadFilename, payloadLevel = self.hasPayload()

        if not payloadFilename:
            raise ValueError("No payload found in '{}'.".format(self.filename))

        if verbose: print("File '{}' found encoded as L{}!\nDecoding...".format(payloadFilename, payloadLevel))

        self._cur = 0

        # Read payload header
        payload = Payload()
        payload.encoding, payload.level, payload.filenameSize = self.__readNextNBytes(3, payloadLevel)
        payload.filename = self.__readNextNBytes(payload.filenameSize, payloadLevel).decode("UTF-8")
        hashRead = self.__readNextNBytes(hashlib.sha256().digest_size, payloadLevel)
        payload.dataSize = int.from_bytes(self.__readNextNBytes(4, payloadLevel), byteorder="big", signed=False)
        
        # Read data
        payload.data = self.__readNextNBytes(payload.dataSize, payloadLevel)
        assert hashRead == hashlib.sha256(payload.data).digest(), "Payload integrity check failed. File might be corrupted."

        return payload

    def encodePayload(self, payload, fillRandom=False, verbose=True):
        packedSize = payload.getPackedSize()

        if packedSize > self.storageL2:
            raise ValueError("Payload '{}' too big to encode into '{}'.".format(payload.filename, self.filename))

        if packedSize <= self.storageL0:
            payloadLevel = 0
        elif packedSize <= self.storageL1:
            payloadLevel = 1
        else:
            payloadLevel = 2

        packedPayload = payload.getBytes(payloadLevel)

        if verbose: print("Encoding '{}' into '{}' using L{}...".format(payload.filename, self.filename, payloadLevel))

        # lvl stp mask
        #  0   1    1
        #  1   2    3
        #  2   4   15
        step = 2**payloadLevel
        mask = (2**(2**payloadLevel)) - 1

        # Convert payload to a matrix format to allow for NumPy's vectorization
        if fillRandom: # Fill remaining pixels with random noise 
            payloadMatrix = np.random.randint(0, mask+1, (self.width, self.height, 3), dtype=np.uint8)
        else:
            payloadMatrix = self.data.copy()

        for byte in range(len(packedPayload)):
            cur = byte * (8 // step)
            
            # 0: [7, 6, 5, 4, 3, 2, 1, 0], 1: [6, 4, 2, 0], 2: [4, 0]
            for bit in range(8-step, -1, -step):
                i = cur // (self.height * 3)
                j = (cur % (self.height * 3)) // 3
                k = cur % 3

                payloadMatrix[i,j,k] = (packedPayload[byte] >> bit) & mask

                cur += 1

        # Replace last bits of every subpixel
        self.data &= 0b11111111 - mask
        self.data |= payloadMatrix

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

    def getPackedSize(self):
        return 3 + self.filenameSize + hashlib.sha256().digest_size + 4 + self.dataSize

    def printInfo(self):
        print("'{}' needs {} of payload storage.".format(self.filename, formatBytes(self.getPackedSize())))

    def getBytes(self, payloadLevel):
        # Encoding payload header (at least 40 bytes)

        # encoding + level + filename-size + FILENAME + data-hash + data-size
        #    1B    +   1B  +       1B      + [1-255]B +    32B    +     4B   

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
        print("Saved to '{}'! Took {:.2f}s.".format(payload.filename, t1-t0))

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

        imgOutputFilename = image.saveFile(imgOutputFilename)
        print("Saved to '{}'! Took {:.2f}s.".format(imgOutputFilename, t1-t0))