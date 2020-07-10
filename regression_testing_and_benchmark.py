import hashlib
import os
from time import time

from StegoPack import *

def test(cleanImageFilename, payloadFilename):
    encodedImageFilename = "out.png"
    extractedPayloadFilename = "out-" + payloadFilename

    image = Image(cleanImageFilename)
    payload = Payload(payloadFilename)

    t0 = time()
    image.encodePayload(payload)
    t1 = time()

    image.saveFile(encodedImageFilename)
    print("Encoding took {:.3f}s.".format(t1-t0))

    image = Image(encodedImageFilename)

    t2 = time()
    payload = image.decodePayload()
    t3 = time()

    payload.saveFile()
    print("Decoding took {:.3f}s.".format(t3-t2))

    os.remove(encodedImageFilename)
    os.remove(payloadFilename.split("/")[-1])

test("demo_files/corgi-599x799.jpg", "demo_files/payloads/faustao.png") # L0
'''
Encoding 'faustao.png' into 'demo_files/corgi-599x799.jpg' using L0...
Encoding took 4.304s.
File 'faustao.png' found encoded as L0!
Decoding...
Decoding took 2.637s.
'''

test("demo_files/nightfall-1920x1080.jpg", "demo_files/payloads/hap.mp4") # L1
'''
Encoding 'hap.mp4' into 'demo_files/nightfall-1920x1080.jpg' using L1...
Encoding took 27.924s.
File 'hap.mp4' found encoded as L1!
Decoding...
Decoding took 17.057s.
'''

test("demo_files/randall-2560x1372.png", "demo_files/payloads/pier39.mp4") # L2
'''
Encoding 'pier39.mp4' into 'demo_files/randall-2560x1372.png' using L2...
Encoding took 37.608s.
File 'pier39.mp4' found encoded as L2!
Decoding...
Decoding took 22.345s.
'''