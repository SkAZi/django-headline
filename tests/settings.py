import os.path


MEDIA_ROOT = os.path.dirname(__file__)
MEDIA_URL = ''

HEADLINE_CLASSES = {
   "class_name": {
       'font': "font.ttf",
       'size': 10,
       'color': "#000",
       'decoration': {
            'underline': -10,
            'strikeout': 0,
            'opacity': 0.5,
        }
   }
}

HEADLINE_CACHE_DIR = '.'

HEADLINE_FONTS_DIR = '.'

HEADLINE_TEMPLATE = """<img alt="%(text)s" src="%(url)s" />"""

#HEADLINE_PNG_OPTIMIZER = "optipng -q -o7 %(file)s"
