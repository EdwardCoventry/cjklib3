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
Unit tests for :mod:`cjklib.characterlookup`.
"""

# pylint: disable-msg=E1101
#  testcase attributes and methods are only available in concrete classes

import re
import unittest

from cjklib.reading import ReadingFactory
from cjklib import characterlookup
from cjklib import exception
from cjklib.test import (NeedsDatabaseTest, attr, DatabaseConnectorMock,
    EngineMock)

class CharacterLookupTest(NeedsDatabaseTest):
    """
    Base class for testing the
    :class:`~cjklib.characterlookup.CharacterLookup` class.
    """
    def setUp(self):
        NeedsDatabaseTest.setUp(self)
        self.characterLookup = characterlookup.CharacterLookup('T',
            dbConnectInst=self.db)

    def shortDescription(self):
        methodName = getattr(self, self.id().split('.')[-1])
        # get whole doc string and remove superfluous white spaces
        noWhitespaceDoc = re.sub('\s+', ' ', methodName.__doc__.strip())
        # remove markup for epytext format
        return re.sub('[CLI]\{([^\}]*)}', r'\1', noWhitespaceDoc)


class CharacterLookupMetaTest(CharacterLookupTest, unittest.TestCase):
    def testInitialization(self):
        """Test initialisation."""
        # test if locales are accepted
        for locale in 'TCJKV':
            characterlookup.CharacterLookup(locale, dbConnectInst=self.db)

        # test if locale is rejected
        self.assertRaises(ValueError, characterlookup.CharacterLookup, 'F',
            dbConnectInst=self.db)

        # test default database connector
        characterlookup.CharacterLookup('T')

        # test if character domain 'Unicode' is accepted
        characterlookup.CharacterLookup('T', 'Unicode', dbConnectInst=self.db)

        # test if character domain is accepted
        from sqlalchemy import Table, Column, String
        domain = 'MyDomain'
        tableObj = Table(domain + 'Set', self.db.metadata,
            Column('ChineseCharacter', String), useexisting=True)
        mydb = DatabaseConnectorMock(self.db,
            mockTables=[domain + 'Set'], mockTableDefinition=[tableObj])
        characterlookup.CharacterLookup('T', domain, dbConnectInst=mydb)
        self.db.metadata.remove(tableObj)

        # test if character domain is rejected
        domain = 'MyDomain'
        mydb = DatabaseConnectorMock(self.db, mockNonTables=[domain + 'Set'])
        self.assertRaises(ValueError, characterlookup.CharacterLookup, 'T',
            domain, dbConnectInst=mydb)

        # test if character domain is rejected
        domain = 'MyOtherDomain'
        tableObj = Table(domain + 'Set', self.db.metadata,
            Column('SomeColumn', String), useexisting=True)
        mydb = DatabaseConnectorMock(self.db,
            mockTables=[domain + 'Set'], mockTableDefinition=[tableObj])
        self.assertRaises(ValueError, characterlookup.CharacterLookup, 'T',
            domain, dbConnectInst=mydb)
        self.db.metadata.remove(tableObj)

    def testAvailableCharacterDomains(self):
        """Test if ``getAvailableCharacterDomains()`` returns proper domains."""
        # test default domain
        self.assertTrue('Unicode' \
            in self.characterLookup.getAvailableCharacterDomains())

        # test provided domain
        from sqlalchemy import Table, Column, String
        domain = 'MyDomain'
        tableObj = Table(domain + 'Set', self.db.metadata,
            Column('ChineseCharacter', String), useexisting=True)
        mydb = DatabaseConnectorMock(self.db,
            mockTables=[domain + 'Set'], mockTableDefinition=[tableObj])
        cjk = characterlookup.CharacterLookup('T', dbConnectInst=mydb)
        self.assertTrue(domain in cjk.getAvailableCharacterDomains())
        self.db.metadata.remove(tableObj)

        # test domain not included
        domain = 'MyDomain'
        mydb = DatabaseConnectorMock(self.db,
            mockNonTables=[domain + 'Set'])
        cjk = characterlookup.CharacterLookup('T', dbConnectInst=mydb)
        self.assertTrue(domain not in cjk.getAvailableCharacterDomains())

        # test domain not included
        domain = 'MyOtherDomain'
        tableObj = Table(domain + 'Set', self.db.metadata,
            Column('SomeColumn', String), useexisting=True)
        mydb = DatabaseConnectorMock(self.db,
            mockTables=[domain + 'Set'], mockTableDefinition=[tableObj])
        cjk = characterlookup.CharacterLookup('T', dbConnectInst=mydb)
        self.assertTrue(domain not in cjk.getAvailableCharacterDomains())
        self.db.metadata.remove(tableObj)


class CharacterLookupCharacterDomainTest(CharacterLookupTest,
    unittest.TestCase):

    def testCharacterDomainInUnicode(self):
        """
        Tests if all character domains are included in the maximum Unicode
        domain.
        """
        for domain in self.characterLookup.getAvailableCharacterDomains():
            characterLookupDomain = characterlookup.CharacterLookup('T',
                domain, dbConnectInst=self.db)
            domainChars = [c for c \
                in characterLookupDomain.getDomainCharacterIterator()]
            self.assertTrue(domainChars \
                == self.characterLookup.filterDomainCharacters(domainChars))

    @attr('slow')
    def testDomainCharsAccepted(self):
        """Test if all characters in the character domain are accepted."""
        for domain in self.characterLookup.getAvailableCharacterDomains():
            characterLookupDomain = characterlookup.CharacterLookup('T',
                domain, dbConnectInst=self.db)
            for char in characterLookupDomain.getDomainCharacterIterator():
                self.assertTrue(characterLookupDomain.isCharacterInDomain(char))

    def testFilterIdentityOnSelf(self):
        """
        Test if filterDomainCharacters operates as identity on characters from
        domain.
        """
        for domain in self.characterLookup.getAvailableCharacterDomains():
            characterLookupDomain = characterlookup.CharacterLookup('T',
                domain, dbConnectInst=self.db)
            domainChars = [c for c \
                in characterLookupDomain.getDomainCharacterIterator()]
            self.assertTrue(domainChars \
                == characterLookupDomain.filterDomainCharacters(domainChars))


class CharacterLookupStrokesTest(CharacterLookupTest, unittest.TestCase):

    def testUnicodeNamesMatchAbbreviations(self):
        """
        Tests if the stroke form names by Unicode match the abbreviations
        defined here.
        """
        import unicodedata
        for strokeCP in range(int('31C0', 16), int('31EF', 16)+1):
            stroke = chr(strokeCP)
            try:
                abbrev = unicodedata.name(stroke).replace('CJK STROKE ', '')
            except ValueError:
                continue
            try:
                self.assertEqual(stroke,
                    self.characterLookup.getStrokeForAbbrev(abbrev))
            except ValueError:
                self.fail("Abbreviation '%s' not supported" % abbrev)


class CharacterLookupStrokeOrderTest(CharacterLookupTest, unittest.TestCase):

    @attr('slow')
    def testStrokeOrderMatchesStrokeCount(self):
        """
        Tests if stroke order information returned by ``getStrokeOrder`` matches
        stroke count returned by ``getStrokeCount``.
        """
        cjk = characterlookup.CharacterLookup('T', 'GlyphInformation',
            dbConnectInst=self.db)
        for char in cjk.getDomainCharacterIterator():
            try:
                strokeOrder = cjk.getStrokeOrder(char, includePartial=True)
                strokeCount = cjk.getStrokeCount(char)
                self.assertTrue(len(strokeOrder) == strokeCount,
                    "Stroke count %d does not match stroke order (%d)"
                    % (strokeCount, len(strokeOrder))
                    + " for character '%s'" % char)
            except exception.NoInformationError:
                continue


class CharacterLookupReadingMethodsTest(CharacterLookupTest, unittest.TestCase):
    """
    Runs consistency checks on the reading methods of the
    :class:`~cjklib.characterlookup.CharacterLookup` class.

    .. todo::
        * Impl: include script table from Unicode 5.2.0 to get character ranges
          for Hangul and Kana
    """
    DIALECTS = {}

    SPECIAL_ENTITY_LIST = {}

    def setUp(self):
        CharacterLookupTest.setUp(self)
        self.f = ReadingFactory(dbConnectInst=self.db)

    def testReadingMappingAvailability(self):
        """
        Test if the readings under
        ``CharacterLookup.CHARARACTER_READING_MAPPING`` are available for
        conversion.
        """
        # mock to simulate availability of all tables in
        #   characterLookup.CHARARACTER_READING_MAPPING
        tables = [table for table, _ \
            in list(self.characterLookup.CHARARACTER_READING_MAPPING.values())]
        self.characterLookup.db.engine = EngineMock(
                self.characterLookup.db.engine, mockTables=tables)

        for reading in self.characterLookup.CHARARACTER_READING_MAPPING:
            # only if table exists
            table, _ = self.characterLookup.CHARARACTER_READING_MAPPING[reading]

            self.assertTrue(
                self.characterLookup.hasMappingForReadingToCharacter(reading))
            self.assertTrue(
                self.characterLookup.hasMappingForCharacterToReading(reading))

        # test proper checking for all known readings
        for reading in self.f.getSupportedReadings():
            self.assertTrue(
                self.characterLookup.hasMappingForReadingToCharacter(reading) \
                in [True, False])
            self.assertTrue(
                self.characterLookup.hasMappingForCharacterToReading(reading) \
                in [True, False])

    @attr('slow')
    def testGetCharactersForReadingAcceptsAllEntities(self):
        """Test if ``getCharactersForReading`` accepts all reading entities."""
        for reading in self.f.getSupportedReadings():
            if not self.characterLookup.hasMappingForReadingToCharacter(
                reading):
                continue

            dialects = [{}]
            if reading in self.DIALECTS:
                dialects.extend(self.DIALECTS[reading])

            for dialect in dialects:
                if hasattr(self.f.getReadingOperatorClass(reading),
                    'getReadingEntities'):
                    entities = self.f.getReadingEntities(reading, **dialect)
                elif reading in self.SPECIAL_ENTITY_LIST:
                    entities = self.SPECIAL_ENTITY_LIST[reading]
                else:
                    continue

                for entity in entities:
                    try:
                        results = self.characterLookup.getCharactersForReading(
                            entity, reading, **dialect)

                        self.assertEqual(type(results), type([]),
                            "Method getCharactersForReading() doesn't return" \
                                + " a list for entity %s " % repr(entity) \
                        + ' (reading %s, dialect %s)' % (reading, dialect))

                        for entry in results:
                            self.assertEqual(len(entry), 1,
                                "Entry %s in result for %s has length != 1" \
                                    % (repr(entry), repr(entity)) \
                                + ' (reading %s, dialect %s)' \
                                % (reading, dialect))
                    except exception.UnsupportedError:
                        pass
                    except exception.ConversionError:
                        pass


class CharacterLookupReferenceTest(CharacterLookupTest):
    METHOD_NAME = None

    def shortDescription(self):
        methodName = getattr(self, self.id().split('.')[-1])
        # get whole doc string and remove superfluous white spaces
        noWhitespaceDoc = re.sub('\s+', ' ', methodName.__doc__.strip())
        # remove markup for epytext format
        clearName = re.sub('[CL]\{([^\}]*)}', r'\1', noWhitespaceDoc)
        # add name of reading
        return clearName + ' (for %s)' % self.METHOD_NAME

    def getCharacterLookupInst(self, options):
        if not hasattr(self, '_instanceDict'):
            self._instanceDict = {}
        if options not in self._instanceDict:
            self._instanceDict[options] = characterlookup.CharacterLookup(
                dbConnectInst=self.db, *options)

        return self._instanceDict[options]

    def testMethodReferences(self):
        """Test if the given references are reached"""
        for options, references in self.REFERENCE_LIST:
            cjk = self.getCharacterLookupInst(options)
            method = getattr(cjk, self.METHOD_NAME)

            for methodArgs, methodOptions, target in references:
                result = method(*methodArgs, **methodOptions)
                self.assertEqual(result, target,
                    "Target %s not reached for input %s: %s" \
                        % (repr(target), repr((methodArgs, methodOptions)),
                            repr(result)))


class CharacterLookupFilterDomainCharactersReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'filterDomainCharacters'

    REFERENCE_LIST = [
        (('T', 'Unicode'), [
            ((['说', '説', '說', '丷', 'か', '국', '\U000200d3'], ), {},
                ['说', '説', '說', '丷', '\U000200d3']),
            ]),
        (('T', 'BIG5'), [
            ((['说', '説', '說', '丷', 'か', '국'], ), {}, ['說']),
            ]),
        (('T', 'GB2312'), [
            ((['说', '説', '說', '丷', 'か', '국'], ), {}, ['说']),
            ]),
        ]


class CharacterLookupIsCharacterInDomainReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'isCharacterInDomain'

    REFERENCE_LIST = [
        (('T', 'Unicode'), [
            (('说', ), {}, True),
            (('説', ), {}, True),
            (('說', ), {}, True),
            (('丷', ), {}, True),
            (('か', ), {}, False),
            (('국', ), {}, False),
            (('\U000200d3', ), {}, True),
            ]),
        (('T', 'BIG5'), [
            (('说', ), {}, False),
            (('説', ), {}, False),
            (('說', ), {}, True),
            (('丷', ), {}, False),
            (('か', ), {}, False),
            (('국', ), {}, False),
            (('\U000200d3', ), {}, False),
            ]),
        (('T', 'GB2312'), [
            (('说', ), {}, True),
            (('説', ), {}, False),
            (('說', ), {}, False),
            (('丷', ), {}, False),
            (('か', ), {}, False),
            (('국', ), {}, False),
            (('\U000200d3', ), {}, False),
            ]),
        ]


class CharacterLookupGetReadingForCharacterReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getReadingForCharacter'

    REFERENCE_LIST = [
        (('T', ), [
            (('中', 'Pinyin'), {}, ['zhōng', 'zhòng']),
            (('漢', 'Hangul'), {}, ['한']),
            (('漢', 'MandarinBraille'), {}, ['⠓⠧⠆', '⠞⠧⠁']),
            ]),
        ]


class CharacterLookupGetCharactersForReadingReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharactersForReading'

    REFERENCE_LIST = [
        (('T', 'GB2312'), [
            (('èr', 'Pinyin'), {}, ['二', '佴', '贰']),
            ]),
        (('T', 'BIG5'), [
            (('m\u0300h', 'CantoneseYale'), {}, ['唔', '嘸']),
            ]),
        ]


class CharacterLookupGetCharacterVariantsReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterVariants'

    REFERENCE_LIST = [
        (('T', ), [
            (('台', 'T'), {}, ['\u53f0', '\u6aaf', '\u81fa', '\u98b1']),
            ]),
        (('T', ), [
            (('台', 'S'), {}, ['\u53f0']),
            ]),
        ]


class CharacterLookupGetAllCharacterVariantsReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getAllCharacterVariants'

    REFERENCE_LIST = [
        (('T', ), [
            (('他', ), {}, [('\u5979', 'M'), ('\u7260', 'M')]),
            ]),
        ]


class CharacterLookupGetDefaultGlyphReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getDefaultGlyph'

    REFERENCE_LIST = [
        (('T', ), [
            (('台', ), {}, 0),
            ]),
        ]


class CharacterLookupGetCharacterGlyphsReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterGlyphs'

    REFERENCE_LIST = [
        (('T', ), [
            (('口', ), {}, [0]),
            ]),
        ]


class CharacterLookupGetStrokeCountReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getStrokeCount'

    REFERENCE_LIST = [
        (('T', ), [
            (('口', ), {}, 3),
            ]),
        ]


class CharacterLookupGetStrokeForAbbrevReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getStrokeForAbbrev'

    REFERENCE_LIST = [
        (('T', ), [
            (('HZG', ), {}, '㇆'),
            ]),
        ]


class CharacterLookupGetStrokeForNameReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getStrokeForName'

    REFERENCE_LIST = [
        (('T', ), [
            (('提', ), {}, '㇀'),
            ]),
        ]


class CharacterLookupGetStrokeOrderReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getStrokeOrder'

    REFERENCE_LIST = [
        (('T', ), [
            (('口', ), {}, ['㇑', '㇕', '㇐']),
            ]),
        ]


class CharacterLookupGetStrokeOrderAbbrevReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getStrokeOrderAbbrev'

    REFERENCE_LIST = [
        (('T', ), [
            (('口', ), {}, 'S-HZ-H'),
            ]),
        ]


class CharacterLookupGetCharacterKangxiRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterKangxiRadicalIndex'

    REFERENCE_LIST = [
        (('T', ), [
            (('他', ), {}, 9),
            ]),
        ]


class CharacterLookupGetCharacterKangxiRadicalResidualStrokeCountReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterKangxiRadicalResidualStrokeCount'

    REFERENCE_LIST = [
        (('T', ), [
            (('他', ), {}, [('\u4ebb', 0, '\u2ff0', 0, 3)]),
            ]),
        ]


class CharacterLookupGetCharacterRadicalResidualStrokeCountReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterRadicalResidualStrokeCount'

    REFERENCE_LIST = [
        (('T', ), [
            (('他', 9), {}, [('\u4ebb', 0, '\u2ff0', 0, 3)]),
            ]),
        ]


class CharacterLookupGetCharacterKangxiResidualStrokeCountReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterKangxiResidualStrokeCount'

    REFERENCE_LIST = [
        (('T', ), [
            (('他', ), {}, 3),
            ]),
        ]


class CharacterLookupGetCharacterResidualStrokeCountReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterResidualStrokeCount'

    REFERENCE_LIST = [
        (('T', ), [
            (('他', 9), {}, 3),
            ]),
        ]


class CharacterLookupGetCharactersForKangxiRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharactersForKangxiRadicalIndex'

    REFERENCE_LIST = [
        (('C', 'GB2312'), [
            ((214, ), {}, ['\u9fa0']),
            ]),
        ]


class CharacterLookupGetCharactersForRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharactersForRadicalIndex'

    REFERENCE_LIST = [
        (('C', 'GB2312'), [
            ((214, ), {}, ['\u7039', '\u9fa0']),
            ]),
        ]


class CharacterLookupGetResidualStrokeCountForKangxiRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getResidualStrokeCountForKangxiRadicalIndex'

    REFERENCE_LIST = [
        (('C', 'GB2312'), [
            ((214, ), {}, [('\u9fa0', 0)]),
            ]),
        ]


class CharacterLookupGetResidualStrokeCountForRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getResidualStrokeCountForRadicalIndex'

    REFERENCE_LIST = [
        (('C', 'GB2312'), [
            ((214, ), {}, [('\u7039', 3), ('\u9fa0', 0)]),
            ]),
        ]


class CharacterLookupGetKangxiRadicalFormReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getKangxiRadicalForm'

    REFERENCE_LIST = [
        (('T', ), [
            ((214, ), {}, '\u2fd5'),
            ]),
        ]


class CharacterLookupGetKangxiRadicalVariantFormsReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getKangxiRadicalVariantForms'

    REFERENCE_LIST = [
        (('T', ), [
            ((149, ), {}, []),
            ]),
        (('C', ), [
            ((149, ), {}, ['\u2ec8']),
            ]),
        ]


class CharacterLookupGetKangxiRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getKangxiRadicalIndex'

    REFERENCE_LIST = [
        (('T', ), [
            (('⿕', ), {}, 214),
            ]),
        ]


class CharacterLookupGetKangxiRadicalIndexReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getKangxiRadicalIndex'

    REFERENCE_LIST = [
        (('T', ), [
            (('⿕', ), {}, 214),
            ]),
        ]


class CharacterLookupGetKangxiRadicalRepresentativeCharactersReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getKangxiRadicalRepresentativeCharacters'

    REFERENCE_LIST = [
        (('T', ), [
            ((149, ), {}, ['\u2f94', '\u8a00', '\u8a01']),
            ]),
        (('C', ), [
            ((149, ), {}, ['\u2ec8', '\u2f94', '\u8a00', '\u8a01',
                '\u8ba0']),
            ]),
        ]


class CharacterLookupIsKangxiRadicalFormOrEquivalentReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'isKangxiRadicalFormOrEquivalent'

    REFERENCE_LIST = [
        (('T', ), [
            (('讠', ), {}, False),
            ]),
        (('C', ), [
            (('讠', ), {}, True),
            ]),
        ]


class CharacterLookupIsRadicalCharReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'isRadicalChar'

    REFERENCE_LIST = [
        (('T', ), [
            (('⿕', ), {}, True), (('龠', ), {}, False),
            ]),
        ]


class CharacterLookupGetRadicalFormEquivalentCharacterReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getRadicalFormEquivalentCharacter'

    REFERENCE_LIST = [
        (('T', ), [
            (('⿕', ), {}, '龠'),
            ]),
        ]


class CharacterLookupGetCharacterEquivalentRadicalFormsReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharacterEquivalentRadicalForms'

    REFERENCE_LIST = [
        (('T', ), [
            (('网', ), {}, ['\u2f79', '\u2eb3', '\u2eb4']),
            ]),
        ]


class CharacterLookupGetCharactersForComponentsReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getCharactersForComponents'

    REFERENCE_LIST = [
        (('C', 'GB2312'), [
            ((['⿕', '氵'], ), {}, [('\u7039', 0)]),
            ]),
        ]


class CharacterLookupGetDecompositionEntriesReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'getDecompositionEntries'

    REFERENCE_LIST = [
        (('C', 'GB2312'), [
            (('瀹', ), {}, [['\u2ff0', ('\u6c35', 0), ('\u9fa0', 0)]]),
            ]),
        ]


class CharacterLookupIsComponentInCharacterReferenceTest(
    CharacterLookupReferenceTest, unittest.TestCase):
    METHOD_NAME = 'isComponentInCharacter'

    REFERENCE_LIST = [
        (('T', ), [
            (('女', '好'), {}, True),
            (('女', '他'), {}, False),
            ]),
        ]
