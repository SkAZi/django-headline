# -*- coding: utf-8 -*-
import random
import unittest
import headline
from os import path
from django.template import TemplateSyntaxError
import Image
from settings import *

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
        pass
    
    def test_do_text_image_tag(self):
        pass
    
    def test_TextImageNode(self):
        pass
    
    def test_do_text_images_tag(self):
        pass
    
    def test_TextImagesNode(self):
        pass
  
if __name__ == '__main__':
    unittest.main()
