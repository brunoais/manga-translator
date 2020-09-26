#!/usr/bin/python
import re
import string

from PIL import Image
from pytesseract import Output

from translate import Blurb
from functools import lru_cache

import sys
import numpy as np
import dill as pickle
import cv2

import pytesseract

latin_only = re.compile(r"""^[a-zA-Z0-9-_ー<>?'«»%& ]+$""")


def tesseract_params():

    configParams = []

    def configParam(param, val):
        return "-c " + param + "=" + val

    configParams.append(("--psm", "12"))
    configParams.append(("chop_enable", "T"))
    configParams.append(('use_new_state_cost', 'F'))
    configParams.append(('segment_segcost_rating', 'F'))
    configParams.append(('enable_new_segsearch', '0'))
    configParams.append(('textord_force_make_prop_words', 'F'))
    configParams.append(('tessedit_char_blacklist', '}><Lrat' +
                         string.printable.replace('"', '\\"').replace('"', "\\'").strip()))
    configParams.append(('textord_debug_tabfind', '0'))
    params = " ".join([configParam(p[0], p[1]) for p in configParams])
    return params


tesseract_params = tesseract_params()


def is_allowed(text):
    txt = text.strip().lower()

    return (
        len(txt) > 1 and
        not latin_only.match(txt)

    )


def text_confidence(idata):
    filtered_confidence = []
    filtered_text = []

    for confidence, character in zip(idata['conf'], idata['text']):
        confidence = int(confidence)
        if confidence < 0:
            continue

        filtered_confidence.append(confidence)
        filtered_text.append(character)

    average_confidence = sum(filtered_confidence) / len(filtered_confidence) if len(filtered_confidence) > 0 else -1

    if average_confidence < 7:
        return None

    if average_confidence < 40:
        print(f"Rejecting {''.join(idata['text'])} because of low confidence of {average_confidence}%")
        return None

    print("Attempt: ", ''.join(filtered_text))
    return ''.join(filtered_text)


class CorruptedImageError(Exception):
    pass


def get_blurbs(img):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.bitwise_not(
        cv2.adaptiveThreshold(img_gray, 255, cv2.THRESH_BINARY, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 75, 10))

    kernel = np.ones((2, 2), np.uint8)
    img_gray = cv2.erode(img_gray, kernel, iterations=2)
    img_gray = cv2.bitwise_not(img_gray)
    contours, hierarchy = cv2.findContours(img_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    pruned_contours = []
    mask = np.zeros_like(img)
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    height, width, channel = img.shape

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 100 and area < ((height / 3) * (width / 3)):
            pruned_contours.append(cnt)

    # find contours for the mask for a second pass after pruning the large and small contours
    cv2.drawContours(mask, pruned_contours, -1, (255, 255, 255), 1)
    contours2, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    final_mask = cv2.cvtColor(np.zeros_like(img), cv2.COLOR_BGR2GRAY)

    def calc_blurb(cnt):
        area = cv2.contourArea(cnt)
        if area > 1000 and area < ((height / 3) * (width / 3)):
            draw_mask = cv2.cvtColor(np.zeros_like(img), cv2.COLOR_BGR2GRAY)
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
            # pickle.dump(approx, open("approx.pkl", mode="w"))
            cv2.fillPoly(draw_mask, [approx], (255, 0, 0))
            cv2.fillPoly(final_mask, [approx], (255, 0, 0))
            image = cv2.bitwise_and(draw_mask, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
            # draw_mask_inverted = cv2.bitwise_not(draw_mask)
            # image = cv2.bitwise_or(image, draw_mask_inverted)
            y = approx[:, 0, 1].min()
            h = approx[:, 0, 1].max() - y
            x = approx[:, 0, 0].min()
            w = approx[:, 0, 0].max() - x
            image = image[y:y + h, x:x + w]
            pil_image = Image.fromarray(image)

            try:
                idata = pytesseract.image_to_data(pil_image, lang="jpn_ver5", output_type=Output.DICT,
                                                  config=tesseract_params)
                # idata = pytesseract.image_to_data(pil_image, lang="jpn_vert", output_type=Output.DATAFRAME,
                #                                   config=tesseract_params)
                # text = pytesseract.image_to_string(pil_image, lang="jpn_vert", config=tesseract_params)
            except IndexError:
                pass
            except (AttributeError, SystemError) as e:
                raise CorruptedImageError() from e
            else:
                cv2.imshow('Speech Bubble Identification', image)
                confident_text = text_confidence(idata)

                cv2.waitKey(0)
                cv2.destroyAllWindows()

                if confident_text and is_allowed(confident_text):
                    blurb = Blurb(x, y, w, h, confident_text)
                    print("Attempt: " + confident_text)
                    return blurb

    calcs = []
    for cnt in contours2:
        # calcs.append(PROCESSING_THREAD_POOL.submit(calc_blurb, cnt))
        yield calc_blurb(cnt)

    for calc in calcs:
        result = calc.result(30)
        if result:
            yield result



if __name__ == '__main__':
    img = cv2.imread(sys.argv[1])
    get_blurbs(img)
