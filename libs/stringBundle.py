#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import resources
import os
import sys
import locale
from libs.ustr import ustr
from libs.constants import LANGUAGE_ENGLISH

try:
    from PyQt5.QtCore import *
except ImportError:
    if sys.version_info.major >= 3:
        import sip
        sip.setapi('QVariant', 2)
    from PyQt4.QtCore import *


class StringBundle:

    __create_key = object()
    __instance = None

    def __init__(self, create_key, localeStr):
        assert(create_key == StringBundle.__create_key), "StringBundle must be created using StringBundle.getBundle"
        self.idToMessage = {}
        self.localeStr = localeStr
        self.loadBundle(localeStr)
        
    def loadBundle(self, localeStr):
        self.idToMessage = {}  # 清空之前的消息
        paths = self.__createLookupFallbackList(localeStr)
        for path in paths:
            self.__loadBundle(path)

    @classmethod
    def getBundle(cls, localeStr=None):
        if localeStr is None:
            try:
                localeStr = locale.getlocale()[0] if locale.getlocale() and len(
                    locale.getlocale()) > 0 else os.getenv('LANG')
            except:
                print('Invalid locale')
                localeStr = LANGUAGE_ENGLISH
        
        if cls.__instance is None:
            cls.__instance = StringBundle(cls.__create_key, localeStr)
        elif localeStr != cls.__instance.localeStr:
            cls.__instance.loadBundle(localeStr)
            cls.__instance.localeStr = localeStr
            
        return cls.__instance

    def getString(self, stringId):
        assert(stringId in self.idToMessage), "Missing string id : " + stringId
        return self.idToMessage[stringId]

    def __createLookupFallbackList(self, localeStr):
        resultPaths = []
        basePath = ":/strings"
        resultPaths.append(basePath)
        if localeStr is not None:
            # Don't follow standard BCP47. Simple fallback
            tags = re.split('[^a-zA-Z]', localeStr)
            for tag in tags:
                lastPath = resultPaths[-1]
                resultPaths.append(lastPath + '-' + tag)

        return resultPaths

    def __loadBundle(self, path):
        PROP_SEPERATOR = '='
        f = QFile(path)
        if f.exists():
            if f.open(QIODevice.ReadOnly | QFile.Text):
                text = QTextStream(f)
                text.setCodec("UTF-8")

            while not text.atEnd():
                line = ustr(text.readLine())
                key_value = line.split(PROP_SEPERATOR)
                key = key_value[0].strip()
                value = PROP_SEPERATOR.join(key_value[1:]).strip().strip('"')
                self.idToMessage[key] = value

            f.close()
