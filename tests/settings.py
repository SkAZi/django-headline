import os.path

### Use current directoy for testing
MEDIA_ROOT = os.path.dirname(__file__)
MEDIA_URL = ''

HEADLINE_CLASSES = {
   "class_name": {
       'font': "font.ttf",
       'size': 120,
       'color': "#000",
       'decoration': {
            'underline': -10,
            'strikeout': 0,
            'opacity': 0.5,
        }
   }, 
   "class_v2": {
       'font': "font.ttf",
       'size': 120,
       'color': "#000",
       'decoration': ['underline'],
   },
   "class_no_dec": {
       'font': "font.ttf",
       'size': 120,
       'color': "#000",
   }
}

HEADLINE_CACHE_DIR = '.'
HEADLINE_FONTS_DIR = '.'
HEADLINE_TEMPLATE = """<img alt="%(text)s" src="%(url)s" />"""
