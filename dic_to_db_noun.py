# -*- coding: utf-8 -*-
# Make the word objects from Noun.dic and save these in database
# In Noun.dic, the word information is like following:
# (品詞 (名詞 一般)) ((見出し語 (鉄腕 3999)) (読み テツワン) (発音 テツワン) )
# Store the information of Hinshi, Midashigo, Yomi(katakana), and hiragana
import codecs
import re
import os
from jcconv import *

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from games.models import *

file = codecs.open('dic/Noun.dic', 'r', 'utf_8')
lines = file.readlines()
# delete all object
Word.objects.all().delete()
# make the word objects from Noun.dic
for line in lines: 
    regex = u"品詞 \((.+?)\)\)"
    list = re.findall(regex, line)
    hinshi =  list[0].encode('utf_8')

    regex = u"見出し語 \((\S+)"
    list = re.findall(regex, line)
    midashigo = list[0].encode('utf_8')

    regex = u"読み (\S+)\)"
    list = re.findall(regex, line)
    katakana = list[0].encode('utf_8')
    if katakana.startswith('{'):
        # the case that there are 2 way to read
        kanas = katakana.split('/')
        for kana in kanas:
            hira = kata2hira(kana.strip('{}'))
            word = Word(hinshi=hinshi, midashigo=midashigo, katakana=kana, hiragana=hira)        
            word.save()
    else:
        hiragana = kata2hira(list[0].encode('utf_8'))
        word = Word(hinshi=hinshi, midashigo=midashigo, katakana=katakana, hiragana=hiragana)
        word.save()
