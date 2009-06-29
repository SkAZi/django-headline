# -*- coding: utf-8 -*-
import random
import unittest
import headline
from os import path
from django.template import TemplateSyntaxError
import Image
from settings import *

class Tentacle(dict):
    def __init__(self, __value__=None, **kwargs):
        self.__value__ = __value__ 
        super(Tentacle, self).__init__(**kwargs)
    def __getattr__(self, item):
        if not item in self:
            self[item] = Tentacle()
        return self[item]
    def __setattr__(self, item, value):
        if item != '__value__':
            self[item] = Tentacle(value)
        else:
            self.__dict__[item] = value
    def __call__(self, *args, **kwargs):
        return self.__value__

class TestHeadlines(unittest.TestCase):
    
    def test_clean_text(self):
        self.assertEqual(headline._clean_text(u"  test "), u"test", "Space cleaning failed")
        self.assertEqual(headline._clean_text(u"   \t   "), u"", "Space and Tabs cleaning failed")
        self.assertEqual(headline._clean_text(
            u"\t &laquo;&raquo;&bdquo;&ldquo;&ndash;&mdash;&amp;&quot;&reg;&copy;&trade;&sect;&euro;&nbsp;&rsquo;&Prime;&le;&ge;&lt;&gt;\n \t "
        ), u"«»„“–—&\"®©™§€ ’″≤≥<>", "Html-entities replacement failed")
        self.assertEqual(headline._clean_text(u"&test; &some;"), u"&test; &some;", "Something width unknown entities")
        self.assertEqual(headline._clean_text(u"&nbsp; &nbsp;"), u"\xa0 \xa0", "&nbsp; replacement failed")

    def test_create_splitter(self):
        splitter, joiner = headline._create_splitter(u"br")
        self.assertEqual(splitter.split("<br /><br/><br><br    />"), ["","","","",""], "Br splitter failed")
        self.assertEqual(splitter.split("br br br<br />br br<br> br br"), ["br br br","br br"," br br"], "Br splitter failed")
        self.assertEqual(splitter.split("br"), ["br",], "Br splitter failed: single")
        self.assertEqual(joiner.join(("","")), "<br />", "Br joiner failed")
        self.assertEqual(joiner.join(("",)), "", "Br joiner failed: single")

        splitter, joiner = headline._create_splitter(u"all")
        self.assertEqual(splitter.split("test test<br />test"), ["test","test","test"], "All splitter failed: ")
        self.assertEqual(splitter.split("test test<br /> test"), ["test","test","","test"], "All splitter failed: ")
        self.assertEqual(splitter.split("testtesttest"), ["testtesttest",], "All splitter failed: single")

        self.assertEqual(headline._create_splitter(u"none"), (False, ""), "None splitter failed: none")
        self.assertEqual(headline._create_splitter(u"other"), (False, ""), "None splitter failed: other")
        self.assertEqual(headline._create_splitter(u""), (False, ""), "None splitter failed: ''")
    
    def test_get_class(self):

        self.failUnlessRaises(TemplateSyntaxError, lambda: headline._get_class("base"))
        self.failUnlessRaises(TemplateSyntaxError, lambda: headline._get_class("font.ttf,#000"))
        self.failUnlessRaises(TemplateSyntaxError, lambda: headline._get_class("class_name,all,strikeout:10000"))
        
        decore = {
            'font': "font.ttf",
            'size': 12,
            'color': "#000",
            'decoration': {}
        }
        
        self.assertEqual(headline._get_class("font.ttf,12,#000"), (decore, False), "Params parsing failed: clean")
        self.assertEqual(headline._get_class("font.ttf,12,#000,all"), (decore, "all"), "Params parsing failed: break type all")

        decore.update({'decoration': {'opacity': 1}})
        self.assertEqual(headline._get_class("font.ttf,12,opacity,#000,all"), (decore, "all"), "Params parsing failed: opacity")

        decore.update({'decoration': {'opacity': '0.5'}})
        self.assertEqual(headline._get_class("font.ttf,12,opacity:0.5,#000,none"), (decore, "none"), "Params parsing failed: opacity:0.5")

        decore.update({'decoration': {'underline': 0, 'strikeout': '7'}})
        self.assertEqual(headline._get_class("font.ttf,12,underline, strikeout:7,#000"), (decore, False), "Params parsing failed: underline, strikeout")

        decore.update({'decoration': {'strikeout': '7'}})
        self.assertEqual(headline._get_class("font.ttf,12,#000,bug:0,bug, strikeout:7"), (decore, "bug:0"), "Params parsing failed: buggy params")

        self.assertEqual(headline._get_class("class_name"), (
            HEADLINE_CLASSES["class_name"], False), "Class parsing failed: clean")

        self.assertEqual(headline._get_class("class_name,all"), (
            HEADLINE_CLASSES["class_name"], "all"), "Class parsing failed: with break type")


    def test_image_list(self):
        splitter, joiner = headline._create_splitter(u"br")
        klass = HEADLINE_CLASSES["class_name"]
        
        images = headline._image_list("Test test", klass, splitter, object=False)
        
        i = 0
        for image in images:
            i += 1
            self.assertEqual(image, """<img alt="Test test" src="./headline-91cafd03cea08d1cd558f849e530da18.png" />""", "(Template want work or hash algorythm changed)")
            
        self.assertEqual(i, 1)

        splitter, joiner = headline._create_splitter(u"all")
        images = headline._image_list("test test", klass, splitter, object=True)

        for image in images:
            i += 1
            self.assert_(path.isfile(image['url']), "File is not created")
            self.assert_(image['width'], "There is no returned width")
            self.assert_(image['height'], "There is no returned height")
            self.assert_(image['text'], "There is no returned text")
            self.assertEqual(image['text'], 'test', "Returned text is not normal")
            
            real_image = Image.open(image['url'])
            size = real_image.size
            self.assertEqual(Image.open(image['url']).size, (image['width'], image['height']), "Real image size is not normal")
            
            colors = real_image.getcolors()
            color_count = len(colors)
            
            self.assert_(8 < color_count < 150, "Color count on image is not normal normal is 8..64")
            
            
        self.assertEqual(i, 3)
            
       
    
    def test_do_text_image_filter(self):
        self.assertEqual(headline.do_text_image_filter('test_do_text_image_filter', 'class_name'), u'''<img alt="test_do_text_image_filter" src="./headline-1e1ee9cb10da2d897bdca38eaae8ae12.png" />''', "Template for filter or filter aint work")
        self.assert_(path.isfile("headline-1e1ee9cb10da2d897bdca38eaae8ae12.png"), "File with filter doesnt created")
    
    def test_do_text_image_tag(self):
        parser = Tentacle()
        parser.parse = parser
        parser.render = 'test_do_text_image_tag'
        
        token = Tentacle()
        token.split_contents = ('headline', 'class_name')
        
        imageNode = headline.do_text_image_tag(parser, token)
        self.assertEqual(imageNode.render(''), u'''<img alt="test_do_text_image_tag" src="./headline-4fe670999bfea37424dfa1789e14e391.png" />''', "Template for tag headline or tag aint work")
        self.assert_(path.isfile("headline-4fe670999bfea37424dfa1789e14e391.png"), "File with tag headline doesnt created")

    
    def test_do_text_images_tag(self):
        parser = Tentacle()
        parser.compile_filter = "HELLO"
        
        token = Tentacle()
        token.split_contents = ('headlines', '"test_do_text_images_tag"', 'Hello|upper', 'as', 'headlines', '"class_name"')

        imageNodes = headline.do_text_images_tag(parser, token)
        context = dict()
        imageNodes.render(context)
        
        self.assertEqual(len(context['headlines']), 2)
        self.assertEqual(context['headlines'][0]['url'], "./headline-8833bb66718a93d75a8330cf1f7c0f9e.png")
        self.assertEqual(context['headlines'][0]['text'], "test_do_text_images_tag")
        self.assertEqual(context['headlines'][1]['url'], "./headline-f28506525c21f7dc8d4a9d529e73d93b.png")
        self.assertEqual(context['headlines'][1]['text'], "HELLO")
        self.assert_(path.isfile("headline-8833bb66718a93d75a8330cf1f7c0f9e.png"), "File with tag headline doesnt created")
        self.assert_(path.isfile("headline-f28506525c21f7dc8d4a9d529e73d93b.png"), "File with tag headline doesnt created")
    
 
if __name__ == '__main__':
    unittest.main()
