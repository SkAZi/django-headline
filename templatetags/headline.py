# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Igor "SkAZi" Potapov <igor@poatpoff.org>
# GNU General Public License
#
# http://github.com/SkAZi/django-headline/

from django import template
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.template import TemplateSyntaxError

import Image, ImageFont, ImageDraw, ImageChops
from os import path
try:
    from hashlib import md5
except:
    from md5 import new as md5
import re

HEADLINE_CACHE_DIR = getattr(settings, 'HEADLINE_CACHE_DIR', 'upload')
HEADLINE_NO_CACHE = getattr(settings, 'HEADLINE_NO_CACHE', False)
HEADLINE_FONTS_DIR = getattr(settings, 'HEADLINE_FONTS_DIR', 'fonts')
HEADLINE_CLASSES = getattr(settings, 'HEADLINE_CLASSES', {})
HEADLINE_TEMPLATE = getattr(settings, 'HEADLINE_TEMPLATE',
        u"""<img alt="%(text)s" src="%(url)s" class="png" width="%(width)s" height="%(height)s" />""")
HEADLINE_PNG_OPTIMIZER = getattr(settings, 'HEADLINE_PNG_OPTIMIZER', False)

AVIABLE_DECORATIONS = {
    'underline': 0,
    'strikeout': 0,
    'opacity': 1,
}

AVIABLE_SPLITTERS = ('br', 'all', 'none')

ENTITIES = (
    (u'&laquo;', u'«'), (u'&raquo;', u'»'),
    (u'&bdquo;', u'„'), (u'&ldquo;', u'“'),
    (u'&lquo;', u'”'),  (u'&ndash;', u'–'),
    (u'&mdash;', u'—'), (u'&amp;', u'&'),
    (u'&quot;', u"\""), (u'&apos;', u"'"),
    (u'&reg;', u'®'),   (u'&copy;', u'©'),
    (u'&trade;', u'™'), (u'&sect;', u'§'),
    (u'&euro;', u'€'),  (u'&nbsp;', u' '),
    (u'&rsquo;', u'’'), (u'&Prime;', u'″'),
    (u'&le;', u'≤'),    (u'&ge;', u'≥'),
    (u'&lt;', u'<'),    (u'&gt;', u'>'),
    (u'\n', u''),       (u'\t', u'    '),
)


def _clean_text(text):
    """
        Clean text from extra spaces and replaces
        html-entities by unicode symbols
    """
    text = text.strip()
    for (s, r) in ENTITIES:
        text = re.sub(s, r, text)
    return text



def _img_from_text(text, font, size=12, color='#000', decoration={}):
    """
        Draws text with font, size, color and decoration parameters.
        Caches images and returns (html or object, width, size) of
        new or exists image
    """
    
    image_path = path.join(settings.MEDIA_ROOT, HEADLINE_CACHE_DIR)
    font_path = path.join(settings.MEDIA_ROOT, HEADLINE_FONTS_DIR)

    id = "headline-%s" % md5(smart_str(''.join((text, font, size.__str__(), color, decoration.__str__())))).hexdigest()
    image_file = path.join(image_path, "%s.png" % id)
    

    if not path.isfile(image_file) or HEADLINE_NO_CACHE:
        
        size = int(size)
        font = ImageFont.truetype(path.join(font_path, font), size)
        width, height = font.getsize(text)
        
        ### Init surfaces
        image = Image.new("RGB", (width, height), (0,0,0))
        alpha = Image.new("L", image.size, "black")
        imtext = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(imtext)
        
        ### Real Drawings on alpha with white color
        if decoration.has_key('opacity'):
            opacity = float(decoration['opacity']) * 255
        else:
            opacity = 255
            
        draw.text((0, 0), text, font=font, fill=opacity)
        if decoration.has_key('underline'):
            val = int(decoration['underline'])
            draw.line((0 + size/20, height * 4 / 5 + val,
                       width - size/20, height * 4 / 5 + val),
                       fill=opacity, width=size / 20)
            
        if decoration.has_key('strikeout'):
            val = int(decoration['strikeout'])
            draw.line((0 + size/20, height / 2  + val,
                       width - size/20, height / 2  + val),
                       fill=opacity, width=size / 20)
            
        ### Alpha color black-magic
        alpha = ImageChops.lighter(alpha, imtext)
        solidcolor = Image.new("RGBA", image.size, color)
        immask = Image.eval(imtext, lambda p: 255 * (int(p != 0)))
        image = Image.composite(solidcolor, image, immask)
        image.putalpha(alpha)
        image.save(image_file, "PNG")
        
        if HEADLINE_PNG_OPTIMIZER:
            from os import system
            system(HEADLINE_PNG_OPTIMIZER % {"file": image_file})
    
    else:
        width, height = Image.open(image_file).size
        
    return "%s%s/%s.png" % \
           (settings.MEDIA_URL, HEADLINE_CACHE_DIR, id), width, height



def _image_list(output, klass, splitter, object=False):
    """
        Pictures and html or objects generator by split options
    """
    if splitter:
        chunks = splitter.split(output)
    else:
        chunks = (output, )
        
    for text in chunks:
        text = _clean_text(text)
        if not text: continue

        url, width, height = _img_from_text(text, **klass)
        obj = { 'text': text,
                'url': url,
                'width': width,
                'height': height }

        if object:
            yield obj
        else:
            yield HEADLINE_TEMPLATE % obj
    
    
def _create_splitter(splitting):
    """
        Creates regular expression text splitter
    """
    if splitting == 'br':
        return re.compile(r"<br */?>"), "<br />"
    elif splitting == 'all':
        return re.compile(r"<br */?>| *"), " "
    else:
        return False, ""



def _get_class( klass ):
    """
        Get or create real class parameters by options string
    """
    params = re.split(r", *", klass.strip('"'))
    cleaned = []
    typ = False

    if len(params) > 2:
        decoration = {}
        
        for param in params:
            param_unpack = param.split(':')
            if param_unpack[0] in AVIABLE_DECORATIONS:
                if len(param_unpack) > 1:
                    decoration[param_unpack[0]] = param_unpack[1]
                else:
                    decoration[param_unpack[0]] = AVIABLE_DECORATIONS[param_unpack[0]]
            else:
                cleaned.append(param)
        
        if(len(cleaned) < 3):
            raise TemplateSyntaxError('Must have at less 3 arguments')
        elif len(cleaned) > 3:
            typ = cleaned[3]
        
        klass = {
            'font': cleaned[0],
            'size': int(cleaned[1]),
            'color': cleaned[2],
            'decoration': decoration
        }
        
        return klass, typ
        
    elif params > 0:
        klass = params[0]
        if len(params) > 1:
            typ = params[1]
        
        try:
            return HEADLINE_CLASSES[klass], typ
        except:
            raise TemplateSyntaxError('There is no class: %s' % klass)
        
    return False, False

    
    
register = template.Library()


@register.filter(name="headline")
def do_text_image_filter(value, klass):
    klass, typ = _get_class(klass)
    if not klass:
        raise TemplateSyntaxError('Headline filter needs in parameter' )
        
    return mark_safe(TextImageNode(value, klass, typ).show())

do_text_image_filter.is_safe = True


@register.tag(name="headline")
def do_text_image_tag(parser, token):
    
    params = token.split_contents()
    
    klass, typ = _get_class(params[1])
        
    if not klass:
        raise TemplateSyntaxError('Headline tag needs in parameter' )
        
    if not typ:
        typ = "br"
    
    nodelist = parser.parse(('endheadline',))
    parser.delete_first_token()
        
    return TextImageNode(nodelist, klass, typ)


class TextImageNode(template.Node):
    
    def __init__(self, nodelist, klass, splitting="br"):
        self.klass = klass
        self.splitter, self.joiner = _create_splitter(splitting)
        self.nodelist = nodelist
        
    def show(self):
        """ If filter """
        output = self.nodelist
        return self.joiner.join(
            _image_list( output, self.klass, self.splitter )
        )
        
    def render(self, context):
        """ If tag """
        output = self.nodelist.render(context)
        return self.joiner.join(
            _image_list( output, self.klass, self.splitter )
        )



@register.tag(name="headlines")
def do_text_images_tag(parser, token):
    params = token.split_contents()
        
    if len(params) > 4 and params[-3] == 'as':
        klass, typ = _get_class(params[-1])
        
        output = []
        for st in params[1:-3]:
            if st.startswith('"') and st.endswith('"'):
                output.append(st.strip('"'))
            else:
                output.append(parser.compile_filter(st))
                
        return TextImagesNode(output, params[-2], klass, typ)
           
    else:
        raise TemplateSyntaxError('Hedlines tag must be like {% headlines <list of vars> as <context_var> <class_or_params> %}' )


class TextImagesNode(template.Node):
    def __init__(self, output, to, klass, splitting):
        self.klass = klass
        self.output = output
        self.to = to
        self.splitter, self.joiner = _create_splitter(splitting)
        
    def _flatten_data(self, output, context):
        """
            Generator of images from all-typed parameters
        """
        for token in output:
            if isinstance(token, (unicode, str)):
                token = (token, )
            else:
                token = token.resolve(context)
                if not isinstance(token, (list, tuple, dict)):
                    token = (token, )
                
            for tk in token:
                for obj in _image_list( tk, self.klass, self.splitter, True):
                    yield obj
    
    def render(self, context):
        context[self.to] = [item for item in self._flatten_data(self.output, context)]
        return ''
