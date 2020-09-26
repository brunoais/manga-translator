import os
from enum import Enum
from pathlib import Path
from queue import Queue
from sys import stderr

from concurrency import QUERYING_THREAD_POOL

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


class MirrorPlacement(Enum):
    TOP = 'top'
    RIGHT = 'right'
    BOTTOM = 'bottom'
    LEFT = 'left'
    NONE = 'none'

def cache(blurb, translation, do=True):
    if do:
        if translation is None:
            with open(f'holds/translated_{blurb.x}_{blurb.y}.pkl', 'rb') as f:
                return pickle.load(f)
        with open(f'holds/translated_{blurb.x}_{blurb.y}.pkl', 'wb') as f:
            pickle.dump(translation, f)
            return translation

    return translation


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("imgs", type=Path, nargs='+')
    parser.add_argument("--out", '-o', default='{stem}-out.{ext}', help=
        '''Output file name format. replacements:
        {dirpath}: the path to the directory containing the file 
        {name}: input file name
        {stem}: input file name without extension
        {ext}: extension (including '.')
        '''
    )
    parser.add_argument("--sideMirror", required=False, default=MirrorPlacement.RIGHT.value,
                        choices=tuple(p.value for p in MirrorPlacement.__members__.values()))

    parsed = parser.parse_args()

    parsed.sideMirror = MirrorPlacement(parsed.sideMirror)

    return parsed


def main():

    args = parse_args()

    for img_path in args.imgs:

        img = cv2.imread(os.fspath(img_path))
        to_typeset = Image.fromarray(img.copy())

        final_bytes_image = to_typeset

        print(f"\nfile: {img_path}\n")

        # blurbs = list(locate_bubbles.get_blurbs(img))

        try:
            blurbs = list(locate_bubbles.get_blurbs(img))
        except locate_bubbles.CorruptedImageError as e:
            print(e, file=stderr)
        else:

            translated_blurbs = []
            for blurb in blurbs:
                translated_blurbs.append(QUERYING_THREAD_POOL.submit(translate.translate_blurb, blurb))

            for translated_blurb in translated_blurbs:
                translated = translated_blurb.result()
                typeset.typeset_blurb(to_typeset, translated)

            if args.sideMirror != MirrorPlacement.NONE:
                axis = 0
                if args.sideMirror in (MirrorPlacement.LEFT, MirrorPlacement.RIGHT):
                    axis = 1

                left, right = img, to_typeset
                if args.sideMirror in (MirrorPlacement.RIGHT, MirrorPlacement.BOTTOM):
                    left, right = to_typeset, img

                final_bytes_image = np.concatenate((left, right), axis=axis)

            out_pathname = args.out.format(
                dirpath=img_path.parent,
                name=img_path.name,
                stem=img_path.stem,
                ext=img_path.suffix,
            )
            Path(out_pathname).parent.mkdir(parents=True, exist_ok=True)

            Image.fromarray(final_bytes_image).save(out_pathname)
        # to_typeset.save(args.out)


if __name__ == "__main__":
    main()
