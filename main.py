from os.path import isfile
from time import time
from sys import argv

from StegoPack import *

def main():
    # Help info
    if len(argv) != 2 and len(argv) != 4:
        prog = argv[0]

        print("Usage:")
        print("  python3 {} (imageFilename)".format(prog))
        print("    > Get info about file storage capacity and check if there's a payload")
        print("  python3 {} (imageFilename) (payloadFilename) (outputFilename)".format(prog))
        print("    > Store payload into image and output a new PNG image")
        
        return

    # File info / decoding
    if len(argv) == 2:
        filename = argv[1]

        if not isfile(filename):
            print("File '{}' not found. Exiting...".format(filename))
            return

        try:
            image = Image(filename)
        except ValueError:
            print("File '{}' is not a valid image file! Exiting...".format(filename))
            return

        image.printInfo()

        payloadFilename, payloadLevel = image.hasPayload()
        if payloadFilename:
            print("File '{}' found encoded as L{}!".format(payloadFilename, payloadLevel))
            # print("File '{}' found encoded as L{}! Decode? (y/n)".format(payloadFilename, payloadLevel), end=" ")
            # if not input().lower().startswith("y"):
            #     return

            print("Decoding...")
            
            t0 = time()
            payload = image.decodePayload(payloadLevel)
            t1 = time()

            payload.saveFile()
            
            print("Saved to '{}'! Took {:.2f}s".format(payload.filename, t1-t0))
        else:
            print("No payload detected in '{}'!".format(image.filename))
            return

    # File encoding
    if len(argv) == 4:
        imgInputFilename, payloadFilename, imgOutputFilename = argv[1:]

        for filename in [imgInputFilename, payloadFilename]:
            if not isfile(filename):
                print("File '{}' not found. Exiting...".format(filename))
                return

        if len(payloadFilename) > 255:
            print("File '{}' has a filename that's too long! ({})".format(payloadFilename, len(payloadFilename)))
            return

        try:
            image = Image(imgInputFilename)
        except ValueError:
            print("File '{}' is not a valid image file! Exiting...".format(imgInputFilename))
            return
        image.printInfo()

        payload = Payload(payloadFilename)
        payload.printInfo()

        if payload.dataSize > image.storageL2:
            print("Can't encode '{}' into '{}'.".format(payload.filename, image.filename))
            return

        if payload.dataSize <= image.storageL0:
            print("Encoding using L0...")
            payload.level = 0
        elif payload.dataSize <= image.storageL1:
            print("Encoding using L1...")
            payload.level = 1
        else:
            print("Encoding using L2...")
            payload.level = 2

        t0 = time()
        image.encodePayload(payload)
        t1 = time()

        image.saveFile(imgOutputFilename)

        print("Payload '{}' encoded to '{}',".format(payloadFilename, imgInputFilename), end=" ")
        print("result saved as '{}'! Took {:.2f}s.".format(imgOutputFilename, t1-t0))

if __name__ == "__main__":
    main()