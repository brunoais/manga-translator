from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from translate import TranslatedBlurb
import math
import dill as pickle

def maxmin(minv, val, maxv):
    return max(min(val, maxv), minv)

def flow_into_box(text, w, font=None, min_word_on_line=.3):
    def text_width(l):
        if l:
            return d.textsize(l, font=font)[0]
        else:
            return 0
    dimg = Image.new("RGB", (100, 100))
    d = ImageDraw.Draw(dimg)
    lines = []
    idx = 0
    line = ""
    while idx < len(text):
        if not line and text[idx] == " ":
            idx += 1
        running_width = text_width(line)
        next_token = text.find(" ", idx + 1)
        if next_token != -1:
            c_text = text[idx:next_token]
        else:
            c_text = text[idx:]
        c_width = text_width(c_text)
        proportion_of_fit = float(w - running_width) / c_width if c_width != 0 else 0
        if proportion_of_fit > .95:
            line += c_text
            idx += len(c_text)
#        elif proportion_of_fit > min_word_on_line:
#            split = max(int(proportion_of_fit * len(c_text)), 1)
#            c_text = c_text[:split] + "-"
#            line += c_text
#            idx += len(c_text) - 1
        else:
            if len(line) > 0:
                lines.append(line)
                line = ""
            else:
                split = int(max(proportion_of_fit * len(c_text) / 2, 1))
                c_text = c_text[:split] + "-"
                lines.append(c_text)
                idx += len(c_text) - 1

    if len(line) > 0:
        lines.append(line)

    return "\n".join(lines)


def typeset_blurb(img, blurb):
    if isinstance(blurb, TranslatedBlurb):
        text = blurb.translation
    else:
        text = blurb.text


    area = blurb.w * blurb.h
    # fontsize = int(math.sqrt(area) / 20)
    fontsize = int(math.sqrt(area) / maxmin(7, len(text) / 10, 20))
    font = ImageFont.truetype(font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=fontsize)
    # pickle.dump(img, open("tts.pkl", mode="w"))
    flowed = flow_into_box(text, blurb.w, font)
    d = ImageDraw.Draw(img)
    size = d.textsize(flowed, font=font)
    x = int((blurb.x + (blurb.w / 2)) - (size[0] / 2))
    y = int((blurb.y + (blurb.h / 2)) - (size[1] / 2))
    # x = int(blurb.x)
    # y = int(blurb.y)
    img.paste((255, 255, 255), (x, y, x + size[0], y + size[1]))
    d.text((x, y), flowed.strip(), fill=(0, 0, 0), font=font)
