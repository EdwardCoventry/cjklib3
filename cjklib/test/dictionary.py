#!/usr/bin/python
# -*- coding: utf-8 -*-
# This file is part of cjklib.
#
# cjklib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cjklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with cjklib.  If not, see <http://www.gnu.org/licenses/>.

"""
Unit tests for :mod:`cjklib.dictionary`.
"""

# pylint: disable-msg=E1101
#  testcase attributes and methods are only available in concrete classes

import re
import os
import new
import unittest

from cjklib.dictionary import (getAvailableDictionaries, getDictionaryClass,
    getDictionary)
from cjklib.dictionary import search as searchstrategy
from cjklib.build import DatabaseBuilder
from cjklib import util
from cjklib.test import NeedsTemporaryDatabaseTest, attr, EngineMock

class DictionaryTest(NeedsTemporaryDatabaseTest):
    """Base class for testing of :mod:`cjklib.dictionary` classes."""
    DICTIONARY = None
    """Name of dictionary to test"""

    def setUp(self):
        NeedsTemporaryDatabaseTest.setUp(self)

        self.dictionaryClass = cls = getDictionaryClass(self.DICTIONARY)
        self.table = (hasattr(cls, 'DICTIONARY_TABLE') and cls.DICTIONARY_TABLE
            or None)

    def shortDescription(self):
        methodName = getattr(self, self.id().split('.')[-1])
        # get whole doc string and remove superfluous white spaces
        noWhitespaceDoc = re.sub(r'\s+', ' ', methodName.__doc__.strip())
        # remove markup for epytext format
        clearName = re.sub(r'[CLI]\{([^\}]*)}', r'\1', noWhitespaceDoc)
        # add name of reading
        return clearName + ' (for %s)' % self.DICTIONARY


class DictionaryMetaTest(DictionaryTest):
    """Tests meta operations."""
    def testInitialization(self):
        """Test initialisation."""
        originalEngine = self.db.engine

        # test if dictionary is accepted
        self.db.engine = EngineMock(originalEngine, mockTables=[self.table])

        self.assertTrue(self.dictionaryClass.available(self.db))
        dictionary = getDictionary(self.DICTIONARY, dbConnectInst=self.db)
        self.assertTrue(self.dictionaryClass in getAvailableDictionaries(self.db))

        # test if character domain is rejected
        self.db.engine = EngineMock(originalEngine, mockNonTables=[self.table])

        self.assertTrue(not self.dictionaryClass.available(self.db))
        self.assertRaises(ValueError, getDictionary, self.DICTIONARY,
            dbConnectInst=self.db)
        self.assertTrue(self.dictionaryClass not in getAvailableDictionaries(
            self.db))


class DictionaryResultTest(DictionaryTest):
    """Base class for testing of dictionary return values."""
    INSTALL_CONTENT = None
    """
    Content the dictionary mock will include. Should follow the dictionary's
    actual format.
    """

    ACCESS_RESULTS = []
    """List of query/result tuples."""

    DICTIONARY_OPTIONS = {}
    """Options for the dictionary instance passed when constructing object."""

    class _ContentGenerator(object):
        def getGenerator(self):
            for line in self.content:
                yield line

    def setUp(self):
        DictionaryTest.setUp(self)

        builderClasses = DatabaseBuilder.getTableBuilderClasses(quiet=True)
        dictionaryBuilder = [cls for cls in builderClasses
            if cls.PROVIDES == self.table][0]

        contentBuilder = new.classobj("SimpleDictBuilder",
            (DictionaryResultTest._ContentGenerator, dictionaryBuilder),
            {'content': self.INSTALL_CONTENT})

        self.builder = DatabaseBuilder(quiet=True, dbConnectInst=self.db,
            additionalBuilders=[contentBuilder], prefer=["SimpleDictBuilder"],
            rebuildExisting=True, noFail=False)
        self.builder.build(self.DICTIONARY)
        assert self.db.mainHasTable(self.DICTIONARY)

        self.dictionary = self.dictionaryClass(dbConnectInst=self.db,
            **self.DICTIONARY_OPTIONS)

    def tearDown(self):
        self.builder.remove(self.DICTIONARY)
        assert not self.db.mainHasTable(self.DICTIONARY)

    @util.cachedproperty
    def resultIndexMap(self):
        content = self.INSTALL_CONTENT[:]

        content = list(map(list, content))
        for strategy in self.dictionary._formatStrategies:
            content = list(map(strategy.format, content))
        content = list(map(tuple, content))

        return dict((row, idx) for idx, row in enumerate(content))

    def testResults(self):
        """Test results for access methods ``getFor...``."""
        def resultPrettyPrint(indices):
            return '[' + "\n".join(repr(self.INSTALL_CONTENT[index])
                for index in sorted(indices)) + ']'

        for methodName, options, requests in self.ACCESS_RESULTS:
            options = dict(options) or {}
            method = getattr(self.dictionary, methodName)
            for request, targetResultIndices in requests:
                results = method(request, **options)
                resultIndices = [self.resultIndexMap[tuple(e)] for e in results]
                self.assertEqual(set(resultIndices), set(targetResultIndices),
                        ("Mismatch for method %s and string %s (options %s)\n"
                        % (repr(methodName), repr(request), repr(options))
                        + "Should be\n%s\nbut is\n%s\n"
                            % (resultPrettyPrint(targetResultIndices),
                                resultPrettyPrint(resultIndices))))


class FullDictionaryTest(DictionaryTest):
    """Base class for testing a full database instance."""
    def setUp(self):
        DictionaryTest.setUp(self)

        # build dictionary
        dataPath = [util.getDataPath(), os.path.join('.', 'test'),
            os.path.join('.', 'test', 'downloads')]
        self.builder = DatabaseBuilder(quiet=True, dbConnectInst=self.db,
            dataPath=dataPath, rebuildExisting=True, noFail=False)
        self.builder.build(self.DICTIONARY)

        self.dictionary = self.dictionaryClass(dbConnectInst=self.db)

    def tearDown(self):
        self.builder.remove(self.DICTIONARY)


class DictionaryAccessTest(FullDictionaryTest):
    """Tests access methods ``getFor...``."""
    ACCESS_METHODS = ('getFor', 'getForHeadword', 'getForReading',
        'getForTranslation')

    TEST_STRINGS = ('跼', '東京', 'とうきょう', "Xi'an", 'New York', 'term')

    def testAccess(self):
        """Test access methods ``getFor...``."""
        for methodName in self.ACCESS_METHODS:
            method = getattr(self.dictionary, methodName)
            for string in self.TEST_STRINGS:
                method(string)


class EDICTMetaTest(DictionaryMetaTest, unittest.TestCase):
    DICTIONARY = 'EDICT'

class EDICTAccessTest(DictionaryAccessTest, unittest.TestCase):
    DICTIONARY = 'EDICT'

class EDICTDictionaryResultTest(DictionaryResultTest, unittest.TestCase):
    DICTIONARY = 'EDICT'

    INSTALL_CONTENT = [
        ('東京', 'とうきょう', '/(n) Tokyo (current capital of Japan)/(P)/'),
        ('東京語', 'とうきょうご', '/(n) Tokyo dialect (esp. historical)/'),
        ('東京都', 'とうきょうと', '/(n) Tokyo Metropolitan area/'),
        ('頭胸部', 'とうきょうぶ', '/(n) cephalothorax/'),
        #(u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getForHeadword', (), [('東京', [0])]),
        ('getFor', (), [('とうきょう_', [1, 2, 3])]),
        ('getForHeadword', (), [('Tokyo', [])]),
        ('getForHeadword', (), [('東%', [0, 1, 2])]),
        ('getFor', (), [('Tokyo', [0])]),
        ('getFor', (), [('_Tokyo', [])]),
        ('getForTranslation', (), [('tokyo%', [0, 1, 2])]),
    ]


class CEDICTMetaTest(DictionaryMetaTest, unittest.TestCase):
    DICTIONARY = 'CEDICT'

class CEDICTAccessTest(DictionaryAccessTest, unittest.TestCase):
    DICTIONARY = 'CEDICT'

class CEDICTDictionaryResultTest(DictionaryResultTest, unittest.TestCase):
    DICTIONARY = 'CEDICT'

    INSTALL_CONTENT = [
        ('知道', '知道', 'zhi1 dao5', '/to know/to be aware of/'),
        ('執導', '执导', 'zhi2 dao3', '/to direct (a film, play etc)/'),
        ('直搗', '直捣', 'zhi2 dao3', '/to storm/to attack directly/'),
        ('直到', '直到', 'zhi2 dao4', '/until/'),
        ('指導', '指导', 'zhi3 dao3', '/to guide/to give directions/to direct/to coach/guidance/tuition/CL:個|个[ge4]/'),
        ('制導', '制导', 'zhi4 dao3', '/to control (the course of sth)/to guide (a missile)/'),
        ('指導教授', '指导教授', 'zhi3 dao3 jiao4 shou4', '/adviser/advising professor/'),
        ('指導課', '指导课', 'zhi3 dao3 ke4', '/tutorial/period of tuition for one or two students/'),
        ('個', '个', 'ge4', '/individual/this/that/size/classifier for people or objects in general/'),
        ('西安', '西安', 'Xi1 an1', "/Xi'an city, subprovincial city and capital of Shaanxi 陝西省|陕西省[Shan3 xi1 sheng3] in northwest China/see 西安區|西安区[Xi1 an1 qu1]/"),
        ('仙', '仙', 'xian1', '/immortal/'),
        ('Ｃ盤', 'Ｃ盘', 'C pan2', '/C drive or default startup drive (computing)/'),
        ('ＵＳＢ手指', 'ＵＳＢ手指', 'U S B shou3 zhi3', '/USB flash drive/'),
        ('\U000289c0\U000289c0', '\U000289c0\U000289c0', 'bo1 bo1', '/Bohrium Bohrium/'),
        ('\U000289c0', '\U000289c0', 'bo1', '/Bohrium/'),
        #(u'', u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getFor', (('toneMarkType', 'numbers'),),
            [('zhidao', [0, 1, 2, 3, 4, 5])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('zhi2dao', [1, 2, 3])]),
        ('getFor', (), [('to %', [0, 1, 2, 4, 5])]),
        ('getForTranslation', (), [('to guide', [4, 5])]),
        ('getForReading', (('toneMarkType', 'numbers'),),
            [('zhi导', [1, 4, 5])]),
        ('getForReading', (('toneMarkType', 'numbers'),),
            [('zhi导%', [1, 4, 5, 6, 7])]),
        ('getFor', (), [('個', [8])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('xian1', [9, 10])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('C pan', [11])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('Ｃpan', [11])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('Ｃ pan', [11])]),
        ('getFor', (), [('Ｃ盘', [11])]),
        ('getFor', (), [('C盘', [11])]),
        ('getForReading', (('toneMarkType', 'numbers'),),
            [('USB shou指', [12])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('bo', [14])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('\U000289c0bo1', [13])]),
        ]


class CEDICTGRMetaTest(DictionaryMetaTest, unittest.TestCase):
    DICTIONARY = 'CEDICTGR'

class CEDICTGRAccessTest(DictionaryAccessTest, unittest.TestCase):
    DICTIONARY = 'CEDICTGR'


class HanDeDictMetaTest(DictionaryMetaTest, unittest.TestCase):
    DICTIONARY = 'HanDeDict'

class HanDeDictAccessTest(DictionaryAccessTest, unittest.TestCase):
    DICTIONARY = 'HanDeDict'

class HanDeDictDictionaryResultTest(DictionaryResultTest, unittest.TestCase):
    DICTIONARY = 'HanDeDict'

    INSTALL_CONTENT = [
        ('對不起', '对不起', 'dui4 bu5 qi3', '/Entschuldigung (u.E.) (S)/sorry (u.E.)/'),
        ('自由大學', '自由大学', 'zi4 you2 da4 xue2', '/Freie Universität, FU (meist FU Berlin) (u.E.) (Eig)/'),
        ('西柏林', '西柏林', 'xi1 bo2 lin2', '/West-Berlin (u.E.) (Eig, Geo)/'),
        ('柏林', '柏林', 'bo2 lin2', '/Berlin (u.E.) (Eig, Geo)/'),
        ('北', '北', 'bei3', '/Norden (S)/nördlich (Adj)/nordwärts, nach Norden, gen Norden (Adv)/Nord-; Bsp.: 北風 北风 -- Nordwind/'),
        ('朔風', '朔风', 'shuo4 feng1', '/Nordwind (u.E.) (S)/'),
        ('IC卡', 'IC卡', 'I C ka3', '/Chipkarte (S)/'),
        ('USB電纜', 'USB电缆', 'U S B dian4 lan3', '/USB-Kabel (u.E.) (S)/'),
        ('\U000289c0\U000289c0', '\U000289c0\U000289c0', 'bo1 bo1', '/Bohrium Bohrium/'),
        ('\U000289c0', '\U000289c0', 'bo1', '/Bohrium/'),
        #(u'', u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getFor', (), [('对不起', [0])]),
        ('getFor', (), [('對不起', [0])]),
        ('getFor', (), [('对_起', [0])]),
        ('getFor', (), [('duì bu qǐ', [0])]),
        ('getFor', (), [('duì_qǐ', [0])]),
        ('getForReading', (('toneMarkType', 'numbers'),),
            [('dui4bu5qi3', [0])]),
        ('getFor', (), [('Sorry', [0])]),
        ('getForTranslation', (), [('Entschuldigung', [0])]),
        ('getForTranslation', (), [('Berlin', [3])]),
        ('getForTranslation', (), [('%Berlin', [2, 3])]),
        ('getFor', (), [('Nordwind', [5])]),
        ('getFor', (), [('%Nordwind%', [4, 5])]),
        ('getForReading', (('toneMarkType', 'numbers'),), [('IC ka', [6])]),
        ('getForReading', (('toneMarkType', 'numbers'),),
            [('USB dian纜', [7])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('bo', [9])]),
        ('getFor', (('toneMarkType', 'numbers'),), [('\U000289c0bo1', [8])]),
        ]


class CFDICTMetaTest(DictionaryMetaTest, unittest.TestCase):
    DICTIONARY = 'CFDICT'

class CFDICTAccessTest(DictionaryAccessTest, unittest.TestCase):
    DICTIONARY = 'CFDICT'

class CFDICTDictionaryResultTest(DictionaryResultTest, unittest.TestCase):
    DICTIONARY = 'CFDICT'

    INSTALL_CONTENT = [
        ('對不起', '对不起', 'dui4 bu5 qi3', '/Excusez-moi!/'),
        #(u'', u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getFor', (), [('对不起', [0])]),
        ('getFor', (), [('對不起', [0])]),
        ('getFor', (), [('对_起', [0])]),
        ('getFor', (), [('duì bu qǐ', [0])]),
        ('getFor', (), [('duì_qǐ', [0])]),
        ('getForReading', (('toneMarkType', 'numbers'),),
            [('dui4bu5qi3', [0])]),
        ('getFor', (), [('excusez-moi', [0])]),
        ('getForTranslation', (), [('Excusez-moi', [0])]),
        ('getForTranslation', (), [('excusez-moi!', [0])]),
        ('getForTranslation', (), [('%-moi', [0])]),
        ]


class ParameterTest(DictionaryResultTest):
    PARAMETER_DESC = None

    def shortDescription(self):
        methodName = getattr(self, self.id().split('.')[-1])
        # get whole doc string and remove superfluous white spaces
        noWhitespaceDoc = re.sub(r'\s+', ' ', methodName.__doc__.strip())
        # remove markup for epytext format
        clearName = re.sub(r'[CLI]\{([^\}]*)}', r'\1', noWhitespaceDoc)
        # add name of reading
        return clearName + ' (for %s)' % self.PARAMETER_DESC



class EscapeParameterTest(ParameterTest, unittest.TestCase):
    """Test if non-standard escape will yield proper results."""
    DICTIONARY = 'EDICT'
    PARAMETER_DESC = 'escape'

    INSTALL_CONTENT = [
        ('東京', 'とうきょう', '/(n) Tokyo (current capital of Japan)/(P)/'),
        ('東京語', 'とうきょうご', '/(n) Tokyo dialect (esp. historical)/'),
        ('東京都', 'とうきょうと', '/(n) Tokyo Metropolitan area/'),
        ('頭胸部', 'とうきょうぶ', '/(n) cephalothorax/'),
        #(u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getForHeadword', (), [('東京', [0])]),
        ('getFor', (), [('とうきょう_', [1, 2, 3])]),
        ('getForHeadword', (), [('Tokyo', [])]),
        ('getForHeadword', (), [('東%', [0, 1, 2])]),
        ('getFor', (), [('Tokyo', [0])]),
        ('getForTranslation', (), [('Tokyyo', [0])]),
        ('getFor', (), [('_Tokyo', [])]),
        ('getForTranslation', (), [('tokyo%', [0, 1, 2])]),
        ('getForTranslation', (), [('tokyyo%', [0, 1, 2])]),
    ]

    DICTIONARY_OPTIONS = {
        'translationSearchStrategy': searchstrategy.SimpleWildcardTranslation(
            escape='y'),
        }


class CaseInsensitiveParameterTest(ParameterTest, unittest.TestCase):
    """
    Test if non-default setting of caseInsensitive will yield proper results.
    """
    DICTIONARY = 'EDICT'
    PARAMETER_DESC = 'caseInsensitive'

    INSTALL_CONTENT = [
        ('東京', 'とうきょう', '/(n) Tokyo (current capital of Japan)/(P)/'),
        ('東京語', 'とうきょうご', '/(n) Tokyo dialect (esp. historical)/'),
        ('東京都', 'とうきょうと', '/(n) Tokyo Metropolitan area/'),
        ('頭胸部', 'とうきょうぶ', '/(n) cephalothorax/'),
        #(u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getFor', (), [('Tokyo', [0])]),
        ('getFor', (), [('tokyo', [])]),
        ('getForTranslation', (), [('tokyo%', [])]),
        ('getForTranslation', (), [('Tokyo%', [0, 1, 2])]),
    ]

    DICTIONARY_OPTIONS = {
        'translationSearchStrategy': searchstrategy.SimpleWildcardTranslation(
            caseInsensitive=False),
        }


class WildcardParameterTest(ParameterTest, unittest.TestCase):
    """
    Test if non-default settings of wildcards will yield proper results.
    """
    DICTIONARY = 'EDICT'
    PARAMETER_DESC = 'singleCharacter/multipleCharacters'

    INSTALL_CONTENT = [
        ('東京', 'とうきょう', '/(n) Tokyo% (current capital of Japan)/(P)/'),
        ('東京', 'とうきょう', '/(n) Tokyo_ (current capital of Japan)/(P)/'),
        ('東京語', 'とうきょうご', '/(n) Tokyo dialect (esp. historical)/'),
        ('東京都', 'とうきょうと', '/(n) Tokyo Metropolitan area/'),
        ('頭胸部', 'とうきょうぶ', '/(n) cephalothorax/'),
        #(u'', u'', u''),
        ]

    ACCESS_RESULTS = [
        ('getFor', (), [('Tokyo', [])]),
        ('getForTranslation', (), [('Tokyo%', [0])]),
        ('getForTranslation', (), [('tokyo%', [0])]),
        ('getForTranslation', (), [('Tokyo*', [0, 1, 2, 3])]),
        ('getForTranslation', (), [('Tokyo?', [0, 1])]),
        ('getForTranslation', (), [('Tokyo_', [1])]),
    ]

    DICTIONARY_OPTIONS = {
        'translationSearchStrategy': searchstrategy.SimpleWildcardTranslation(
            singleCharacter='?', multipleCharacters='*'),
        }
