import os

if os.name != 'nt':
    os.environ.setdefault('TMPDIR', '/dev/shm')

import argparse
import numpy as np
import dill as pickle
import cv2
import locate_bubbles
import translate
import typeset

from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("img")
    parser.add_argument("sideMirror", default=True)
    parser.add_argument("out")
    args = parser.parse_args()

    img = cv2.imread(args.img)
    blurbs = locate_bubbles.get_blurbs(img)
    to_typeset = Image.fromarray(img.copy())

    for blurb in blurbs:
        translated = translate.translate_blurb(blurb)
#        translated = blurb
        typeset.typeset_blurb(to_typeset, translated)

    numpy_horizontal_concat = to_typeset
    if args.sideMirror:
        numpy_horizontal_concat = np.concatenate((img, to_typeset), axis=1)

    Image.fromarray(numpy_horizontal_concat).save(args.out)
    # to_typeset.save(args.out)


if __name__ == "__main__":
    main()
