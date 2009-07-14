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

from htmlentitydefs import name2codepoint
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

AVIABLE_SPLITTERS = ('br', 'all', 'none')
AVIABLE_DECORATIONS = {
    'underline': 0,
    'strikeout': 0,
    'opacity': 1,
    'rotate': 0,
}

ENTITY_CONVERTER = re.compile(r'(?:&#x([a-fA-F\d]{1,4});)|(?:&#(\d{1,5});)|(?:&([a-zA-Z\d]+);)')



def _convertentity(m):
    """
        Convert single entity into unicode character
    """
    ### If it is hex entity like &#xFF;
    if m.group(1):
        return unichr(int(m.group(1), 16))
    ### If it is dec entity like &#255;
    elif m.group(2):
        return unichr(int(m.group(2)))
    ### If it is named entity like &laquo;
    elif m.group(3) and m.group(3) in name2codepoint:
        return unichr(name2codepoint[m.group(3)])
    ### Dont touch all other 
    else:
        return m.group(0)



def _clean_text(text):
    """
        Clean text from extra spaces and replaces
        html-entities by unicode symbols
    """
    text = text.strip().replace(u'\n', u'').replace(u'\r', u'')
    return ENTITY_CONVERTER.sub(_convertentity, text)




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
            
        ### Draws text
        draw.text((0, 0), text, font=font, fill=opacity)
        
        ### Draws an underline
        if decoration.has_key('underline'):
            val = int(decoration['underline'])
            draw.line((0 + size/20, height * 4 / 5 + val,
                       width - size/20, height * 4 / 5 + val),
                       fill=opacity, width=size / 20)
        
        ### Draws an strikeout line
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
        
        ### Rotation
        if decoration.has_key('rotate') and decoration['rotate']:
            angle = float(decoration['rotate'])
            if angle == 90:
                image = image.transpose(Image.ROTATE_90)
            elif angle == 180:
                image = image.transpose(Image.ROTATE_180)
            elif angle == 270:
                image = image.transpose(Image.ROTATE_270)
            else:
                # XXX: Bad rotation
                # Really bicubic transformation works only
                # when canvas doesn`t resize: last param is False
                image = image.rotate(angle, Image.BICUBIC, True)
            width, height = image.size
        
        ### Save image
        image.save(image_file, "PNG")
        
        ### Optimize png with external tool
        if HEADLINE_PNG_OPTIMIZER:
            from os import system
            system(HEADLINE_PNG_OPTIMIZER % {"file": image_file})
        
    else:
        ### We need just dimentions
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
    klass = False
    typ = False

    ### If it is render parameters string
    if len(params) > 2:
        decoration = {}
        
        ### Remove all decorators, they can be anywhere
        ### and add they into separate dict
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
            raise TemplateSyntaxError('Headline render parameters string must have at least 3 parameters (excepting decorations): %s' % ",".join(cleaned))
        ### There we can have type of splitting too
        elif len(cleaned) > 3:
            typ = cleaned[3]
        
        klass = {
            'font': cleaned[0],
            'size': int(cleaned[1]),
            'color': cleaned[2],
            'decoration': decoration
        }
        
    ### If it is class
    elif params > 0:
        try:
            klass = HEADLINE_CLASSES[params[0]]
        except:
            raise TemplateSyntaxError('There is no class %s in HEADLINE_CLASSES definition.' % klass)
        
        ### Back compatibility with v0.2
        if isinstance(klass['decoration'], (list, tuple)):
            decoration = {}
            for i in klass['decoration']:
                decoration[i] = AVIABLE_DECORATIONS[i]
            klass['decoration'] = decoration
        
        ### Type of splitting can be here too
        if len(params) > 1:
            typ = params[1]
        
    return klass, typ



register = template.Library()



@register.filter(name="headline")
def do_text_image_filter(value, klass):
    '''
    Django filter, that generates png image with text
    from variable and returns it`s html representation.
    
    Examples:
       {{ foo|headline:"font.ttf,20,#000" }}
       {{ foo|headline:"font.ttf,20,#000,underline,all" }}
       {{ foo|headline:"base,br" }}    
    '''
    klass, typ = _get_class(klass)
    if not klass:
        raise TemplateSyntaxError('Headline filter needs in single render parameters string' )
        
    return mark_safe(TextImageNode(value, klass, typ).render_text())

do_text_image_filter.is_safe = True



@register.tag(name="headline")
def do_text_image_tag(parser, token):
    '''
    Django tag, that generates png image with text
    from tag inside and returns it`s html representation.
    
    Examples:
        {% headline "font.ttf,20,opacity:0.5,#000" %}Big {{ foo }}{% endheadline %}
        {% headline "font.ttf,20,#000,strikeout:-5,none" %}Big {{ foo }}{% endheadline %}
        {% headline "base" %}Big {{ foo }}{% endheadline %} 
    '''
    params = token.split_contents()
    
    klass, typ = _get_class(params[1])
        
    if not klass:
        raise TemplateSyntaxError('Headline tag needs in single render parameters string' )
        
    if not typ:
        typ = "br"
    
    nodelist = parser.parse(('endheadline',))
    parser.delete_first_token()
        
    return TextImageNode(nodelist, klass, typ)



@register.tag(name="headlines")
def do_text_images_tag(parser, token):
    '''
    Django tag, that generates png images with text
    from tag parameters and returns it`s dict representations
    into context variable.
    
    Examples:
        {% headlines foo_list bar_dict baz_var "And some text" as headers "font.ttf,20,#000" %}
        {% headlines foo_list bar_dict baz_var "And some text" as headers "font.ttf,20,#000,all" %}
        {% headlines foo_list bar_dict baz_var "And some text" as headers "base" %}
    '''
    params = token.split_contents()
        
    if len(params) > 4 and params[-3] == 'as':
        klass, typ = _get_class(params[-1])
        
        output = []
        
        for st in params[1:-3]:
            ### If it is just a string
            if st.startswith('"') and st.endswith('"'):
                output.append(st.strip('"'))
                
            ### Else it is context variable
            else:
                output.append(parser.compile_filter(st))
                
        return TextImagesNode(output, params[-2], klass, typ)
           
    else:
        raise TemplateSyntaxError('Hedlines tag must have at least 4 parameters: one or more variables to render, "as" keyword, context variable and render parameters string. Like this: {% headlines <list of vars> as <context_var> <class_or_params> %}' )




class TextImageNode(template.Node):
    
    def __init__(self, nodelist, klass, splitting="br"):
        self.klass = klass
        self.splitter, self.joiner = _create_splitter(splitting)
        self.nodelist = nodelist
        
    def render_text(self):
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
        ### We walk thu all parameters
        for token in output:
            
            ### Gets just text strings
            if isinstance(token, (unicode, str)):
                token = (token, )
            
            else:
                ### And context variables
                token = token.resolve(context)
                
                ### If it single variable we transforms is into list
                if not isinstance(token, (list, tuple, dict)):
                    token = (token, )
                    
            ### And then ruturns all of them in single stream
            for tk in token:
                for obj in _image_list( tk, self.klass, self.splitter, True):
                    yield obj
    
    def render(self, context):
        context[self.to] = [item for item in self._flatten_data(self.output, context)]
        return ''
