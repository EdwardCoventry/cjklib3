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
Unit tests for :mod:`cjklib.reading.converter`.

.. todo::
    * Impl: Add second dimension to consistency check for converting between
      dialect forms for all entities. Use cartesian product
      ``option_list x dialects``
"""

# pylint: disable-msg=E1101
#  testcase attributes and methods are only available in concrete classes

import re
import types
import unittest

from cjklib.reading import ReadingFactory, converter, operator
from cjklib import exception
from cjklib.test import NeedsDatabaseTest, attr

from cjklib.util import titlecase, istitlecase

class ReadingConverterTest(NeedsDatabaseTest):
    """
    Base class for testing of
    :class:`~cjklib.reading.converter.ReadingConverter` classes."""
    CONVERSION_DIRECTION = None
    """Tuple of reading names for conversion from reading A to reading B."""

    def setUp(self):
        NeedsDatabaseTest.setUp(self)
        self.fromReading, self.toReading = self.CONVERSION_DIRECTION

        for clss in list(self.getReadingConverterClasses().values()):
            if self.CONVERSION_DIRECTION in clss.CONVERSION_DIRECTIONS:
                self.readingConverterClass = clss
                break
        else:
            self.readingConverterClass = None

        self.f = ReadingFactory(dbConnectInst=self.db)

    def shortDescription(self):
        methodName = getattr(self, self.id().split('.')[-1])
        # get whole doc string and remove superfluous white spaces
        noWhitespaceDoc = re.sub('\s+', ' ', methodName.__doc__.strip())
        # remove markup for epytext format
        clearName = re.sub('[CLI]\{([^\}]*)}', r'\1', noWhitespaceDoc)
        # add information about conversion direction
        return clearName + ' (for %s to %s)' % self.CONVERSION_DIRECTION

    @staticmethod
    def getReadingConverterClasses():
        """
        Gets all classes from the reading module that implement
        :class:`~cjklib.reading.converter.ReadingConverter`.

        :rtype: dictionary of string class pairs
        :return: dictionary of all classes inheriting form
            :class:`~cjklib.reading.converter.ReadingConverter`
        """
        readingConverterClasses = {}

        # get all non-abstract classes that inherit from ReadingConverter
        readingConverterClasses = dict([(clss.__name__, clss) \
            for clss in list(converter.__dict__.values()) \
            if type(clss) in [type, type] \
            and issubclass(clss, converter.ReadingConverter) \
            and clss.CONVERSION_DIRECTIONS])

        return readingConverterClasses

    def tearDown(self):
        # get rid of the possibly > 1000 instances
        self.f.clearCache()


class ReadingConverterConsistencyTest(ReadingConverterTest):
    """
    Base class for consistency testing of
    :class:`~cjklib.reading.converter.ReadingConverter` classes.
    """

    OPTIONS_LIST = []
    """
    List of option configurations, simmilar to ``test.readingoperator.DIALECTS``.
    """

    FROM_DIALECTS = []
    """List of dialects of the source reading."""

    TO_DIALECTS = []
    """List of dialects of the target reading."""

    def testReadingConverterUnique(self):
        """Test if only one ReadingConverter exists for each reading."""
        seen = False

        for clss in list(self.getReadingConverterClasses().values()):
            if self.CONVERSION_DIRECTION in clss.CONVERSION_DIRECTIONS:
                self.assertTrue(not seen,
                    "Conversion %s to %s has more than one converter" \
                    % self.CONVERSION_DIRECTION)
                seen = True

    def testInstantiation(self):
        """Test if given conversion can be instantiated"""
        self.assertTrue(self.readingConverterClass != None,
            "No reading converter class found" \
                + ' (conversion %s to %s)' % self.CONVERSION_DIRECTION)

        forms = []
        forms.extend(self.OPTIONS_LIST)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            # instantiate
            self.readingConverterClass(**dialect)

    def testDefaultOptions(self):
        """
        Test if option dict returned by ``getDefaultOptions()`` is well-formed
        and includes all options found in the test case's options.
        """
        defaultOptions = self.readingConverterClass.getDefaultOptions()

        self.assertEqual(type(defaultOptions), type({}),
            "Default options %s is not of type dict" % repr(defaultOptions) \
            + ' (conversion %s to %s)' % self.CONVERSION_DIRECTION)
        # test if option names are well-formed
        for option in defaultOptions:
            self.assertEqual(type(option), type(''),
                "Option %s is not of type str" % repr(option) \
                + ' (conversion %s to %s)' % self.CONVERSION_DIRECTION)

        # test all given options
        forms = []
        forms.extend(self.OPTIONS_LIST)
        if {} not in forms:
            forms.append({})
        for options in forms:
            for option in options:
                self.assertTrue(option in defaultOptions,
                    "Test case option %s not found in default options" \
                        % repr(option) \
                    + ' (conversion %s to %s, options %s)' \
                        % (self.fromReading, self.toReading, options))

        # test instantiation of default options
        defaultInstance = self.readingConverterClass(**defaultOptions)

        # check if option value changes after instantiation
        for option in defaultOptions:
            if option in ['sourceOperators', 'targetOperators']:
                continue # TODO in general forbid changing of options?
            self.assertEqual(getattr(defaultInstance, option),
                defaultOptions[option],
                "Default option value %s for %s changed on instantiation: %s" \
                    % (repr(defaultOptions[option]), repr(option),
                        repr(getattr(defaultInstance, option))) \
                + ' (conversion %s to %s)' % self.CONVERSION_DIRECTION)

        # check options against instance without explicit option dict
        instance = self.readingConverterClass()
        for option in defaultOptions:
            self.assertEqual(getattr(instance, option),
                getattr(defaultInstance, option),
                "Option value for %s unequal for default instances: %s and %s" \
                    % (repr(option), repr(getattr(instance, option)),
                        repr(getattr(defaultInstance, option))) \
                + ' (conversion %s to %s)' % self.CONVERSION_DIRECTION)

    @attr('quiteslow')
    def testLetterCaseConversion(self):
        """
        Check if letter case is transferred during conversion.
        """
        def isOneCharEntity(entity):
            return len([c for c \
                in unicodedata.normalize("NFD", str(entity)) \
                if 'a' <= c <= 'z']) == 1

        fromReadingClass = self.f.getReadingOperatorClass(self.fromReading)
        if not issubclass(fromReadingClass, operator.RomanisationOperator) \
            or 'case' not in fromReadingClass.getDefaultOptions():
            return

        toReadingClass = self.f.getReadingOperatorClass(self.toReading)
        if not issubclass(toReadingClass, operator.RomanisationOperator) \
            or 'case' not in toReadingClass.getDefaultOptions():
            return

        import unicodedata

        forms = []
        forms.extend(self.OPTIONS_LIST)
        if {} not in forms:
            forms.append({})
        # TODO extend once unit test includes reading dialects
        entities = self.f.getReadingEntities(self.fromReading)
        for options in forms:
            for entity in entities:
                try:
                    toEntity = self.f.convert(entity, self.fromReading,
                        self.toReading, **options)
                    self.assertTrue(toEntity.islower(),
                        'Mismatch in letter case for conversion %s to %s' \
                            % (repr(entity), repr(toEntity)) \
                        + ' (conversion %s to %s, options %s)' \
                            % (self.fromReading, self.toReading, options))

                    if 'sourceOptions' in options \
                        and 'case' in options['sourceOptions'] \
                        and options['sourceOptions']['case'] == 'lower':
                        # the following conversions only hold for upper case
                        continue

                    toEntity = self.f.convert(entity.upper(), self.fromReading,
                        self.toReading, **options)
                    self.assertTrue(toEntity.isupper(),
                        'Mismatch in letter case for conversion %s to %s' \
                            % (repr(entity.upper()), repr(toEntity)) \
                        + ' (conversion %s to %s, options %s)' \
                            % (self.fromReading, self.toReading, options))

                    ownOptions = options.copy()
                    if 'targetOptions' not in ownOptions:
                        ownOptions['targetOptions'] = {}
                    ownOptions['targetOptions']['case'] = 'lower' # TODO
                    toEntity = self.f.convert(entity.upper(), self.fromReading,
                        self.toReading, **ownOptions)

                    self.assertTrue(toEntity.islower(),
                        'Mismatch in conversion to lower case from %s to %s' \
                            % (repr(entity.upper()), repr(toEntity)) \
                        + ' (conversion %s to %s, options %s)' \
                            % (self.fromReading, self.toReading, options))

                    toEntities = self.f.convert(titlecase(entity),
                        self.fromReading, self.toReading, **options)

                    # trade-off for one-char entities: upper-case goes for title
                    self.assertTrue(istitlecase(toEntities) \
                            or (toEntities.isupper() \
                                and (isOneCharEntity(toEntities) \
                                    or isOneCharEntity(entity))),
                        'Mismatch in title case for conversion %s to %s' \
                            % (repr(titlecase(entity)), repr(toEntities)) \
                        + ' (conversion %s to %s, options %s)' \
                            % (self.fromReading, self.toReading, options))
                except exception.ConversionError:
                    pass

    @attr('quiteslow')
    def testConversionValid(self):
        """
        Check if converted entities are valid in the target reading.
        """
        fromReadingClass = self.f.getReadingOperatorClass(self.fromReading)
        if not hasattr(fromReadingClass, 'getReadingEntities'):
            return

        forms = []
        forms.extend(self.OPTIONS_LIST)
        if {} not in forms:
            forms.append({})

        sourceDialects = []
        sourceDialects.extend(self.FROM_DIALECTS)
        if {} not in sourceDialects:
            sourceDialects.append({})
        targetDialects = []
        targetDialects.extend(self.TO_DIALECTS)
        if {} not in targetDialects:
            targetDialects.append({})

        for options in self.OPTIONS_LIST:
            for sourceDialect in sourceDialects:
                entities = self.f.getReadingEntities(self.fromReading,
                    **sourceDialect)
                for targetDialect in targetDialects:
                    myOptions = options.copy()
                    myOptions['sourceOptions'] = sourceDialect
                    myOptions['targetOptions'] = targetDialect
                    for entity in entities:
                        try:
                            toEntities = self.f.convert(entity,
                                self.fromReading, self.toReading, **myOptions)
                        except exception.ConversionError:
                            continue

                        try:
                            decomposition = self.f.decompose(toEntities,
                                self.toReading, **targetDialect)
                        except exception.DecompositionError:
                            self.fail("Error decomposing conversion result" \
                                " from %s: %s" \
                                    % (repr(entity), repr(toEntities)) \
                                + ' (conversion %s (%s) to %s (%s)' \
                                    % (self.fromReading, repr(sourceDialect),
                                        self.toReading, repr(targetDialect)) \
                                + ', options %s)' % options)

                        if hasattr(self, 'cleanDecomposition'):
                            cleanDecomposition = self.cleanDecomposition(
                                decomposition, self.toReading, **targetDialect)
                        else:
                            cleanDecomposition = decomposition

                        for toEntity in cleanDecomposition:
                            self.assertTrue(
                                self.f.isReadingEntity(toEntity, self.toReading,
                                    **targetDialect),
                                "Conversion from %s to %s" \
                                    % (repr(entity), repr(toEntities)) \
                                + " includes an invalid entity: %s" \
                                    % repr(toEntity) \
                                + ' (conversion %s (%s) to %s (%s)' \
                                    % (self.fromReading, repr(sourceDialect),
                                        self.toReading, repr(targetDialect)) \
                                + ', options %s)' % options)


class ReadingConverterTestCaseCheck(NeedsDatabaseTest, unittest.TestCase):
    """
    Checks if every :class:`~cjklib.reading.converter.ReadingConverter` has
    its own
    :class:`~cjklib.test.readingconverter.ReadingConverterConsistencyTest`.
    """
    def testEveryConverterHasConsistencyTest(self):
        """
        Check if every reading has a test case.
        """
        testClasses = self.getReadingConverterConsistencyTestClasses()
        testClassReadingNames = [clss.CONVERSION_DIRECTION for clss \
            in testClasses]
        self.f = ReadingFactory(dbConnectInst=self.db)

        for clss in self.f.getReadingConverterClasses():
            for direction in clss.CONVERSION_DIRECTIONS:
                self.assertTrue(direction in testClassReadingNames,
                    "Conversion from %s to %s" % direction \
                    + "has no ReadingOperatorConsistencyTest")

    @staticmethod
    def getReadingConverterConsistencyTestClasses():
        """
        Gets all classes implementing
        :class:`cjklib.test.readingconverter.ReadingConverterConsistencyTest`.

        :rtype: list
        :return: list of all classes inheriting form
            :class:`cjklib.test.readingconverter.ReadingConverterConsistencyTest`
        """
        # get all non-abstract classes that inherit from
        #   ReadingConverterConsistencyTest
        testModule = __import__("cjklib.test.readingconverter")
        testClasses = [clss for clss \
            in list(testModule.test.readingconverter.__dict__.values()) \
            if type(clss) in [type, type] \
            and issubclass(clss, ReadingConverterConsistencyTest) \
            and clss.CONVERSION_DIRECTION]

        return testClasses


class ReadingConverterReferenceTest(ReadingConverterTest):
    """
    Base class for testing of references against
    :class:`~cjklib.reading.converter.ReadingConverter` classes.
    These tests assure that the given values are returned correctly.
    """
    CONVERSION_REFERENCES = []
    """
    References to test ``decompose()`` operation.
    List of options/reference tuples, schema:
    ({options, sourceOptions={}, targetOptions={}}, [(reference, target)])
    """

    def testConversionReferences(self):
        """Test if the given conversion references are reached."""
        for options, references in self.CONVERSION_REFERENCES:
            for reference, target in references:
                args = [reference, self.fromReading, self.toReading]

                if type(target) in [type, type] \
                    and issubclass(target, Exception):
                    self.assertRaises(target, self.f.convert, *args, **options)
                else:
                    string = self.f.convert(*args, **options)

                    self.assertEqual(string, target,
                        "Conversion for %s to %s failed: %s" \
                            % (repr(reference), repr(target), repr(string)) \
                        + ' (conversion %s to %s, options %s)' \
                            % (self.fromReading, self.toReading, options))


class CantoneseYaleDialectConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('CantoneseYale', 'CantoneseYale')


# TODO
class CantoneseYaleDialectReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('CantoneseYale', 'CantoneseYale')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {}, 'targetOptions': {'toneMarkType': 'numbers'}}, [
            ('gwóngjāuwá', 'gwong2jau1wa2'),
            ('gwóngjàuwá', 'gwong2jau1wa2'),
            ('GWÓNGJĀUWÁ', 'GWONG2JAU1WA2'),
            ('sīsísisìhsíhsihsīksiksihk', 'si1si2si3si4si5si6sik1sik3sik6'),
            ('SÌSÍSISÌHSÍHSIHSĪKSIKSIHK', 'SI1SI2SI3SI4SI5SI6SIK1SIK3SIK6'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ('gwong2jau1wa2', 'gwóngjāuwá'),
            ('gwong2jauwa2', exception.ConversionError),
            ('GWONG2JAU1WA2', 'GWÓNGJĀUWÁ'),
            ('si1si2si3si4si5si6sik1sik3sik6', 'sīsísisìhsíhsihsīksiksihk'),
            ('SI1SI2SI3SI4SI5SI6SIK1SIK3SIK6', 'SĪSÍSISÌHSÍHSIHSĪKSIKSIHK'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers',
            'yaleFirstTone': '1stToneFalling'},
            'targetOptions': {}}, [
            ('gwong2jau1wa2', 'gwóngjàuwá'),
            ('si1si2si3si4si5si6sik1sik3sik6', 'sìsísisìhsíhsihsīksiksihk'),
            ('SI1SI2SI3SI4SI5SI6SIK1SIK3SIK6', 'SÌSÍSISÌHSÍHSIHSĪKSIKSIHK'),
            ]),
        ({'sourceOptions': {'strictDiacriticPlacement': True},
            'targetOptions': {'toneMarkType': 'numbers'}}, [
            ('gwóngjaùwá', 'gwóngjaùwá'),
            ]),
        ({'sourceOptions': {'strictSegmentation': True,
            'strictDiacriticPlacement': True},
            'targetOptions': {'toneMarkType': 'numbers'}}, [
            ('gwóngjaùwá', exception.DecompositionError),
            ]),
        ]


class JyutpingDialectConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Jyutping', 'Jyutping')


## TODO
#class JyutpingDialectReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('Jyutping', 'Jyutping')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class JyutpingYaleConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Jyutping', 'CantoneseYale')

    OPTIONS_LIST = [{'yaleFirstTone': '1stToneFalling'}]


# TODO
class JyutpingYaleReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Jyutping', 'CantoneseYale')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('gwong2zau1waa2', 'gwóngjāuwá'),
            ('gwong2yau1waa2', exception.CompositionError),
            ('GWONG2ZAU1WAA2', 'GWÓNGJĀUWÁ'),
            ]),
        ]


class YaleJyutpingConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('CantoneseYale', 'Jyutping')


# TODO
class YaleJyutpingReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('CantoneseYale', 'Jyutping')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('gwóngjāuwá', 'gwong2zau1waa2'),
            ('gwóngjàuwá', 'gwong2zau1waa2'),
            ('GWÓNGJĀUWÁ', 'GWONG2ZAU1WAA2'),
            ]),
        ]


class PinyinICUTest(NeedsDatabaseTest, unittest.TestCase):
    """Test Pinyin tonemark conversion on ICU transformation rule."""
    CONVERSION_DIRECTION = ('Pinyin', 'Pinyin')

    def setUp(self):
        NeedsDatabaseTest.setUp(self)
        self.f = ReadingFactory(dbConnectInst=self.db)

        try:
            import PyICU

            self.toNumeric = PyICU.Transliterator.createInstance(
                "Latin-NumericPinyin", PyICU.UTransDirection.UTRANS_FORWARD)
            self.fromNumeric = self.toNumeric.createInverse()
        except ImportError:
            pass

    def testToneMarkPlacement(self):
        """Test Pinyin tonemark conversion on ICU transformation rule."""
        if not hasattr(self, 'toNumeric'):
            return

        for readingEntity in self.f.getReadingEntities('Pinyin'):
            if readingEntity in ('hn\u0304g', 'h\u0144g', 'h\u0148g',
                'h\u01f9g', 'n\u0304g', '\u0144g', '\u0148g',
                '\u01f9g'):
                continue
            targetEntity = self.f.convert(readingEntity, 'Pinyin', 'Pinyin',
                targetOptions={'toneMarkType': 'numbers',
                    'missingToneMark': 'fifth'})
            self.assertEqual(targetEntity,
                self.toNumeric.transliterate(readingEntity))

        for readingEntity in self.f.getReadingEntities('Pinyin',
            toneMarkType='numbers', missingToneMark='fifth'):
            if readingEntity in ('hng1', 'hng2', 'hng3', 'hng4', 'ng1', 'ng2',
                'ng3', 'ng4', 'ê1', 'ê2', 'ê3', 'ê4'):
                continue
            targetEntity = self.f.convert(readingEntity, 'Pinyin', 'Pinyin',
                sourceOptions={'toneMarkType': 'numbers',
                    'missingToneMark': 'fifth'})
            self.assertEqual(targetEntity,
                self.fromNumeric.transliterate(readingEntity))


class PinyinDialectConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'Pinyin')

    OPTIONS_LIST = [{'keepPinyinApostrophes': True},
        {'breakUpErhua': 'on'}]


class PinyinDialectReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'Pinyin')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('xīān', "xī'ān"),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ('lao3shi1', 'lǎoshī'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers', 'yVowel': 'v'},
            'targetOptions': {}}, [
            ('nv3hai2', 'nǚhái'),
            ('NV3HAI2', 'NǙHÁI'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers'},
            'targetOptions': {'shortenedLetters': True}}, [
            ('lao3shi1', 'lǎoŝī'),
            ('Zhi1shi5', 'Ẑīŝi'),
            ('Bei3jing1', 'Běijīŋ'),
            ('nü3hai2', 'nǚhái'),
            ]),
        ({'sourceOptions': {'shortenedLetters': True},
            'targetOptions': {'toneMarkType': 'numbers'}}, [
            ('lǎoŝī', 'lao3shi1'),
            ('Ẑīŝi', 'Zhi1shi5'),
            ('Běijīŋ', 'Bei3jing1'),
            ('nǚhái', 'nü3hai2'),
            ('ĉaŋ', 'chang5'),
            ]),
        ({'sourceOptions': {'pinyinDiacritics': ('\u0304', '\u0301',
                '\u0306', '\u0300')},
            'targetOptions': {}}, [
            ('Wŏ peí nĭ qù Xīān.', "Wǒ péi nǐ qù Xī'ān."),
            ]),
        ]


class WadeGilesDialectConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'WadeGiles')


class WadeGilesDialectReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'WadeGiles')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ("Ssŭ1ma3 Ch’ien1", 'Ssŭ¹-ma³ Ch’ien¹'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers',
            'wadeGilesApostrophe': "'"}, 'targetOptions': {}}, [
            ("Ssŭ1ma3 Ch'ien1", 'Ssŭ¹-ma³ Ch’ien¹'),
            ]),
        ({'sourceOptions': {'zeroFinal': 'ǔ'}, 'targetOptions': {}}, [
            ("K’ung³-tzǔ³", 'K’ung³-tzŭ³'),
            ]),
        ({'sourceOptions': {'zeroFinal': 'u'}, 'targetOptions': {}}, [
            ("K’ung³-tzu³", 'K’ung³-tzŭ³'),
            ]),
        ({'sourceOptions': {'diacriticE': 'e'}, 'targetOptions': {}}, [
            ('he¹', 'hê¹'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {'case': 'lower'}}, [
            ('Kuo³-Yü²', 'kuo³-yü²'),
            ]),
        ({'sourceOptions': {'umlautU': 'u'}, 'targetOptions': {}}, [
            ('hsu¹', 'hsü¹'),
            ('yu²', exception.AmbiguousConversionError),
            ('hsü¹', 'hsü¹'), # invalid entity
            ('hsü⁴-ch’u', exception.ConversionError),
            ]),
        ({'sourceOptions': {'neutralToneMark': 'five'},
            'targetOptions': {}}, [
            ('chih¹-tao⁵', 'chih¹-tao'),
            ('chih¹-tao', exception.ConversionError),
            ]),
        ({'sourceOptions': {'neutralToneMark': 'zero',
            'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ('chih1-tao0', 'chih¹-tao'),
            ]),
        ]


class WadeGilesPinyinConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'Pinyin')


# TODO
class WadeGilesPinyinReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'Pinyin')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'toneMarkType': 'numbers'},
            'targetOptions': {}}, [
            ('kuo', 'guo'),
            ('kuo³-yü²', 'kuo³-yü²'),
            ('kuo3-yü2', 'guǒyú'),
            ("ssŭ1ma3 ch’ien1", 'sīmǎ qiān'),
            ("Ssŭ1ma3 Ch’ien1", 'Sīmǎ Qiān'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('kuo³-yü²', 'guǒyú'),
            ('KUO³-YÜ²', 'GUǑYÚ'),
            ('ho', 'he'),
            ('hê', 'he'),
            ]),
        ]

    LOC_CONVERSION_TABLE = """
   a    a
   ai    ai
   an    an
   ang    ang
   ao    ao
   cha    zha
   ch`a    cha
   chai    zhai
   ch`ai    chai
   chan    zhan
   ch`an    chan
   chang    zhang
   ch`ang    chang
   chao    zhao
   ch`ao    chao
   che    zhe
   ch`e    che
   chen    zhen
   ch`en    chen
   cheng    zheng
   ch`eng    cheng
   chi    ji
   ch`i    qi
   chia    jia
   ch`ia    qia
   chiang    jiang
   ch`iang    qiang
   chiao    jiao
   ch`iao    qiao
   chieh    jie
   ch`ieh    qie
   chien    jian
   ch`ien    qian
   chih    zhi
   ch`ih    chi
   chin    jin
   ch`in    qin
   ching    jing
   ch`ing    qing
   chiu    jiu
   ch`iu    qiu
   chiung    jiong
   ch`iung    qiong
   cho    zhuo
   ch`o    chuo
   chou    zhou
   ch`ou    chou
   chu    zhu
   ch`u    chu
   chü    ju
   ch`ü    qu
   chua    zhua
   chuai    zhuai
   ch`uai    chuai
   chuan    zhuan
   ch`uan    chuan
   chüan    juan
   ch`üan    quan
   chuang    zhuang
   ch`uang    chuang
   chüeh    jue
   ch`üeh    que
   chui    zhui
   ch`ui    chui
   chun    zhun
   ch`un    chun
   chün    jun
   ch`ün    qun
   chung    zhong
   ch`ung    chong
   en    en
   erh    er
   fa    fa
   fan    fan
   fang    fang
   fei    fei
   fen    fen
   feng    feng
   fo    fo
   fou    fou
   fu    fu
   ha    ha
   hai    hai
   han    han
   hang    hang
   hao    hao
   hei    hei
   hen    hen
   heng    heng
   ho    he
   hou    hou
   hsi    xi
   hsia    xia
   hsiang    xiang
   hsiao    xiao
   hsieh    xie
   hsien    xian
   hsin    xin
   hsing    xing
   hsiu    xiu
   hsiung    xiong
   hsü    xu
   hsüan    xuan
   hsüeh    xue
   hsün    xun
   hu    hu
   hua    hua
   huai    huai
   huan    huan
   huang    huang
   hui    hui
   hun    hun
   hung    hong
   huo    huo
   i    yi
   jan    ran
   jang    rang
   jao    rao
   je    re
   jen    ren
   jeng    reng
   jih    ri
   jo    ruo
   jou    rou
   ju    ru
   juan    ruan
   jui    rui
   jun    run
   jung    rong
   ka    ga
   k`a    ka
   kai    gai
   k`ai    kai
   kan    gan
   k`an    kan
   kang    gang
   k`ang    kang
   kao    gao
   k`ao    kao
   ken    gen
   k`en    ken
   keng    geng
   k`eng    keng
   ko    ge
   k`o    ke
   kou    gou
   k`ou    kou
   ku    gu
   k`u    ku
   kua    gua
   k`ua    kua
   kuai    guai
   k`uai    kuai
   kuan    guan
   k`uan    kuan
   kuang    guang
   k`uang    kuang
   kuei    gui
   k`uei    kui
   kun    gun
   k`un    kun
   kung    gong
   k`ung    kong
   kuo    guo
   k`uo    kuo
   la    la
   lai    lai
   lan    lan
   lang    lang
   lao    lao
   le    le
   lei    lei
   leng    leng
   li    li
   liang    liang
   liao    liao
   lieh    lie
   lien    lian
   lin    lin
   ling    ling
   liu    liu
   lo    luo
   lou    lou
   lu    lu
   lü    lü
   luan    luan
   lüeh    lüe
   lun    lun
   lung    long
   ma    ma
   mai    mai
   man    man
   mang    mang
   mao    mao
   mei    mei
   men    men
   meng    meng
   mi    mi
   miao    miao
   mieh    mie
   mien    mian
   min    min
   ming    ming
   miu    miu
   mo    mo
   mou    mou
   mu    mu
   na    na
   nai    nai
   nan    nan
   nang    nang
   nao    nao
   nei    nei
   nen    nen
   neng    neng
   ni    ni
   niang    niang
   niao    niao
   nieh    nie
   nien    nian
   nin    nin
   ning    ning
   niu    niu
   no    nuo
   nou    nou
   nu    nu
   nü    nü
   nuan    nuan
   nüeh    nüe
   nung    nong
   o    ê
   ou    ou
   pa    ba
   p`a    pa
   pai    bai
   p`ai    pai
   pan    ban
   p`an    pan
   pang    bang
   p`ang    pang
   pao    bao
   p`ao    pao
   pei    bei
   p`ei    pei
   pen    ben
   p`en    pen
   peng    beng
   p`eng    peng
   pi    bi
   p`i    pi
   piao    biao
   p`iao    piao
   pieh    bie
   p`ieh    pie
   pien    bian
   p`ien    pian
   pin    bin
   p`in    pin
   ping    bing
   p`ing    ping
   po    bo
   p`o    po
   p`ou    pou
   pu    bu
   p`u    pu
   sa    sa
   sai    sai
   san    san
   sang    sang
   sao    sao
   se    se
   sen    sen
   seng    seng
   sha    sha
   shai    shai
   shan    shan
   shang    shang
   shao    shao
   she    she
   shen    shen
   sheng    sheng
   shih    shi
   shou    shou
   shu    shu
   shua    shua
   shuai    shuai
   shuan    shuan
   shuang    shuang
   shui    shui
   shun    shun
   shuo    shuo
   so    suo
   sou    sou
   ssu    si
   su    su
   suan    suan
   sui    sui
   sun    sun
   sung    song
   ta    da
   t`a    ta
   tai    dai
   t`ai    tai
   tan    dan
   t`an    tan
   tang    dang
   t`ang    tang
   tao    dao
   t`ao    tao
   te    de
   t`e    te
   teng    deng
   t`eng    teng
   ti    di
   t`i    ti
   tiao    diao
   t`iao    tiao
   tieh    die
   t`ieh    tie
   tien    dian
   t`ien    tian
   ting    ding
   t`ing    ting
   tiu    diu
   to    duo
   t`o    tuo
   tou    dou
   t`ou    tou
   tu    du
   t`u    tu
   tuan    duan
   t`uan    tuan
   tui    dui
   t`ui    tui
   tun    dun
   t`un    tun
   tung    dong
   t`ung    tong
   tsa    za
   ts`a    ca
   tsai    zai
   ts`ai    cai
   tsan    zan
   ts`an    can
   tsang    zang
   ts`ang    cang
   tsao    zao
   ts`ao    cao
   tse    ze
   ts`e    ce
   tsei    zei
   tsen    zen
   ts`en    cen
   tseng    zeng
   ts`eng    ceng
   tso    zuo
   ts`o    cuo
   tsou    zou
   ts`ou    cou
   tsu    zu
   ts`u    cu
   tsuan    zuan
   ts`uan    cuan
   tsui    zui
   ts`ui    cui
   tsun    zun
   ts`un    cun
   tsung    zong
   ts`ung    cong
   tzu    zi
   tz`u    ci
   wa    wa
   wai    wai
   wan    wan
   wang    wang
   wei    wei
   wen    wen
   weng    weng
   wo    wo
   wu    wu
   ya    ya
   yai    yai
   yang    yang
   yao    yao
   yeh    ye
   yen    yan
   yin    yin
   ying    ying
   yo    yo
   yu    you
   yü    yu
   yüan    yuan
   yüeh    yue
   yün    yun
   yung    yong
"""
    """
    Conversion table from the  Library of Congress Pinyin Conversion Project -
    New Chinese Romanization Guidelines:
    http://www.loc.gov/catdir/pinyin/romcover.html, 28.05.1999
    This list contains syllables taken from Dìmíng Hànzì Yìyīnbiǎo (名漢字譯音表,
    1971) and ALA-LC romanization tables (1997) for the Wade-Giles parts and
    furthermore Xiàndài Hànyǔ Cídiǎn (现代汉语词典, 1983) for the Pinyin parts.

    Corrected entry: lüeh -> lue to lüe, nüeh -> nue to nüe, o -> e to ê,
    Removed entry: lüan -> luan (missing source)
    """

    def setUp(self):
        super(WadeGilesPinyinReferenceTest, self).setUp()

        # set up LOC table
        wgOptions = {'wadeGilesApostrophe': '`', 'toneMarkType': 'none',
            'diacriticE': 'e', 'zeroFinal': 'u'}
        pinyinOptions = {'erhua': 'ignore', 'toneMarkType': 'none'}
        self.converter = self.f.createReadingConverter('WadeGiles',
            'Pinyin', sourceOptions=wgOptions, targetOptions=pinyinOptions)
        self.wgOperator = self.f.createReadingOperator('WadeGiles', **wgOptions)

        # read in plain text mappings
        self.syllableMapping = {}
        for line in self.LOC_CONVERSION_TABLE.split("\n"):
            if line.strip() == "":
                continue
            matchObj = re.match(r"(?u)\s*((?:\w|`)+)\s+((?:\w)+)", line)
            wgSyllable, pinyinSyllable = matchObj.groups()
            self.syllableMapping[wgSyllable] = pinyinSyllable

    def testLOCTableReferences(self):
        """Test if all LoC references are reached."""
        for wgSyllable, target in list(self.syllableMapping.items()):
            try:
                syllable = self.converter.convert(wgSyllable)
                self.assertEqual(syllable, target,
                    "Wrong conversion to Pinyin %s for Wade-Giles %s: %s" \
                        % (repr(target), repr(wgSyllable), repr(syllable)))
            except exception.ConversionError:
                pass


class PinyinWadeGilesConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'WadeGiles')


# TODO
class PinyinWadeGilesReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'WadeGiles')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {}, 'targetOptions': {'toneMarkType': 'numbers'}}, [
            ("tiān'ānmén", 't’ien1-an1-mên2'),
            ('he', exception.AmbiguousConversionError),
            ]),
        ]


class GRDialectConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'GR')

    OPTIONS_LIST = [{'keepGRApostrophes': True}, {'breakUpAbbreviated': 'on'},
        {'breakUpAbbreviated': 'off'}]

    def testAbbreviationConsistency(self):
        """
        Check that no abbreviation overlaps with another one.
        """
        # this actually tests the operator, but as the implementation of the
        #   converter (convertAbbreviatedEntities()) depends on this fact, we'll
        #   test it here
        gr = self.f.createReadingOperator('GR')
        abbreviatedForms = gr.getAbbreviatedForms()
        for form in abbreviatedForms:
            if not len(form) > 1:
                # allow being fully contained in, just no overlaps
                continue
            for otherform in abbreviatedForms:
                if len(otherform) > 1 and otherform != form:
                    for left in range(1, len(form)):
                        self.assertTrue(form[:left] != otherform[-left:])
                    for right in range(1, len(form)):
                        self.assertTrue(form[right:] != otherform[:right])


# TODO
class GRDialectReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'GR')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'grSyllableSeparatorApostrophe': "'"},
            'targetOptions': {'grRhotacisedFinalApostrophe': "'"}}, [
            ("tian'anmen", 'tian’anmen'),
            ('jie’l', "jie'l"),
            ('x', 'x'),
            ]),
        ({'breakUpAbbreviated': 'on'}, [
            ("g", '˳geh'),
            ("j", '.je'),
            ("hairtz", 'hair.tzy'),
            ("tz", '.tzy'),
            ("sherm.me", 'shern.me'),
            ("bu", 'bu'),
            ('buh jy.daw', "buh jy.daw"),
            ('x', exception.ConversionError),
            ]),
        ({'sourceOptions': {'optionalNeutralToneMarker': 'ₒ'}}, [
            ("ₒgeh", '˳geh'),
            ]),
        ]


class GRPinyinConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'Pinyin')

    OPTIONS_LIST = [{'grOptionalNeutralToneMapping': 'neutral'}]

    def cleanDecomposition(self, decomposition, reading, **options):
        cls = self.f.getReadingOperatorClass(reading)
        if not hasattr(cls, 'removeApostrophes'):
            return decomposition

        if not hasattr(self, '_operators'):
            self._operators = []
        for operatorReading, operatorOptions, op in self._operators:
            if reading == operatorReading and options == operatorOptions:
                break
        else:
            op = self.f.createReadingOperator(reading, **options)
            self._operators.append((reading, options, op))

        return op.removeApostrophes(decomposition)


# TODO
class GRPinyinReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'Pinyin')

    CONVERSION_REFERENCES = [
        ({'grOptionalNeutralToneMapping': 'neutral'}, [
            # Extract from Y.R. Chao's Sayable Chinese quoted from English
            #   Wikipedia (http://en.wikipedia.org/w/index.php?\
            #title=Gwoyeu_Romatzyh&oldid=301522286
            #   added concrete tone specifiers to "de", "men", "jing", "bu",
            #   removed hyphen in i-goong, changed the Pinyin transcript to not
            #   show tone sandhis for 一, fixed punctuation errors in Pinyin
            ('"Hannshyue" .de mingcheng duey Jonggwo yeou idean buhtzuenjinq .de yihwey. Woo.men tingshuo yeou "Yinnduhshyue", "Aijyishyue", "Hannshyue", erl meiyeou tingshuo yeou "Shilahshyue", "Luomaashyue", genq meiyeou tingshuo yeou "Inggwoshyue", "Meeigwoshyue". "Hannshyue" jeyg mingcheng wanchyuan beaushyh Ou-Meei shyuejee duey nahshie yii.jing chernluen .de guulao-gwojia .de wenhuah .de ijoong chingkann .de tayduh.', '"Hànxué" de míngchēng duì Zhōngguó yǒu yīdiǎn bùzūnjìng de yìwèi. Wǒmen tīngshuō yǒu "Yìndùxué", "Āijíxué", "Hànxué", ér méiyǒu tīngshuō yǒu "Xīlàxué", "Luómǎxué", gèng méiyǒu tīngshuō yǒu "Yīngguóxué", "Měiguóxué". "Hànxué" zhèige míngchēng wánquán biǎoshì Ōu-Měi xuézhě duì nàxiē yǐjing chénlún de gǔlǎo-guójiā de wénhuà de yīzhǒng qīngkàn de tàidù.'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('sheau jie’l', 'xiǎo jiēr'),
            ('jieel', exception.AmbiguousConversionError),
            ('buh jy.daw', 'bù zhīdao'), ('buh jy˳daw', 'bù zhīdào'),
            ('woo de', 'wǒ dē'),
            ('hairtz', 'háizi'), ('ig', 'yīgè'), ('sherm', 'shénme'),
            ('sherm.me', 'shénme'), ('tzeem.me', 'zěnme'),
            ('tzeem.me', 'zěnme'), ('tzemm', 'zènme'),
            ('tzemm.me', 'zènme'), ('jemm', 'zhènme'),
            ('jemm.me', 'zhènme'), ('nemm', 'néme'), ('nemm.me', 'néme'),
            ('.ne.me', 'neme'), ('woom', 'wǒmen'),
            ("liibay’i", 'lǐbàiyī'), ("san’g ren", 'sāngè rén'),
            ("shyr’ell", "shí'èr"),
            ('shie.x', 'xiēxie'), ('duey .le vx', 'duì le duì le'),
            ('duey  .le vx', 'duì  le duì  le'), ('deengiv', 'děngyīděng'),
            ('feyshinvx', 'fèixīnfèixīn'),
            # TODO implement?
            #(u'j-h-eh', u'zhè'),
            ]),
        ]


class PinyinGRConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'GR')


## TODO
#class PinyinGRReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('Pinyin', 'GR')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class BraillePinyinConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('MandarinBraille', 'Pinyin')


# TODO
class BraillePinyinReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('MandarinBraille', 'Pinyin')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {}, 'targetOptions': {'toneMarkType': 'numbers'}}, [
            ('⠍⠢⠆', exception.AmbiguousConversionError), # mo/me
            ('⠇⠢⠆', exception.AmbiguousConversionError), # lo/le
            ('⠢⠆', exception.AmbiguousConversionError),  # o/e
            ('⠛⠥', 'gu5'),
            ('⠛⠥⠁', 'gu1'),
            ('⠛⠬', 'ju5'),
            ]),
        ]


class PinyinBrailleConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'MandarinBraille')


# TODO
class PinyinBrailleReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'MandarinBraille')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ('lao3shi1', '⠇⠖⠄⠱⠁'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('lǎoshī', '⠇⠖⠄⠱⠁'),
            ('lao3shi1', 'lao3shi1'),
            ('mò', '⠍⠢⠆'),
            ('mè', '⠍⠢⠆'),
            ('gu', '⠛⠥'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ('Qing ni deng yi1xia!', '⠅⠡ ⠝⠊ ⠙⠼ ⠊⠁⠓⠫⠰⠂'),
            ('mangwen shushe', '⠍⠦⠒ ⠱⠥⠱⠢'),
            ('shi4yong', '⠱⠆⠹'),
            ('yi1xia', '⠊⠁⠓⠫'),
            ('yi3xia', '⠊⠄⠓⠫'),
            ('gu', '⠛⠥'),
            ]),
        ({'sourceOptions': {'toneMarkType': 'numbers'},
            'targetOptions': {'missingToneMark': 'fifth'}}, [
            ('gu', exception.ConversionError),
            ('gu5', '⠛⠥'),
            ]),
        ]


class PinyinIPAConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'MandarinIPA')

    # TODO add another sandhi function reference
    OPTIONS_LIST = [{'sandhiFunction': None},
        {'coarticulationFunction': \
            converter.PinyinIPAConverter.finalECoarticulation}]


# TODO
class PinyinIPAReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('Pinyin', 'MandarinIPA')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'toneMarkType': 'numbers'}, 'targetOptions': {}}, [
            ('lao3shi1', 'lau˨˩.ʂʅ˥˥'),
            ('LAO3SHI1', 'lau˨˩.ʂʅ˥˥'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('lao3shi1', 'lao3shi1'),
            ]),
        ]


class WadeGilesIPAConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'MandarinIPA')

    # TODO add another sandhi function reference
    OPTIONS_LIST = [{'sandhiFunction': None},
        {'coarticulationFunction': \
            converter.PinyinIPAConverter.finalECoarticulation}]


# TODO
class WadeGilesIPAReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'MandarinIPA')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'toneMarkType': 'numbers'},
            'targetOptions': {}}, [
            ('kuo3-yü2', 'kuo˨˩.y˧˥'),
            ('LAO3-SHIH1', 'lau˨˩.ʂʅ˥˥'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {}}, [
            ('LAO3-SHIH1', 'LAO3-SHIH1'),
            ('LAO³-SHIH¹', 'lau˨˩.ʂʅ˥˥'),
            ]),
        ]


class MandarinBrailleIPAConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('MandarinBraille', 'MandarinIPA')

    # TODO add another sandhi function reference
    OPTIONS_LIST = [{'sandhiFunction': None},
        {'coarticulationFunction': \
            converter.PinyinIPAConverter.finalECoarticulation}]


## TODO
#class MandarinBrailleIPAReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('MandarinBraille', 'MandarinIPA')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class BrailleGRConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('MandarinBraille', 'GR')


## TODO
#class BrailleGRReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('MandarinBraille', 'GR')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class GRBrailleConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'MandarinBraille')


## TODO
#class GRBrailleReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('GR', 'MandarinBraille')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class GRIPAConsistencyTest(ReadingConverterConsistencyTest, unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'MandarinIPA')

    # TODO add another sandhi function reference
    OPTIONS_LIST = [{'sandhiFunction': None},
        {'coarticulationFunction': \
            converter.PinyinIPAConverter.finalECoarticulation}]

    def cleanDecomposition(self, decomposition, reading, **options):
        return [entity for entity in decomposition if entity != '.']


## TODO
#class GRIPAGilesReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('GR', 'MandarinIPA')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class GRWadeGilesConsistencyTest(ReadingConverterConsistencyTest, unittest.TestCase):
    CONVERSION_DIRECTION = ('GR', 'WadeGiles')

    def cleanDecomposition(self, decomposition, reading, **options):
        cls = self.f.getReadingOperatorClass(reading)
        if not hasattr(cls, 'removeHyphens'):
            return decomposition

        if not hasattr(self, '_operators'):
            self._operators = []
        for operatorReading, operatorOptions, op in self._operators:
            if reading == operatorReading and options == operatorOptions:
                break
        else:
            op = self.f.createReadingOperator(reading, **options)
            self._operators.append((reading, options, op))

        return op.removeHyphens(decomposition)


## TODO
#class GRWadeGilesReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('GR', 'WadeGiles')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class WadeGilesGRConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'GR')


## TODO
#class WadeGilesGRReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('WadeGiles', 'GR')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class WadeGilesBrailleConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('WadeGiles', 'MandarinBraille')


## TODO
#class WadeGilesBrailleReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('WadeGiles', 'MandarinBraille')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class BrailleWadeGilesConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('MandarinBraille', 'WadeGiles')


## TODO
#class BrailleWadeGilesReferenceTest(ReadingConverterReferenceTest,
    #unittest.TestCase):
    #CONVERSION_DIRECTION = ('MandarinBraille', 'WadeGiles')

    #CONVERSION_REFERENCES = [
        #({'sourceOptions': {}, 'targetOptions': {}}, [
            #]),
        #]


class ShanghaineseIPADialectConsistencyTest(ReadingConverterConsistencyTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('ShanghaineseIPA', 'ShanghaineseIPA')


class ShanghaineseIPADialectReferenceTest(ReadingConverterReferenceTest,
    unittest.TestCase):
    CONVERSION_DIRECTION = ('ShanghaineseIPA', 'ShanghaineseIPA')

    CONVERSION_REFERENCES = [
        ({'sourceOptions': {'toneMarkType': 'superscriptChaoDigits'},
            'targetOptions': {'toneMarkType': 'chaoDigits'}}, [
            ('ɦi⁵³ ɦɑ̃⁵³.ʦɤ lɛ⁵³ gəˀ¹²', 'ɦi53 ɦɑ̃53.ʦɤ lɛ53 gəˀ12'),
            ]),
        ({'sourceOptions': {}, 'targetOptions': {'toneMarkType': 'chaoDigits'}},
            [
            ('ɦi˥˧ ɦɑ̃˥˧.ʦɤ lɛ˥˧ gəˀ˩˨', 'ɦi53 ɦɑ̃53.ʦɤ lɛ53 gəˀ12'),
            ]),
        ]
