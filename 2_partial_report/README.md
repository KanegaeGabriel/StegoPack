# StegoPack

Final project for **[SCC0251 - Image Processing](https://uspdigital.usp.br/jupiterweb/jupDisciplina?sgldis=SCC0251)** @ ICMC/USP.

* 10262648 - Gabriel Kanegae Souza
* 10262652 - [João Vitor dos Santos Tristão](http://github.com/jtristao/)

`StegoPack` is a Python module and full application that is able to encode any file into an image via **LSB steganography**, as well as detect and decode a file from an image. For that, the lowest level of encoding is be selected (the one that degrades the original image the least), based on file sizes. It receives an image of any extension and size, as well as a file of any type, and outputs a PNG image.

The encoding levels available are:

* **L0**: 1-bit LSB
* **L1**: 2-bit LSB
* **L2**: 4-bit LSB

## Dependencies

- [`NumPy 1.17.4`](https://numpy.org/) module. Install with `pip3 install numpy`.
- [`imageio 2.8.0`](https://pypi.org/project/imageio/) module. Install with `pip3 install imageio`.

## Files

* [`StegoPack.py`](StegoPack.py) is the main module that contains the `Image` and `Payload` classes.
* [`main.py`](main.py) is the CLI application to encode/decode images.
* [`Demo.ipynb`](Demo.ipynb) is a Jupyter Notebook containing a few examples using [`StegoPack.py`](StegoPack.py) and files from [`demo_files/`](demo_files/).

## Application Usage

* `python3 main.py`
  * Show usage info.

* `python3 main.py (imageFilename)`
  * Show image info and storage capabilities. Detects and decodes any payload in it.

* `python3 main.py (imageFilename) (payloadFilename) (outputFilename)`
  * Encode `payloadFilename` into `imageFilename` and output as `outputFilename`.

## Application Step-by-step

The application ([`main.py`](main.py)) starts off by checking CLI arguments and running the appropriate subroutine from the three listed above.

### Encoding

After checking for the files existence, the application prints some input image metadata (`Image.printInfo()`), compiles the payload (`Payload.__init__()`) - creating a header with payload metadata like name and size - and prints its metadata as well (`Payload.printInfo()`). Then, it finds the appropriate encoding level based on payload size and the input image resolution, and encodes it using LSB steganography (`Image.encodePayload()`), saving it as `outputFilename`.

### Decoding / Image Info

Also checks if the files exist and prints image metadata (`Image.printInfo()`). Then, it searches for the existence of a payload in it by trying to read the payload header in all possible encoding levels (`Image.hasPayload()`). If one is found, the payload is decoded (`Image.decodePayload()`) and saved with its original filename.

## Examples

As the application is supposed to work with any image and payload file as input, the examples listed below are random images and files from the internet, with varying resolutions, styles and file sizes as to showcase the different distortions from different encoding levels.

Input Image | Input Size | Payload | Payload Size | Encoding | Output Image | Output Size
-|-|-|-|-|-|-|
[corgi-599x799.jpg](demo_files/corgi-599x799.jpg) | 66.2 KB | [faustao.png](demo_files/payloads/faustao.png) | 97.1 KB | L0 | [corgi-L0.png](demo_files/encoded/corgi-L0.png) | 671 KB
[randall-2560x1372.png](demo_files/randall-2560x1372.png) | 1.2 MB | [pier39.mp4](demo_files/payloads/pier39.mp4) | 3.2 MB | L2 | [randall-L2.png](demo_files/encoded/randall-L2.png) | 4.3 MB
[plush-418x386.jpg](demo_files/plush-418x386.jpg) | 16.6 KB | [paperpeople.txt](demo_files/payloads/paperpeople.txt) | 3.3 KB | L0 | [plush-L0.png](demo_files/encoded/plush-L0.png) | 156 KB
[caliadventure-1080x1350.jpg](demo_files/caliadventure-1080x1350.jpg) | 201.3 KB | [git-cheatsheet.pdf](demo_files/payloads/git-cheatsheet.pdf) | 352.8 KB | L0 | [caliadventure-L0.png](demo_files/encoded/caliadventure-L0.png) | 2.1 MB
[nightfall-1920x1080.jpg](demo_files/nightfall-1920x1080.jpg) | 1.1 MB | [hap.mp4](demo_files/payloads/hap.mp4) | 1.2 MB | L1 | [nightfall-L1.png](demo_files/encoded/nightfall-L1.png) | 2.8 MB

## To-Do List

* Deny GIFs and other unwanted files read by `imageio` 
* Handle BW/transparent PNGs properly
* Parallelize encoding/decoding
* Extra encoding modes and strategies?
