import subprocess
import re

import json

from threading import RLock

def persist_to_file(file_name):

    locker = RLock()
    try:
        cache = json.load(open(file_name, 'r'))
    except (IOError, ValueError):
        cache = {}

    def decorator(original_func):

        def new_func(param):
            if param not in cache:
                result = original_func(param)
                with locker:
                    cache[param] = result
                    json.dump(cache, open(file_name, 'w'))
            return cache[param]

        return new_func

    return decorator

class Blurb(object):
    def __init__(self, x, y, w, h, text, confidence=100.0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.confidence = confidence

    def clean_text(self):
        text = self.text
        text = re.sub(r"\n", "", text)
        return text

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return str(self.x) + ',' + str(self.y) + ' ' + str(self.w) + 'x' + str(self.h) + ' ' + str(
            self.confidence) + '% :' + self.text


class TranslatedBlurb(Blurb):
    def __init__(self, x, y, w, h, text, confidence, translation):
        Blurb.__init__(self, x, y, w, h, text, confidence)
        self.translation = translation

    @classmethod
    def as_translated(cls, parent, translation):
        return cls(parent.x,
                   parent.y,
                   parent.w,
                   parent.h,
                   parent.text,
                   parent.confidence,
                   translation)


@persist_to_file("holds/cache_translations.json")
def translate_text(text):
    bs = subprocess.check_output(["node", "translate.js", text])
    return bs.decode("latin-1")


def translate_blurb(blurb):
    translation = translate_text(blurb.clean_text())
    return TranslatedBlurb.as_translated(blurb, translation)
