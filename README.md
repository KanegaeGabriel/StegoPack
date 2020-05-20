# StegoPack (proposal)

Final project for **[SCC0251 - Image Processing](https://uspdigital.usp.br/jupiterweb/jupDisciplina?sgldis=SCC0251)** @ ICMC/USP.

* 10262648 - Gabriel Kanegae Souza
* 10262652 - [João Vitor dos Santos Tristão](http://github.com/jtristao/)

## Abstract

This project aims to develop a full application that is able to encode a file (of any extension) in an image (able to be read by `imageio`, with or without transparency) via **LSB steganography**, as well as verify and decode a file from an image. For that, the lowest level of encoding should be selected (the one that degrades the original image the least), based on file sizes.

For encoding: as an input, the program should receive an image file as well as a file to be packed in it. The file has to be small enough to fit (max size depending on original image properties). The output is a PNG file.

For decoding: as an input, the program should receive a PNG image. The image will be searched for any encoded files within it. If a file is found, it is given as output. Otherwise, info about the input file will be given.

## Encoding Techniques

For now, the planned encoding algorithms are 1, 2 and 4-bits LSB (on the examples below, referenced as L0, L1 and L2, respectively). Extra techniques may be explored, like scattering the encoded pixels.

Other than the file binary data, a header is required to store attributes like the encoding algorithm used, filename and extension, and file size.

## Extra Analysis

Alongside the application itself, there can be some extra analysis done on the encoding capabilities (e.g. max payload size supported by each of them), as well as the resulting image degradation.

## Examples

### Usage

```
py StegoPack.py
Usage:
   python3 StegoPack.py (imageFilename)
       > Get info about file storage capacity and check if there's a payload
   python3 StegoPack.py (imageFilename) (payloadFilename) (outputFilename)
       > Store payload into image and output a new image
```

### Image Info

```
py StegoPack.py input.png
'input.png' has file size 582.3 KB and dimensions 630x630 (396900 pixels)
Payload storage capacities (including payload header):
    Level 0: up to 145.3 KB
    Level 1: 145.3 KB to 290.7 KB
    Level 2: 290.7 KB to 581.4 KB
No payload detected in 'input.png'!
```

### File Encoding

```
py StegoPack.py input.png payload.txt output.png
'input.png' has file size 582.3 KB and dimensions 630x630 (396900 pixels)
Payload storage capacities (including payload header):
    Level 0: up to 145.3 KB
    Level 1: 145.3 KB to 290.7 KB
    Level 2: 290.7 KB to 581.4 KB
'payload.txt' needs 142.4 KB of payload storage.
Encoding using L0...
Payload 'payload.txt' encoded to 'input.png', result saved as 'output.png'!
```

### File Decoding

```
py StegoPack.py output.png
File 'payload.txt' found in 'output.png'!
Decoding...
Saved to 'payload.txt'!
```