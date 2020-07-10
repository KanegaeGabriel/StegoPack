# StegoPack

Final project for **[SCC0251 - Image Processing](https://uspdigital.usp.br/jupiterweb/jupDisciplina?sgldis=SCC0251)** @ ICMC/USP.

* 10262648 - Gabriel Kanegae Souza
* 10262652 - [João Vitor dos Santos Tristão](http://github.com/jtristao/)

`StegoPack` is a Python module and full application that is able to encode any file into an image via **LSB steganography**, as well as detect and decode a file from an image. For that, the lowest level of encoding is be selected (the one that degrades the original image the least), based on file sizes. For encoding, it receives an image and a file of any type, and outputs a PNG image with the file encoded in it. For decoding, it receives the image with an encoded file, and outputs the file with its original filename.

The encoding levels available are:

* **L0**: 1-bit LSB
* **L1**: 2-bit LSB
* **L2**: 4-bit LSB

## Dependencies

- [`NumPy 1.17.4`](https://numpy.org/) module. Install with `pip3 install numpy`.
- [`imageio 2.8.0`](https://pypi.org/project/imageio/) module. Install with `pip3 install imageio`.

## Files

* [`StegoPack.py`](StegoPack.py) is the main module, containing the `Image` and `Payload` classes. Can also be run standalone as a full application via CLI.
* [`Demo.ipynb`](Demo.ipynb) is a Jupyter Notebook containing a few examples using [`StegoPack.py`](StegoPack.py) and files from [`demo_files/`](demo_files/).

## Application Usage

* `python3 StegoPack.py`
  * Show usage info.

* `python3 StegoPack.py (imageFilename)`
  * Show image info and storage capabilities. Detects and decodes any payload in it.

* `python3 StegoPack.py (imageFilename) (payloadFilename) (outputFilename)`
  * Encode `payloadFilename` into `imageFilename` and output as `outputFilename`.

## Implementation Details

### Payload Header

When the payload is encoded/decoded, a header is placed in the base file preceding the actual data, storing metadata. Here is a more detailed look at its format and fields:

|`encoding`|`level`|`filename-size`|`filename`|`data-hash`|`data-size`|
|-|-|-|-|-|-|
|1 byte|1 byte|1 byte|`filename-size` bytes|32 bytes|4 bytes|

* `encoding`: always 0.
* `level`: can be 0, 1 or 2. Determines the encoding level (1-bit LSB, 2-bit LSB, 4-bit LSB, respectively).
* `filename-size`: length of `filename` field.
* `filename`: payload original filename.
* `data-hash`: SHA-256 hash of the payload data, to be checked against the decoded data.
* `data-size`: payload data size.

After the header, a sequence of `data-size` bytes follows, containing the actual payload data.

## Examples

As the application is supposed to work with any image and payload file as input, the examples listed below are random images and files from the internet, with varying resolutions, styles and file sizes as to showcase the different distortions from different encoding levels.

Input Image | Input Size | Payload | Payload Size | Encoding | Output Image | Output Size
-|-|-|-|-|-|-|
[corgi-599x799.jpg](demo_files/corgi-599x799.jpg) | 66.2 KB | [faustao.png](demo_files/payloads/faustao.png) | 97.1 KB | L0 | [corgi-L0.png](demo_files/encoded/corgi-L0.png) | 671 KB
[randall-2560x1372.png](demo_files/randall-2560x1372.png) | 1.2 MB | [pier39.mp4](demo_files/payloads/pier39.mp4) | 3.2 MB | L2 | [randall-L2.png](demo_files/encoded/randall-L2.png) | 4.3 MB
[plush-418x386.jpg](demo_files/plush-418x386.jpg) | 16.6 KB | [paperpeople.txt](demo_files/payloads/paperpeople.txt) | 3.3 KB | L0 | [plush-L0.png](demo_files/encoded/plush-L0.png) | 156 KB
[caliadventure-1080x1350.jpg](demo_files/caliadventure-1080x1350.jpg) | 201.3 KB | [git-cheatsheet.pdf](demo_files/payloads/git-cheatsheet.pdf) | 352.8 KB | L0 | [caliadventure-L0.png](demo_files/encoded/caliadventure-L0.png) | 2.1 MB
[nightfall-1920x1080.jpg](demo_files/nightfall-1920x1080.jpg) | 1.1 MB | [hap.mp4](demo_files/payloads/hap.mp4) | 1.2 MB | L1 | [nightfall-L1.png](demo_files/encoded/nightfall-L1.png) | 2.8 MB

## Limitations

* Assumes input image is a regular 3- or 4-channel (alpha) image (JPG, BMP, PNG, etc.). No specific support for types such as TIFF or GIF
* Can only output PNGs

## To-Do List

* Handle PNGs as input (ignore transparency?)
* Extra encoding modes and strategies?