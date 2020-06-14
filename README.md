# StegoPack

Final project for **[SCC0251 - Image Processing](https://uspdigital.usp.br/jupiterweb/jupDisciplina?sgldis=SCC0251)** @ ICMC/USP.

* 10262648 - Gabriel Kanegae Souza
* 10262652 - [João Vitor dos Santos Tristão](http://github.com/jtristao/)

`StegoPack` is a full application and Python module that is able to encode any file into an image via **LSB steganography**, as well as detect and decode a file from an image. For that, the lowest level of encoding should be selected (the one that degrades the original image the least) between **1-, 2- and 4-bit LSB**, based on file sizes.

## Dependencies

- [`NumPy 1.17.4`](https://numpy.org/) module. Install with `pip3 install numpy`.
- [`imageio 2.8.0`](https://pypi.org/project/imageio/) module. Install with `pip3 install imageio`.

## Usage

`python3 main.py`
Show usage info.

`python3 main.py (imageFilename)`
Show image info and storage capabilities. Detects and decodes any payload in it.

`python3 main.py (imageFilename) (payloadFilename) (outputFilename)`
Encode `payloadFilename` into `imageFilename` and output as `outputFilename`.

## Examples

...

## To-Do List

* Deny GIFs and other unwanted files read by `imageio` 
* Handle BW/transparent PNGs properly
* Parallelize encoding/decoding
* Extra encoding modes and strategies?