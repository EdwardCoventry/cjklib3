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
Unit tests for :mod:`cjklib.reading.operator`.
"""

# pylint: disable-msg=E1101
#  testcase attributes and methods are only available in concrete classes

import re
import types
import unittest
import unicodedata

from cjklib.reading import ReadingFactory
from cjklib import exception
from cjklib.test import NeedsDatabaseTest, attr
from cjklib.util import crossDict

class ReadingOperatorTest(NeedsDatabaseTest):
    """
    Base class for testing of
    :class:`~cjklib.reading.operator.ReadingOperator` classes.
    """
    READING_NAME = None
    """Name of reading to test"""

    def setUp(self):
        NeedsDatabaseTest.setUp(self)
        self.f = ReadingFactory(dbConnectInst=self.db)

        for clss in self.f.getReadingOperatorClasses():
            if clss.READING_NAME == self.READING_NAME:
                self.readingOperatorClass = clss
                break
        else:
            self.readingOperatorClass = None

    def shortDescription(self):
        methodName = getattr(self, self.id().split('.')[-1])
        # get whole doc string and remove superfluous white spaces
        noWhitespaceDoc = re.sub(r'\s+', ' ', methodName.__doc__.strip())
        # remove markup for epytext format
        clearName = re.sub(r'[CLI]\{([^\}]*)}', r'\1', noWhitespaceDoc)
        # add name of reading
        return clearName + ' (for %s)' % self.READING_NAME

    def tearDown(self):
        # get rid of the possibly > 1000 instances
        self.f.clearCache()


class ReadingOperatorConsistencyTest(ReadingOperatorTest):
    """
    Base class for consistency testing of
    :class:`~cjklib.reading.operator.ReadingOperator` classes.
    """
    DIALECTS = []
    """
    Dialects tested additionally to the standard one.
    Given as list of dictionaries holding the dialect's options.
    """

    def testReadingNameUnique(self):
        """Test if only one ReadingOperator exists for each reading."""
        seen = False

        for clss in self.f.getReadingOperatorClasses():
            if clss.READING_NAME == self.READING_NAME:
                self.assertTrue(not seen,
                    "Reading %s has more than one operator" \
                    % clss.READING_NAME)
                seen = True

    def testInstantiation(self):
        """Test if given dialects can be instantiated."""
        self.assertTrue(self.readingOperatorClass != None,
            "No reading operator class found" \
                + ' (reading %s)' % self.READING_NAME)

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            # instantiate
            self.readingOperatorClass(**dialect)

    def testDefaultOptions(self):
        """
        Test if option dict returned by ``getDefaultOptions()`` is well-formed
        and includes all options found in the test case's options.
        """
        defaultOptions = self.readingOperatorClass.getDefaultOptions()

        self.assertEqual(type(defaultOptions), type({}),
            "Default options %s is not of type dict" % repr(defaultOptions) \
            + ' (reading %s)' % self.READING_NAME)
        # test if option names are well-formed
        for option in defaultOptions:
            self.assertEqual(type(option), type(''),
                "Option %s is not of type str" % repr(option) \
                + ' (reading %s)' % self.READING_NAME)

        # test all given dialects
        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            for option in dialect:
                self.assertTrue(option in defaultOptions,
                    "Test case option %s not found in default options" \
                        % repr(option) \
                    + ' (reading %s, dialect %s)' \
                        % (self.READING_NAME, dialect))

        # test instantiation of default options
        defaultInstance = self.readingOperatorClass(**defaultOptions)

        # check if option value changes after instantiation
        for option in defaultOptions:
            self.assertEqual(getattr(defaultInstance, option),
                defaultOptions[option],
                "Default option value %s for %s changed on instantiation: %s" \
                    % (repr(defaultOptions[option]), repr(option),
                        repr(getattr(defaultInstance, option))) \
                + ' (reading %s)' % self.READING_NAME)

        # check options against instance without explicit option dict
        instance = self.readingOperatorClass()
        for option in defaultOptions:
            self.assertEqual(getattr(instance, option),
                getattr(defaultInstance, option),
                "Option value for %s unequal for default instances: %s and %s" \
                    % (repr(option), repr(getattr(instance, option)),
                        repr(getattr(defaultInstance, option))) \
                + ' (reading %s)' % self.READING_NAME)

    def testGuessReadingDialect(self):
        """
        Test if option dict returned by ``guessReadingDialect()`` is well-formed
        and options are included in dict from ``getDefaultOptions()``.
        """
        if not hasattr(self.readingOperatorClass, 'guessReadingDialect'):
            return

        defaultOptions = self.readingOperatorClass.getDefaultOptions()

        readingDialect = self.readingOperatorClass.guessReadingDialect('')

        self.assertEqual(type(defaultOptions), type({}),
            "Guessed options %s is not of type dict" % repr(readingDialect) \
            + ' (reading %s)' % self.READING_NAME)
        # test if option names are well-formed
        for option in readingDialect:
            self.assertEqual(type(option), type(''),
                "Option %s is not of type str" % repr(option) \
                + ' (reading %s)' % self.READING_NAME)

        # test inclusion in default set
        for option in readingDialect:
            self.assertTrue(option in defaultOptions,
                "Option %s not found in default options" % repr(option) \
                + ' (reading %s)' % self.READING_NAME)

        # test instantiation of default options
        self.readingOperatorClass(**readingDialect)

    @attr('quiteslow')
    def testReadingCharacters(self):
        """
        Test if set returned by ``getReadingCharacters()`` is well-formed and
        includes all characters found in reading entities.
        """
        if not hasattr(self.readingOperatorClass, "getReadingCharacters"):
            return

        # test all given dialects
        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            readingOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            readingCharacters = readingOperator.getReadingCharacters()

            # make sure all are characters
            for char in readingCharacters:
                self.assertTrue(len(char) == 1,
                    "Not len()==1: %s" % repr(char) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

            entities = readingOperator.getReadingEntities()
            for entity in entities:
                charList = set(entity)
                # include NFD form
                charList.update(unicodedata.normalize('NFD', str(entity)))
                for char in charList:
                    self.assertTrue(char in readingCharacters,
                        "Char %s not included" % repr(char) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))

    def testValidReadingEntitiesAccepted(self):
        """
        Test if all *reading entities* returned by ``getReadingEntities()`` are
        accepted by ``isReadingEntity()``.
        """
        if not hasattr(self.readingOperatorClass, "getReadingEntities"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            entities = self.f.getReadingEntities(self.READING_NAME,
                **dialect)
            for entity in entities:
                self.assertTrue(
                    self.f.isReadingEntity(entity, self.READING_NAME,
                        **dialect),
                    "Entity %s not accepted" % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

    def testValidFormattingEntitiesAccepted(self):
        """
        Test if all *formatting entities* returned by
        ``getFormattingEntities()`` are accepted by ``isFormattingEntity()``.
        """
        if not hasattr(self.readingOperatorClass, "getFormattingEntities"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            entities = self.f.getFormattingEntities(self.READING_NAME,
                **dialect)
            for entity in entities:
                self.assertTrue(
                    self.f.isFormattingEntity(entity, self.READING_NAME,
                        **dialect),
                    "Entity %s not accepted" % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

    def testValidPlainReadingEntitiesAccepted(self):
        """
        Test if all plain reading entities returned by
        ``getPlainReadingEntities()`` are accepted by ``isPlainReadingEntity()``.
        """
        if not hasattr(self.readingOperatorClass, "getPlainReadingEntities"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            plainEntities = self.f.getPlainReadingEntities(self.READING_NAME,
                **dialect)
            for plainEntity in plainEntities:
                self.assertTrue(
                    self.f.isPlainReadingEntity(plainEntity, self.READING_NAME,
                        **dialect),
                    "Plain entity %s not accepted" % repr(plainEntity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

    @attr('quiteslow')
    def testOnsetRhyme(self):
        """Test if all plain entities are accepted by ``getOnsetRhyme()``."""
        if not hasattr(self.readingOperatorClass, "getPlainReadingEntities") \
            or not hasattr(self.readingOperatorClass, "getOnsetRhyme"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            readingOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            plainEntities = readingOperator.getPlainReadingEntities()
            for plainEntity in plainEntities:
                try:
                    readingOperator.getOnsetRhyme(plainEntity)
                except exception.InvalidEntityError:
                    self.fail("Plain entity %s not accepted" \
                        % repr(plainEntity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))
                except exception.UnsupportedError:
                    pass

    @attr('quiteslow')
    def testDecomposeIsIdentityForSingleEntity(self):
        """
        Test if all reading entities returned by ``getReadingEntities()`` are
        decomposed into the single entity again.
        """
        if not hasattr(self.readingOperatorClass, "getReadingEntities"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            entities = self.f.getReadingEntities(self.READING_NAME, **dialect)
            for entity in entities:
                try:
                    entities = self.f.decompose(entity, self.READING_NAME,
                        **dialect)
                    self.assertEqual(entities, [entity],
                        "decomposition on single entity %s" % repr(entity) \
                        + " is not identical: %s" % repr(entities) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))
                except exception.AmbiguousDecompositionError:
                    self.fail("ambiguous decomposition for %s" % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))
                except exception.DecompositionError:
                    self.fail("decomposition error for %s" % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))


    @attr('quiteslow')
    def testGetTonalEntityOfSplitEntityToneIsIdentity(self):
        """
        Test if the composition of ``getTonalEntity()`` and ``splitEntityTone()``
        returns the original value for all entities returned by
        ``getReadingEntities()``.
        """
        if not (hasattr(self.readingOperatorClass, "getTonalEntity")
            and hasattr(self.readingOperatorClass, "splitEntityTone")
            and hasattr(self.readingOperatorClass, "getReadingEntities")):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            entities = self.f.getReadingEntities(self.READING_NAME, **dialect)
            for entity in entities:
                try:
                    plainEntity, tone = self.f.splitEntityTone(entity,
                        self.READING_NAME, **dialect)

                    self.assertEqual(
                        self.f.getTonalEntity(plainEntity, tone,
                            self.READING_NAME, **dialect),
                        entity,
                        "Entity %s not preserved in composition" % repr(entity)\
                            + " of getTonalEntity() and splitEntityTone()" \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))
                except exception.UnsupportedError:
                    pass
                except exception.InvalidEntityError:
                    self.fail("Entity %s raised InvalidEntityError" \
                        % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))


            if (not hasattr(self, 'testUpperCase')
                or self.testUpperCase(dialect)):
                for entity in entities:
                    entityUpper = entity.upper()
                    if entity == entityUpper:
                        continue
                    try:
                        plainEntity, tone = self.f.splitEntityTone(
                            entityUpper, self.READING_NAME, **dialect)

                        self.assertEqual(
                            self.f.getTonalEntity(plainEntity, tone,
                                self.READING_NAME, **dialect),
                            entity.upper(),
                            ("Entity %s not preserved in composition"
                                % repr(entityUpper)) \
                                + " of getTonalEntity() and splitEntityTone()" \
                                + ' (reading %s, dialect %s)' \
                                    % (self.READING_NAME, dialect))
                    except exception.UnsupportedError:
                        pass
                    except exception.InvalidEntityError:
                        self.fail("Entity %s raised InvalidEntityError" \
                            % repr(entityUpper) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))

    @attr('quiteslow')
    def testSplitEntityToneReturnsValidInformation(self):
        """
        Test if ``splitEntityTone()`` returns a valid plain entity and a valid
        tone for all entities returned by ``getReadingEntities()``.
        """
        if not hasattr(self.readingOperatorClass, "getPlainReadingEntities"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            entities = self.f.getReadingEntities(self.READING_NAME, **dialect)
            for entity in entities:
                try:
                    plainEntity, tone = self.f.splitEntityTone(entity,
                        self.READING_NAME, **dialect)

                    self.assertTrue(self.f.isPlainReadingEntity(plainEntity,
                        self.READING_NAME, **dialect),
                        "Plain entity of %s not accepted: %s" \
                            % (repr(entity), repr(plainEntity)) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

                    self.assertTrue(
                        tone in self.f.getTones(self.READING_NAME, **dialect),
                        "Tone of entity %s not valid: %s " \
                            % (repr(entity), repr(tone)) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))
                except exception.UnsupportedError:
                    pass
                except exception.InvalidEntityError:
                    self.fail("Entity %s raised InvalidEntityError" \
                        % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

    #TODO Jyutping (missing tone marks) and CantoneseYale don't create strict
      #compositions
    @attr('slow')
    def testDecomposeKeepsSyllablePairs(self):
        """
        Test if all pairs of reading entities returned by
        ``getReadingEntities()`` are decomposed into the same pairs again and
        possibly are strict.
        """
        if not hasattr(self.readingOperatorClass, "getReadingEntities"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            entities = self.f.getReadingEntities(self.READING_NAME, **dialect)
            for entityA in entities:
                for entityB in entities:
                    pair = [entityA, entityB]
                    string = self.f.compose(pair, self.READING_NAME, **dialect)
                    try:
                        decomposition = self.f.decompose(string,
                            self.READING_NAME, **dialect)

                        if hasattr(self, 'cleanDecomposition'):
                            cleanDecomposition = self.cleanDecomposition(
                                decomposition, self.READING_NAME, **dialect)
                        else:
                            cleanDecomposition = decomposition

                        self.assertEqual(cleanDecomposition, pair,
                            "decompose doesn't keep entity pair %s: %s" \
                                % (repr(pair), repr(cleanDecomposition)) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

                        # test if method exists and by default is not False
                        if hasattr(self.readingOperatorClass,
                            "isStrictDecomposition") \
                            and self.f.isStrictDecomposition([],
                                self.READING_NAME, **dialect) != False: # TODO this doesn't capture bugs in isStrictDecomposition that return False for an empty array

                            strict = self.f.isStrictDecomposition(decomposition,
                                self.READING_NAME, **dialect)

                            self.assertTrue(strict,
                                "Decomposition for pair %s is not strict" \
                                    % repr(string) \
                                + ' (reading %s, dialect %s)' \
                                    % (self.READING_NAME, dialect))

                    except exception.AmbiguousDecompositionError:
                        self.fail('Decomposition ambiguous for pair %s' \
                            % repr(pair) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))
                    except exception.DecompositionError:
                        self.fail('Decomposition fails for pair %s' \
                            % repr(pair) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))


class ReadingOperatorTestCaseCheck(NeedsDatabaseTest, unittest.TestCase):
    """
    Checks if every
    :class:`~cjklib.reading.operator.ReadingOperator` has its own
    :class:`~cjklib.test.readingoperator.ReadingOperatorConsistencyTest`.
    """
    def testEveryOperatorHasConsistencyTest(self):
        """
        Check if every reading has a test case.
        """
        testClasses = self.getReadingOperatorConsistencyTestClasses()
        testClassReadingNames = [clss.READING_NAME for clss in testClasses]
        self.f = ReadingFactory(dbConnectInst=self.db)

        for clss in self.f.getReadingOperatorClasses():
            self.assertTrue(clss.READING_NAME in testClassReadingNames,
                "Reading %s has no ReadingOperatorConsistencyTest" \
                    % clss.READING_NAME)

    @staticmethod
    def getReadingOperatorConsistencyTestClasses():
        """
        Gets all classes implementing
        :class:`cjklib.test.readingoperator.ReadingOperatorConsistencyTest`.

        :rtype: list
        :return: list of all classes inheriting form
            :class:`cjklib.test.readingoperator.ReadingOperatorConsistencyTest`
        """
        # get all non-abstract classes that inherit from
        #   ReadingOperatorConsistencyTest
        testModule = __import__("cjklib.test.readingoperator")
        testClasses = [clss for clss \
            in list(testModule.test.readingoperator.__dict__.values()) \
            if type(clss) in [type, type] \
            and issubclass(clss, ReadingOperatorConsistencyTest) \
            and clss.READING_NAME]

        return testClasses


class ReadingOperatorReferenceTest(ReadingOperatorTest):
    """
    Base class for testing of references against
    :class:`~cjklib.reading.operator.ReadingOperator` classes.
    These tests assure that the given values are returned correctly.
    """

    DECOMPOSITION_REFERENCES = []
    """
    References to test ``decompose()`` operation.
    List of dialect/reference tuples, schema: ({dialect}, [(reference, target)])
    """

    COMPOSITION_REFERENCES = []
    """
    References to test ``compose()`` operation.
    List of dialect/reference tuples, schema: ({}, [(reference, target)])
    """

    READING_ENTITY_REFERENCES = []
    """
    References to test ``isReadingEntity()`` operation.
    List of dialect/reference tuples, schema: ({}, [(reference, target)])
    """

    GUESS_DIALECT_REFERENCES = []
    """
    References to test ``guessReadingDialect()`` operation.
    List of reference/dialect tuples, schema: (reference, {})
    """

    def testDecompositionReferences(self):
        """Test if the given decomposition references are reached."""
        for dialect, references in self.DECOMPOSITION_REFERENCES:
            for reference, target in references:
                args = [reference, self.READING_NAME]
                if type(target) in [type, type] \
                    and issubclass(target, Exception):
                    self.assertRaises(target, self.f.decompose, *args,
                        **dialect)
                else:
                    try:
                        decomposition = self.f.decompose(*args, **dialect)
                        self.assertEqual(decomposition, target,
                            "Decomposition %s of %s not reached: %s" \
                                % (repr(target), repr(reference),
                                    repr(decomposition)) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))
                    except exception.DecompositionError as e:
                        self.fail(
                            'DecompositionError for %s with target %s: %s' \
                                % (repr(reference), repr(target), repr(e)) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))

    def testCompositionReferences(self):
        """Test if the given composition references are reached."""
        for dialect, references in self.COMPOSITION_REFERENCES:
            for reference, target in references:
                args = [reference, self.READING_NAME]
                if type(target) in [type, type] \
                    and issubclass(target, Exception):
                    self.assertRaises(target, self.f.compose, *args, **dialect)
                else:
                    try:
                        composition = self.f.compose(*args, **dialect)
                        self.assertEqual(composition, target,
                            "Composition %s of %s not reached: %s" \
                                % (repr(target), repr(reference),
                                    repr(composition)) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))
                    except exception.CompositionError as e:
                        self.fail('CompositionError for %s with target %s: %s' \
                            % (repr(reference), repr(target), repr(e)) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))

    def testEntityReferences(self):
        """Test if the given entity references are accepted/rejected."""
        for dialect, references in self.READING_ENTITY_REFERENCES:
            for reference, target in references:
                result = self.f.isReadingEntity(reference,
                    self.READING_NAME, **dialect)
                self.assertEqual(result, target,
                    "Target %s of %s not reached: %s" \
                        % (repr(target), repr(reference), repr(result)) \
                    + ' (reading %s, dialect %s)' \
                        % (self.READING_NAME, dialect))

    def testGuessDialectReferences(self):
        """Test if ``guessReadingDialect()`` guesses the needed options."""
        if not hasattr(self.readingOperatorClass, 'guessReadingDialect'):
            return

        for reference, dialect in self.GUESS_DIALECT_REFERENCES:
            result = self.readingOperatorClass.guessReadingDialect(reference)
            for option, value in list(dialect.items()):
                self.assertTrue(option in result,
                    "Guessed dialect doesn't include option  %s" \
                        % repr(option) \
                    + ' (reading %s, dialect %s)' \
                        % (self.READING_NAME, dialect))
                self.assertEqual(result[option], value,
                    "Target for option %s=%s not reached for %s: %s" \
                        % (repr(option), repr(value), repr(reference),
                            repr(result[option])) \
                    + ' (reading %s)' % self.READING_NAME)


class CanoneseIPAOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'CantoneseIPA'

    DIALECTS = crossDict(
        [{}, {'toneMarkType': 'numbers'}, {'toneMarkType': 'chaoDigits'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'numbers', 'firstToneName': 'HighFalling'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'ignore',
                'firstToneName': 'HighFalling'},
            {'toneMarkType': 'chaoDigits', 'missingToneMark': 'ignore'},
            #{'toneMarkType': 'diacritics'}, # TODO NotImplementedError
            #{'toneMarkType': 'diacritics', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'none'}],
        [{}, {'stopTones': 'general'}, {'stopTones': 'explicit'}],
        )

    @staticmethod
    def testUpperCase(dialect):
        return False

    def cleanDecomposition(self, decomposition, reading, **options):
        return [entity for entity in decomposition if entity != '.']

    def testEntityCountConstant(self):
        """
        Test if the number of reading entities reported by
        ``getReadingEntities()`` is constant between different stop tone
        realisations.
        """
        if not hasattr(self.readingOperatorClass, "getReadingEntities"):
            return

        entityCount = None
        for stopTones in ['none', 'general', 'explicit']:
            count = len(self.f.getReadingEntities(self.READING_NAME,
                stopTones=stopTones))
            if entityCount != None:
                self.assertEqual(entityCount, count)

    def testReportedToneValid(self):
        """
        Test if the tone reported by ``splitEntityTone()`` is valid for the given
        entity.
        """
        if not hasattr(self.readingOperatorClass, "isToneValid"):
            return

        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            ipaOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)

            entities = ipaOperator.getReadingEntities()
            for entity in entities:
                plainEntity, tone = ipaOperator.splitEntityTone(entity)

                self.assertTrue(ipaOperator.isToneValid(plainEntity, tone),
                    "Tone %s is invalid with plain entity %s" \
                        % (repr(tone), repr(plainEntity)) \
                    + ' (reading %s, dialect %s)' \
                        % (self.READING_NAME, dialect))

    def testBaseExplicitTones(self):
        """
        Test if the tones reported by ``getBaseTone()`` and ``getExplicitTone()``
        are valid.
        """
        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            ipaOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            for tone in ipaOperator.getTones():
                tone = ipaOperator.getBaseTone(tone)
                self.assertTrue(tone == None or tone in ipaOperator.TONES)

            entities = ipaOperator.getPlainReadingEntities()
            for plainEntity in entities:
                for tone in ipaOperator.getTones():
                    try:
                        explicitTone = ipaOperator.getExplicitTone(plainEntity,
                            tone)
                        self.assertTrue(explicitTone == None \
                            or explicitTone in ipaOperator.TONES \
                            or explicitTone in ipaOperator.STOP_TONES_EXPLICIT)
                    except exception.InvalidEntityError:
                        pass


# TODO
#class CantoneseIPAOperatorReferenceTest(ReadingOperatorReferenceTest,
    #unittest.TestCase):
    #READING_NAME = 'CantoneseIPA'

    #DECOMPOSITION_REFERENCES = []

    #COMPOSITION_REFERENCES = []

    #READING_ENTITY_REFERENCES = []


class CanoneseYaleOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'CantoneseYale'

    DIALECTS = crossDict(
        [{}, {'strictDiacriticPlacement': True}, {'toneMarkType': 'numbers'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'numbers', 'yaleFirstTone': '1stToneFalling'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'ignore',
                'yaleFirstTone': '1stToneFalling'},
            {'toneMarkType': 'none'}],
        [{}, {'strictSegmentation': True}],
        [{}, {'case': 'lower'}],
        )


# TODO
class CantoneseYaleOperatorReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'CantoneseYale'

    DECOMPOSITION_REFERENCES = [
        ({}, [
            ('gwóngjàuwá', ['gwóng', 'jàu', 'wá']),
            ('yuhtyúh', ['yuht', 'yúh']),
            ('néihhóu', ['néih', 'hóu']),
            ('gwóngjaù', ['gwóng', 'jaù']), # wrong placement of tone
            ('GWÓNGJÀUWÁ', ['GWÓNG', 'JÀU', 'WÁ']),
            ('sīsísisìhsíhsihsīksiksihk', ['sī', 'sí', 'si', 'sìh', 'síh',
                'sih', 'sīk', 'sik', 'sihk']),
            ('SÌSÍSISÌHSÍHSIHSĪKSIKSIHK', ['SÌ', 'SÍ', 'SI', 'SÌH', 'SÍH',
                'SIH', 'SĪK', 'SIK', 'SIHK']),
            ]),
        ({'toneMarkType': 'numbers'}, [
            ('gwong2jau1wa2', ['gwong2', 'jau1', 'wa2']),
            ('yut6yu5', ['yut6', 'yu5']),
            ('nei5hou2', ['nei5', 'hou2']),
            ('GWONG2JAU1WA2', ['GWONG2', 'JAU1', 'WA2']),
            ('si1si2si3si4si5si6sik1sik3sik6', ['si1', 'si2', 'si3', 'si4',
                'si5', 'si6', 'sik1', 'sik3', 'sik6']),
            ('SI1SI2SI3SI4SI5SI6SIK1SIK3SIK6', ['SI1', 'SI2', 'SI3', 'SI4',
                'SI5', 'SI6', 'SIK1', 'SIK3', 'SIK6']),
            ]),
        ({'strictDiacriticPlacement': True}, [
            ('gwóngjàuwá', ['gwóng', 'jàu', 'wá']),
            ('yuhtyúh', ['yuht', 'yúh']),
            ('néihhóu', ['néih', 'hóu']),
            ('gwóngjaù', ['gwóngjaù']), # wrong placement of tone
            ])
        ]
    COMPOSITION_REFERENCES = [
        ({}, [
            (['gwóng', 'jàu', 'wá'], 'gwóngjàuwá'),
            (['yuht', 'yúh'], 'yuhtyúh'),
            (['gwóng', 'jaù'], 'gwóngjaù'), # wrong placement of tone
            (['GWÓNG', 'JÀU', 'WÁ'], 'GWÓNGJÀUWÁ'),
            (['sī', 'sí', 'si', 'sìh', 'síh', 'sih', 'sīk', 'sik',
                'sihk'], 'sīsísisìhsíhsihsīksiksihk'),
            (['SÌ', 'SÍ', 'SI', 'SÌH', 'SÍH', 'SIH', 'SĪK', 'SIK',
                'SIHK'], 'SÌSÍSISÌHSÍHSIHSĪKSIKSIHK'),
            ]),
        ({'toneMarkType': 'numbers'}, [
            (['gwong2', 'jau1', 'wa2'], 'gwong2jau1wa2'),
            (['yut6', 'yu5'], 'yut6yu5'),
            (['GWONG2', 'JAU1', 'WA2'], 'GWONG2JAU1WA2'),
            (['si1', 'si2', 'si3', 'si4', 'si5', 'si6', 'sik1', 'sik3',
                'sik6'], 'si1si2si3si4si5si6sik1sik3sik6'),
            (['SI1', 'SI2', 'SI3', 'SI4', 'SI5', 'SI6', 'SIK1', 'SIK3',
                'SIK6'], 'SI1SI2SI3SI4SI5SI6SIK1SIK3SIK6'),
            ]),
        ({'strictDiacriticPlacement': True}, [
            (['gwóng', 'jàu', 'wá'], 'gwóngjàuwá'),
            (['yuht', 'yúh'], 'yuhtyúh'),
            (['gwóng', 'jaù'], exception.CompositionError),
                # wrong placement of tone
            (['jau\u0300', 'gwóng'], exception.CompositionError),
                # wrong placement of tone
            ]),
        ({'toneMarkType': 'numbers', 'missingToneMark': 'ignore'}, [
            (['gwong2', 'jau1', 'wa2'], 'gwong2jau1wa2'),
            (['gwong2', 'jau', 'wa2'], exception.CompositionError),
            ])
        ]

    READING_ENTITY_REFERENCES = [
        ({}, [
            ('wā', True),
            ('gwóng', True),
            ('jàu', True),
            ('wá', True),
            ('néih', True),
            ('yuht', True),
            ('gwong', True),
            ('wa\u0304', True),
            ('jaù', True),
            ('gwongh', True),
            ('wáa', False),
            ('GWÓNG', True),
            ('SIK', True),
            ('bàt', False), # stop tone
            ('bat4', False), # stop tone
            ]),
        ({'strictDiacriticPlacement': True}, [
            ('wā', True),
            ('gwóng', True),
            ('jàu', True),
            ('wá', True),
            ('néih', True),
            ('yuht', True),
            ('gwong', True),
            ('wa\u0304', True),
            ('jaù', False),
            ('gwongh', False),
            ('wáa', False),
            ('GWÓNG', True),
            ('SIK', True),
            ('bàt', False), # stop tone
            ('bat4', False), # stop tone
            ]),
        ({'case': 'lower'}, [
            ('wā', True),
            ('gwóng', True),
            ('jàu', True),
            ('wá', True),
            ('néih', True),
            ('yuht', True),
            ('gwong', True),
            ('wa\u0304', True),
            ('jaù', True),
            ('gwongh', True),
            ('wáa', False),
            ('GWÓNG', False),
            ('SIK', False),
            ('bàt', False), # stop tone
            ('bat4', False), # stop tone
            ]),
        ]

    GUESS_DIALECT_REFERENCES = [
        ("Mh", {'toneMarkType': 'diacritics'}),
        ("YUHT", {'toneMarkType': 'diacritics'}),
        ("yuht", {'toneMarkType': 'diacritics'}),
        ("wā", {'toneMarkType': 'diacritics'}),
        ("gwong2", {'toneMarkType': 'numbers'}),
        ]


class JyutpingOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'Jyutping'

    DIALECTS = crossDict(
        [{}, {'missingToneMark': 'ignore'}, {'toneMarkType': 'none'}],
        [{}, {'strictSegmentation': True}],
        [{}, {'case': 'lower'}],
        )


# TODO
class JyutpingOperatorReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'Jyutping'

    DECOMPOSITION_REFERENCES = [
        ({}, [
            ('gwong2zau1waa2', ['gwong2', 'zau1', 'waa2']),
            ]),
        ]

    COMPOSITION_REFERENCES = [
        ({}, [
            (['gwong2', 'zau1', 'waa2'], 'gwong2zau1waa2'),
            ]),
        ({'missingToneMark': 'ignore'}, [
            (['gwong2', 'zau1', 'waa2'], 'gwong2zau1waa2'),
            (['gwong2', 'zau', 'waa2'], exception.CompositionError),
            ]),
        ]

    READING_ENTITY_REFERENCES = [
        ({}, [
            ('si1', True),
            ('si2', True),
            ('si3', True),
            ('si4', True),
            ('si5', True),
            ('si6', True),
            ('sik1', True),
            ('sik2', False), # stop tone
            ('sik3', True),
            ('sik4', False), # stop tone
            ('sik5', False), # stop tone
            ('sik6', True),
            ]),
        ]


class HangulOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'Hangul'


# TODO
class HangulOperatorReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'Hangul'

    DECOMPOSITION_REFERENCES = [
        ({}, [
            ("한글은 한국어의 고유", ["한", "글", "은", " ",
                "한", "국", "어", "의", " ", "고", "유"]),
            ]),
        ]

    COMPOSITION_REFERENCES = [
        ({}, [
            (["한", "글", "은", " ", "한", "국", "어", "의", " ", "고",
                "유"], "한글은 한국어의 고유"),
            ]),
        ]

    READING_ENTITY_REFERENCES = []


class HiraganaOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'Hiragana'


# TODO
#class HiraganaOperatorReferenceTest(ReadingOperatorReferenceTest,
    #unittest.TestCase):
    #READING_NAME = 'Hiragana'

    #DECOMPOSITION_REFERENCES = []

    #COMPOSITION_REFERENCES = []

    #READING_ENTITY_REFERENCES = []


class KatakanaOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'Katakana'


# TODO
#class KatakanaOperatorReferenceTest(ReadingOperatorReferenceTest,
    #unittest.TestCase):
    #READING_NAME = 'Katakana'

    #DECOMPOSITION_REFERENCES = []

    #COMPOSITION_REFERENCES = []

    #READING_ENTITY_REFERENCES = []


class KanaOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'Kana'


# TODO
#class KanaOperatorReferenceTest(ReadingOperatorReferenceTest,
    #unittest.TestCase):
    #READING_NAME = 'Kana'

    #DECOMPOSITION_REFERENCES = []

    #COMPOSITION_REFERENCES = []

    #READING_ENTITY_REFERENCES = []


class PinyinOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'Pinyin'

    def _noToneApostropheRule(operatorInst, precedingEntity, followingEntity):
        return precedingEntity and precedingEntity[0].isalpha() \
            and not precedingEntity[-1].isdigit() \
            and followingEntity[0].isalpha()
    noToneApostropheRule = staticmethod(_noToneApostropheRule)

    DIALECTS = crossDict(
         [{}, {'toneMarkType': 'numbers'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'fifth'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'numbers', 'yVowel': 'v'},
            {'toneMarkType': 'numbers', 'yVowel': 'uu'},
            {'toneMarkType': 'none'},
            {'pinyinDiacritics': ('\u0304', '\u0301', '\u0306', '\u0300')},
            {'pinyinDiacritics': ('\u0304', '\u0301', '\u0302', '\u0300')},
            {'strictDiacriticPlacement': True}],
        [{}, {'pinyinApostrophe': '’'}],
        [{}, {'pinyinApostropheFunction': _noToneApostropheRule}],
        [{}, {'erhua': 'oneSyllable'}, {'erhua': 'ignore'}],
        [{}, {'strictSegmentation': True}],
        [{}, {'case': 'lower'}],
        [{}, {'shortenedLetters': True}],
        )

    def cleanDecomposition(self, decomposition, reading, **options):
        if not hasattr(self, '_operators'):
            self._operators = []
        for operatorReading, operatorOptions, op in self._operators:
            if reading == operatorReading and options == operatorOptions:
                break
        else:
            op = self.f.createReadingOperator(reading, **options)
            self._operators.append((reading, options, op))

        return op.removeApostrophes(decomposition)


class PinyinOperatorReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'Pinyin'

    DECOMPOSITION_REFERENCES = [
        ({}, [
            ("tiān'ānmén", ["tiān", "'", "ān", "mén"]),
            ("xian", ["xian"]),
            ("xīān", ["xī", "ān"]),
            ("tian1'an1men2", ["tian1", "'", "an1", "men2"]),
            ("tian'anmen", ["tian", "'", "an", "men"]),
            ("xi1an1", ["xi1", "an1"]),
            ("lao3tou2r5", ["lao3", "tou2", "r5"]),
            ("lao3tour2", ["lao3", "tour2"]),
            ("er2hua4yin1", ["er2", "hua4", "yin1"]),
            ("peínǐ", ['peí', 'nǐ']), # wrong placement of tone
            ("hónglùo", ['hóng', 'lùo']), # wrong placement of tone
            ("Tiān'ānmén", ["Tiān", "'", "ān", "mén"]),
            ("TIĀN'ĀNMÉN", ["TIĀN", "'", "ĀN", "MÉN"]),
            ("XIAN", ["XIAN"]),
            ("TIAN1'AN1MEN2", ["TIAN1", "'", "AN1", "MEN2"]),
            ('tiananmen', exception.DecompositionError),
            ('zhīshi', ['zhī', 'shi']),
            ]),
        ({'toneMarkType': 'numbers'}, [
            ("tiān'ānmén", ["tiān", "'", "ānmén"]),
            ("xian", ["xian"]),
            ("xīān", ["xīān"]),
            ("tian1'an1men2", ["tian1", "'", "an1", "men2"]),
            ("tian'anmen", ["tian", "'", "an", "men"]),
            ("xi1an1", ["xi1", "an1"]),
            ("lao3tou2r5", ["lao3", "tou2", "r5"]),
            ("lao3tour2", ["lao3", "tour2"]),
            ("er2hua4yin1", ["er2", "hua4", "yin1"]),
            ("peínǐ", ['peínǐ']), # wrong placement of tone
            ("hónglùo", ['hónglùo']), # wrong placement of tone
            ("Tiān'ānmén", ["Tiān", "'", "ānmén"]),
            ("TIĀN'ĀNMÉN", ["TIĀN", "'", "ĀNMÉN"]),
            ("XIAN", ["XIAN"]),
            ("TIAN1'AN1MEN2", ["TIAN1", "'", "AN1", "MEN2"]),
            ]),
        ({'toneMarkType': 'numbers', 'missingToneMark': 'ignore'}, [
            ("tiān'ānmén", ["tiān", "'", "ānmén"]),
            ("xian", ["xian"]),
            ("xīān", ["xīān"]),
            ("tian1'an1men2", ["tian1", "'", "an1", "men2"]),
            ("tian'anmen", ["tian", "'", "anmen"]),
            ("xi1an1", ["xi1", "an1"]),
            ("lao3tou2r5", ["lao3", "tou2", "r5"]),
            ("lao3tour2", ["lao3", "tour2"]),
            ("er2hua4yin1", ["er2", "hua4", "yin1"]),
            ("peínǐ", ['peínǐ']), # wrong placement of tone
            ("hónglùo", ['hónglùo']), # wrong placement of tone
            ("Tiān'ānmén", ["Tiān", "'", "ānmén"]),
            ("TIĀN'ĀNMÉN", ["TIĀN", "'", "ĀNMÉN"]),
            ("XIAN", ["XIAN"]),
            ("TIAN1'AN1MEN2", ["TIAN1", "'", "AN1", "MEN2"]),
            ]),
        ({'erhua': 'oneSyllable'}, [
            ("tiān'ānmén", ["tiān", "'", "ān", "mén"]),
            ("xian", ["xian"]),
            ("xīān", ["xī", "ān"]),
            ("tian1'an1men2", ["tian1", "'", "an1", "men2"]),
            ("tian'anmen", ["tian", "'", "an", "men"]),
            ("xi1an1", ["xi1", "an1"]),
            ("lao3tou2r5", ["lao3", "tou2", "r5"]),
            ("lao3tour2", ["lao3", "tour2"]),
            ("er2hua4yin1", ["er2", "hua4", "yin1"]),
            ("peínǐ", ['peí', 'nǐ']), # wrong placement of tone
            ("hónglùo", ['hóng', 'lùo']), # wrong placement of tone
            ("Tiān'ānmén", ["Tiān", "'", "ān", "mén"]),
            ("TIĀN'ĀNMÉN", ["TIĀN", "'", "ĀN", "MÉN"]),
            ("XIAN", ["XIAN"]),
            ("TIAN1'AN1MEN2", ["TIAN1", "'", "AN1", "MEN2"]),
            ]),
        ({'strictDiacriticPlacement': True}, [
            ("tiān'ānmén", ["tiān", "'", "ān", "mén"]),
            ("xian", ["xian"]),
            ("xīān", ["xī", "ān"]),
            ("tian1'an1men2", ["tian1", "'", "an1", "men2"]),
            ("tian'anmen", ["tian", "'", "an", "men"]),
            ("xi1an1", ["xi1", "an1"]),
            ("lao3tou2r5", ["lao3", "tou2", "r5"]),
            ("lao3tour2", ["lao3", "tour2"]),
            ("er2hua4yin1", ["er2", "hua4", "yin1"]),
            ("peínǐ", ['peínǐ']), # wrong placement of tone
            ("hónglùo", ['hóng', 'lù', 'o']), # wrong placement of tone
            ("Tiān'ānmén", ["Tiān", "'", "ān", "mén"]),
            ("TIĀN'ĀNMÉN", ["TIĀN", "'", "ĀN", "MÉN"]),
            ("XIAN", ["XIAN"]),
            ("TIAN1'AN1MEN2", ["TIAN1", "'", "AN1", "MEN2"]),
            ]),
        ({'case': 'lower'}, [
            ("tiān'ānmén", ["tiān", "'", "ān", "mén"]),
            ("xian", ["xian"]),
            ("xīān", ["xī", "ān"]),
            ("tian1'an1men2", ["tian1", "'", "an1", "men2"]),
            ("tian'anmen", ["tian", "'", "an", "men"]),
            ("xi1an1", ["xi1", "an1"]),
            ("lao3tou2r5", ["lao3", "tou2", "r5"]),
            ("lao3tour2", ["lao3", "tour2"]),
            ("er2hua4yin1", ["er2", "hua4", "yin1"]),
            ("peínǐ", ['peí', 'nǐ']), # wrong placement of tone
            ("hónglùo", ['hóng', 'lùo']), # wrong placement of tone
            ("Tiān'ānmén", ["Tiān", "'", "ān", "mén"]),
            ("TIĀN'ĀNMÉN", ["TIĀN", "'", "ĀNMÉN"]),
            ("XIAN", ["XIAN"]),
            ("TIAN1'AN1MEN2", ["TIAN1", "'", "AN1", "MEN2"]),
            ]),
        ({'toneMarkType': 'numbers', 'yVowel': 'v'}, [
            ('nv3hai2', ['nv3', 'hai2']),
            ('nvhai', ['nv', 'hai']),
            ('nü3hai2', ['nü3', 'hai2']),
            ('nühai', ['nühai']),
            ]),
        ]

    COMPOSITION_REFERENCES = [
        ({}, [
            (["tiān", "ān", "mén"], "tiān'ānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xī'ān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1an1men2"),
            (["tian", "an", "men"], "tian'anmen"),
            (["xi1", "an1"], "xi1an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3angr2"),
            (["lao3", "ang2", "r5"], "lao3ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], "peínǐ"), # wrong placement of tone
            (['hóng', 'lùo'], "hónglùo"), # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀN'ĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1AN1MEN2", ),
            (["e", "r"], "e'r"),
            (["ti", "anr"], exception.CompositionError),
            (["chang", "an"], "chang'an"),
            (["ĉaŋ", "an"], exception.CompositionError),
            ]),
        ({'toneMarkType': 'numbers'}, [
            (["tiān", "ān", "mén"], "tiānānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xīān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1'an1men2"),
            (["tian", "an", "men"], "tian'anmen"),
            (["xi1", "an1"], "xi1'an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3angr2"),
            (["lao3", "ang2", "r5"], "lao3'ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], "peínǐ"), # wrong placement of tone
            (['hóng', 'lùo'], "hónglùo"), # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀNĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1'AN1MEN2", ),
            (["e", "r"], "e'r"),
            ]),
        ({'toneMarkType': 'numbers', 'missingToneMark': 'ignore'}, [
            (["tiān", "ān", "mén"], "tiānānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xīān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1'an1men2"),
            (["tian", "an", "men"], "tiananmen"),
            (["xi1", "an1"], "xi1'an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3angr2"),
            (["lao3", "ang2", "r5"], "lao3'ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], "peínǐ"), # wrong placement of tone
            (['hóng', 'lùo'], "hónglùo"), # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀNĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1'AN1MEN2", ),
            (["e5", "r5"], "e5'r5"),
            ]),
        ({'erhua': 'oneSyllable'}, [
            (["tiān", "ān", "mén"], "tiān'ānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xī'ān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1an1men2"),
            (["tian", "an", "men"], "tian'anmen"),
            (["xi1", "an1"], "xi1an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3angr2"),
            (["lao3", "ang2", "r5"], "lao3ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], "peínǐ"), # wrong placement of tone
            (['hóng', 'lùo'], "hónglùo"), # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀN'ĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1AN1MEN2", ),
            (["e", "r"], exception.CompositionError),
            ]),
        ({'toneMarkType': 'numbers', 'erhua': 'oneSyllable'}, [
            (["tiān", "ān", "mén"], "tiānānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xīān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1'an1men2"),
            (["tian", "an", "men"], "tian'anmen"),
            (["xi1", "an1"], "xi1'an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3'angr2"),
            (["lao3", "ang2", "r5"], "lao3'ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], "peínǐ"), # wrong placement of tone
            (['hóng', 'lùo'], "hónglùo"), # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀNĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1'AN1MEN2", ),
            (["e", "r"], exception.CompositionError),
            ]),
        ({'strictDiacriticPlacement': True}, [
            (["tiān", "ān", "mén"], "tiān'ānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xī'ān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1an1men2"),
            (["tian", "an", "men"], "tian'anmen"),
            (["xi1", "an1"], "xi1an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3angr2"),
            (["lao3", "ang2", "r5"], "lao3ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], exception.CompositionError),
                # wrong placement of tone
            (['hóng', 'lùo'], exception.CompositionError),
                # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀN'ĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1AN1MEN2", ),
            (["e", "r"], "e'r"),
            ]),
        ({'toneMarkType': 'numbers', 'yVowel': 'v'}, [
            (['nv3', 'hai2'], 'nv3hai2'),
            (['nü3', 'hai2'], 'nü3hai2'),
            ]),
        ({'shortenedLetters': True}, [
            (["tiān", "ān", "mén"], "tiān'ānmén"),
            (["xian"], "xian"),
            (["xī", "ān"], "xī'ān"),
            (["tian1", "'", "an1", "men2"], "tian1'an1men2"),
            (["tian1", "an1", "men2"], "tian1an1men2"),
            (["tian", "an", "men"], "tian'anmen"),
            (["xi1", "an1"], "xi1an1"),
            (["lao3", "tou2", "r5"], "lao3tou2r5"),
            (["lao3", "tour2"], "lao3tour2"),
            (["lao3", "angr2"], "lao3angr2"),
            (["lao3", "ang2", "r5"], "lao3ang2r5"),
            (["er2", "hua4", "yin1"], "er2hua4yin1"),
            (['peí', 'nǐ'], "peínǐ"), # wrong placement of tone
            (["TIĀN", "ĀN", "MÉN"], "TIĀN'ĀNMÉN"),
            (["TIAN1", "AN1", "MEN2"], "TIAN1AN1MEN2", ),
            (["e", "r"], "e'r"),
            (["ti", "anr"], exception.CompositionError),
            (["chang", "an"], exception.CompositionError),
            (["ĉaŋ", "an"], "ĉaŋ'an"),
            ]),
        ]

    READING_ENTITY_REFERENCES = [
        ({}, [
            ("tiān", True),
            ("ān", True),
            ("mén", True),
            ("lào", True),
            ("xǐ", True),
            ("lü", True),
            ("ê", True),
            ("Ê", True),
            ("tian1", False),
            ("an1", False),
            ("men2", False),
            ("lao4", False),
            ("xi3", False),
            ("xian", True),
            ("ti\u0304an", True),
            ("tia\u0304n", True),
            ("laǒ", True),
            ("tīan", True),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", True),
            ("XIAN", True),
            ("TIAN1", False),
            ("r1", False),
            ("zhī", True),
            ("tang", True),
            ("ẑī", False),
            ("taŋ", False),
            ("ề", True),
            ]),
        ({'toneMarkType': 'numbers'}, [
            ("tiān", False),
            ("ān", False),
            ("mén", False),
            ("lào", False),
            ("xǐ", False),
            ("lü", True),
            ("ê", True),
            ("tian1", True),
            ("an1", True),
            ("men2", True),
            ("lao4", True),
            ("xi3", True),
            ("xian", True),
            ("ti\u0304an", False),
            ("tia\u0304n", False),
            ("laǒ", False),
            ("tīan", False),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", False),
            ("XIAN", True),
            ("TIAN1", True),
            ("r1", False),
            ("ề", False),
            ]),
        ({'toneMarkType': 'numbers', 'missingToneMark': 'ignore'}, [
            ("tiān", False),
            ("ān", False),
            ("mén", False),
            ("lào", False),
            ("xǐ", False),
            ("lü", False),
            ("ê", False),
            ("tian1", True),
            ("an1", True),
            ("men2", True),
            ("lao4", True),
            ("xi3", True),
            ("xian", False),
            ("ti\u0304an", False),
            ("tia\u0304n", False),
            ("laǒ", False),
            ("tīan", False),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", False),
            ("r", False),
            ("TIĀN", False),
            ("XIAN", False),
            ("TIAN1", True),
            ("r1", False),
            ("ề", False),
            ]),
        ({'erhua': 'oneSyllable'}, [
            ("tiān", True),
            ("ān", True),
            ("mén", True),
            ("lào", True),
            ("xǐ", True),
            ("lü", True),
            ("ê", True),
            ("tian1", False),
            ("an1", False),
            ("men2", False),
            ("lao4", False),
            ("xi3", False),
            ("xian", True),
            ("ti\u0304an", True),
            ("tia\u0304n", True),
            ("laǒ", True),
            ("tīan", True),
            ("tīa", False),
            ("tiā", False),
            ("angr", True),
            ("er", True),
            ("r", False),
            ("TIĀN", True),
            ("XIAN", True),
            ("TIAN1", False),
            ("r1", False),
            ("ề", True),
            ]),
        ({'strictDiacriticPlacement': True}, [
            ("tiān", True),
            ("ān", True),
            ("mén", True),
            ("lào", True),
            ("xǐ", True),
            ("lü", True),
            ("ê", True),
            ("tian1", False),
            ("an1", False),
            ("men2", False),
            ("lao4", False),
            ("xi3", False),
            ("xian", True),
            ("tia\u0304n", True),
            ("ti\u0304an", False),
            ("laǒ", False),
            ("tīan", False),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", True),
            ("XIAN", True),
            ("TIAN1", False),
            ("r1", False),
            ("ề", True),
            ]),
        ({'case': 'lower'}, [
            ("tiān", True),
            ("ān", True),
            ("mén", True),
            ("lào", True),
            ("xǐ", True),
            ("lü", True),
            ("ê", True),
            ("tian1", False),
            ("an1", False),
            ("men2", False),
            ("lao4", False),
            ("xi3", False),
            ("xian", True),
            ("ti\u0304an", True),
            ("tia\u0304n", True),
            ("laǒ", True),
            ("tīan", True),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", False),
            ("XIAN", False),
            ("TIAN1", False),
            ("r1", False),
            ("ề", True),
            ]),
        ({'toneMarkType': 'numbers', 'yVowel': 'v'}, [
            ("tiān", False),
            ("ān", False),
            ("mén", False),
            ("lào", False),
            ("xǐ", False),
            ("lü", False),
            ("lv", True),
            ("ê", True),
            ("tian1", True),
            ("an1", True),
            ("men2", True),
            ("lao4", True),
            ("xi3", True),
            ("xian", True),
            ("ti\u0304an", False),
            ("tia\u0304n", False),
            ("laǒ", False),
            ("tīan", False),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", False),
            ("XIAN", True),
            ("TIAN1", True),
            ("r1", False),
            ("ề", False),
            ]),
        ({'shortenedLetters': True}, [
            ("tiān", True),
            ("ān", True),
            ("mén", True),
            ("lào", True),
            ("xǐ", True),
            ("lü", True),
            ("ê", True),
            ("Ê", True),
            ("tian1", False),
            ("an1", False),
            ("men2", False),
            ("lao4", False),
            ("xi3", False),
            ("xian", True),
            ("ti\u0304an", True),
            ("tia\u0304n", True),
            ("laǒ", True),
            ("tīan", True),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", True),
            ("XIAN", True),
            ("TIAN1", False),
            ("r1", False),
            ("zhī", False),
            ("tang", False),
            ("ẑī", True),
            ("taŋ", True),
            ("ŜAŊ", True),
            ("ề", True),
            ]),
        ({'pinyinDiacritics': ('\u0304', '\u0301', '\u0302', '\u0300')}, [
            ("tiān", True),
            ("ān", True),
            ("mén", True),
            ("lào", True),
            ("xǐ", False),
            ("lü", True),
            ("ê", True),
            ("Ê", True),
            ("tian1", False),
            ("an1", False),
            ("men2", False),
            ("lao4", False),
            ("xi3", False),
            ("xian", True),
            ("ti\u0304an", True),
            ("tia\u0304n", True),
            ("laǒ", False),
            ("tīan", True),
            ("tīa", False),
            ("tiā", False),
            ("angr", False),
            ("er", True),
            ("r", True),
            ("TIĀN", True),
            ("XIAN", True),
            ("TIAN1", False),
            ("r1", False),
            ("zhī", True),
            ("tang", True),
            ("ẑī", False),
            ("taŋ", False),
            ("ề", False),
            ]),
        ]

    STRICT_DECOMPOSITION_REFERENCES = [
        ({}, [
            (["tiān", "'", "ān", "mén"], True),
            (["tiān", "ān", "mén"], False),
            (["chan", "gan"], True),
            (["xian"], True),
            (["tian1", "an1", "men2"], True),
            (["tian", "an", "men"], False),
            (["tian", "'", "an", "men"], True),
            (["lao3", "angr2"], True),
            (["lao3", "ang2", "r5"], True),
            (["TIĀN", "ĀN", "MÉN"], False),
            (["TIAN1", "AN1", "MEN2"], True),
            ]),
        ({'toneMarkType': 'numbers'}, [
            (["tiān", "'", "ān", "mén"], True),
            (["tiān", "ān", "mén"], True),
            (["chan", "gan"], True),
            (["xian"], True),
            (["tian1", "an1", "men2"], False),
            (["tian", "an", "men"], False),
            (["tian", "'", "an", "men"], True),
            (["lao3", "angr2"], True),
            (["lao3", "ang2", "r5"], False),
            (["TIĀN", "ĀN", "MÉN"], True),
            (["TIAN1", "AN1", "MEN2"], False),
            ]),
        ({'toneMarkType': 'numbers', 'missingToneMark': 'ignore'}, [
            (["tiān", "'", "ān", "mén"], True),
            (["tiān", "ān", "mén"], True),
            (["chan", "gan"], True),
            (["xian"], True),
            (["tian1", "an1", "men2"], False),
            (["tian", "an", "men"], True),
            (["tian", "'", "an", "men"], True),
            (["lao3", "angr2"], True),
            (["lao3", "ang2", "r5"], False),
            (["TIĀN", "ĀN", "MÉN"], True),
            (["TIAN1", "AN1", "MEN2"], False),
            ]),
        ({'toneMarkType': 'numbers', 'erhua': 'oneSyllable'}, [
            (["tiān", "'", "ān", "mén"], True),
            (["tiān", "ān", "mén"], True),
            (["chan", "gan"], True),
            (["xian"], True),
            (["tian1", "an1", "men2"], False),
            (["tian", "an", "men"], False),
            (["tian", "'", "an", "men"], True),
            (["lao3", "angr2"], False),
            (["lao3", "ang2", "r5"], False),
            (["TIĀN", "ĀN", "MÉN"], True),
            (["TIAN1", "AN1", "MEN2"], False),
            ]),
        ]

    GUESS_DIALECT_REFERENCES = [
        ("tiān'ānmén", {'toneMarkType': 'diacritics',
            'pinyinApostrophe': "'"}),
        ("tiān’ānmén", {'toneMarkType': 'diacritics',
            'pinyinApostrophe': "’"}),
        ("xīān", {'toneMarkType': 'diacritics'}),
        ("tian1'an1men2", {'toneMarkType': 'numbers',
            'pinyinApostrophe': "'"}),
        ("nv3hai2", {'toneMarkType': 'numbers', 'yVowel': 'v'}),
        ("NV3HAI2", {'toneMarkType': 'numbers', 'yVowel': 'v'}),
        ("nuu3hai2", {'toneMarkType': 'numbers', 'yVowel': 'uu'}),
        ("nǚhái", {'toneMarkType': 'diacritics', 'yVowel': 'ü'}),
        ("NǙHÁI", {'toneMarkType': 'diacritics', 'yVowel': 'ü'}),
        ("xi1'an1", {'toneMarkType': 'numbers', 'pinyinApostrophe': "'"}),
        ("lao3tou2r5", {'toneMarkType': 'numbers',
            'erhua': 'twoSyllables'}),
        ("lao3tour2", {'toneMarkType': 'numbers', 'erhua': 'oneSyllable'}),
        ("peínǐ", {'toneMarkType': 'diacritics'}), # wrong placement of tone
        ("TIĀNĀNMÉN", {'toneMarkType': 'diacritics'}),
        ("e5'r5", {'toneMarkType': 'numbers', 'pinyinApostrophe': "'",
            'erhua': 'twoSyllables'}),
        ("yi xia r ", {'toneMarkType': 'numbers', 'erhua': 'twoSyllables'}),
        ("ẑīdao", {'toneMarkType': 'diacritics', 'shortenedLetters': True}),
        ("mian4taŋ1", {'toneMarkType': 'numbers', 'shortenedLetters': True}),
        ("ŜÀŊHǍI", {'toneMarkType': 'diacritics', 'shortenedLetters': True,
            'pinyinDiacritics': ('\u0304', '\u0301', '\u030c', '\u0300')}),
        ("SHÀNGHǍI", {'toneMarkType': 'diacritics',
            'shortenedLetters': False}),
        ("Wŏ huì shuō yìdiănr", {'toneMarkType': 'diacritics',
            'pinyinDiacritics': ('\u0304', '\u0301', '\u0306', '\u0300')}),
        ("Xiàndài Hànyû Dàcídiân", {'toneMarkType': 'diacritics',
            'pinyinDiacritics': ('\u0304', '\u0301', '\u0302', '\u0300')}),
        ("ê Hàn", {'pinyinDiacritics': ('\u0304', '\u0301', '\u030c',
            '\u0300')}),
        ]

    def testStrictDecompositionReferences(self):
        """Test if the given decomposition references pass strictness test."""
        for dialect, references in self.STRICT_DECOMPOSITION_REFERENCES:
            for reference, target in references:
                result = self.f.isStrictDecomposition(reference,
                    self.READING_NAME, **dialect)
                self.assertEqual(result, target,
                    "Target %s of %s not reached: %s" \
                        % (repr(target), repr(reference), repr(result)) \
                    + ' (reading %s, dialect %s)' \
                        % (self.READING_NAME, dialect))


class WadeGilesOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'WadeGiles'

    DIALECTS = crossDict(
        [{}, {'diacriticE': 'e'}],
        [{}, {'zeroFinal': 'u'}],
        [{}, {'umlautU': 'u'}],
        [{}, {'useInitialSz': True}],
        [{}, {'neutralToneMark': 'zero'}, {'neutralToneMark': 'five'}],
        [{}, {'wadeGilesApostrophe': "'"}],
        [{}, {'toneMarkType': 'numbers'}, {'toneMarkType': 'none'}],
        [{}, {'missingToneMark': 'ignore'}],
        [{}, {'strictSegmentation': True}],
        [{}, {'case': 'lower'}],
        )

    def cleanDecomposition(self, decomposition, reading, **options):
        if not hasattr(self, '_operators'):
            self._operators = []
        for operatorReading, operatorOptions, op in self._operators:
            if reading == operatorReading and options == operatorOptions:
                break
        else:
            op = self.f.createReadingOperator(reading, **options)
            self._operators.append((reading, options, op))

        return op.removeHyphens(decomposition)


class WadeGilesOperatorReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'WadeGiles'

    DECOMPOSITION_REFERENCES = [
        ({}, [
            ("K’ung³-tzŭ³", ["K’ung³", "-", "tzŭ³"]),
            ("Ssŭma Ch’ien", ["Ssŭ", "ma", " ", "Ch’ien"]),
            ]),
        ({'wadeGilesApostrophe': "'", 'zeroFinal': 'u'}, [
            ("Ssuma Ch'ien", ["Ssu", "ma", " ", "Ch'ien"]),
            ]),
        ({'wadeGilesApostrophe': "'"}, [
            ("Ssuma Ch'ien", ["Ssuma", " ", "Ch'ien"]),
            ("Ssŭma Ch'ien", ["Ssŭ", "ma", " ", "Ch'ien"]),
            ]),
        ({'wadeGilesApostrophe': "'", 'zeroFinal': 'u'}, [
            ("Ssuma Ch'ien", ["Ssu", "ma", " ", "Ch'ien"]),
            ("Ssŭma Ch'ien", ["Ssŭma", " ", "Ch'ien"]),
            ]),
        ({'toneMarkType': 'numbers', 'umlautU': 'u'}, [
            ("Shih3-Chi4", ["Shih3", "-", "Chi4"]),
            ("chueh1", ["chueh1"])
            ]),
        ({'wadeGilesApostrophe': "'", 'strictSegmentation': True}, [
            ("Ssuma Ch'ien", exception.DecompositionError),
            ("Ssŭma Ch'ien", ["Ssŭ", "ma", " ", "Ch'ien"]),
            ]),
        ]

    COMPOSITION_REFERENCES = [
        ({}, [
            (["K’ung³", "-", "tzŭ³"], "K’ung³-tzŭ³"),
            (["K’ung³", "tzŭ³"], "K’ung³-tzŭ³"),
            ]),
        ({'wadeGilesApostrophe': "'", 'zeroFinal': 'u'}, [
            (["Ssu", "ma", " ", "Ch'ien"], "Ssu-ma Ch'ien"),
            ]),
        ({'wadeGilesApostrophe': "'"}, [
            (["Ssu", "ma", " ", "Ch'ien"], exception.CompositionError),
            (["Ssŭ", "ma", " ", "Ch'ien"], "Ssŭ-ma Ch'ien"),
            ]),
        ({'toneMarkType': 'numbers'}, [
            (["Shih3", "-", "Chi4"], "Shih3-Chi4"),
            (["Shih3", "Chi4"], "Shih3-Chi4"),
            (['t', '’', 'ung1'], exception.CompositionError),
            ]),
        ({'toneMarkType': 'numbers', 'neutralToneMark': 'zero',
            'missingToneMark': 'ignore'}, [
            (["Shih3", "-", "Chi"], "Shih3-Chi"),
            (["Shih3", "Chi"], "Shih3Chi"),
            (["Shih", "Chi4"], exception.CompositionError),
            ]),
        ]

    READING_ENTITY_REFERENCES = [
        ({}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", True),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ({'diacriticE': 'e'}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", True),
            ("ch’êng", False),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", True),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ({'zeroFinal': 'u'}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", False),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", True),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ({'neutralToneMark': 'zero'}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", True),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", True),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ({'neutralToneMark': 'five'}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", True),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", True),
            ("shih1", False),
            ]),
        ({'useInitialSz': True}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", False),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("szŭ", True),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ({'umlautU': 'u'}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", False),
            ("Ssŭ", True),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ({'toneMarkType': 'numbers'}, [
            ("shih", True),
            ("jou⁴", False),
            ("nü³", False),
            ("Ssŭ", True),
            ("ch’êng", True),
            ("Ch’ien", True),
            ("ch'ien", False),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", True),
            ]),
        ({'wadeGilesApostrophe': "'"}, [
            ("shih", True),
            ("jou⁴", True),
            ("nü³", True),
            ("Ssŭ", True),
            ("ch’êng", False),
            ("Ch’ien", False),
            ("ch'ien", True),
            ("ssu", False),
            ("szu", False),
            ("ch’eng", False),
            ("shih⁰", False),
            ("shih⁵", False),
            ("shih1", False),
            ]),
        ]

    GUESS_DIALECT_REFERENCES = [
        ("K’ung³-tzǔ³", {'toneMarkType': 'superscriptNumbers',
            'wadeGilesApostrophe': '’', 'zeroFinal': 'ǔ'}),
        ("K’ung³-tzŭ³", {'toneMarkType': 'superscriptNumbers',
            'wadeGilesApostrophe': '’', 'zeroFinal': 'ŭ'}),
        ("Ssŭma Ch'ien", {'wadeGilesApostrophe': "'", 'zeroFinal': 'ŭ'}),
        ("Szuma Ch'ien", {'wadeGilesApostrophe': "'", 'zeroFinal': 'u',
            'useInitialSz': True}),
        ("Szu1ma3 Ch'ien1", {'wadeGilesApostrophe': "'", 'zeroFinal': 'u',
            'useInitialSz': True, 'toneMarkType': 'numbers'}),
        ("Shih3-Chi4", {'toneMarkType': 'numbers'}),
        ("chih¹-tao⁵", {'neutralToneMark': 'five'}),
        ("chih¹-tao", {'neutralToneMark': 'none'}),
        ("p’êng3yu0", {'neutralToneMark': 'zero', 'diacriticE': 'ê',
            'wadeGilesApostrophe': '’', 'toneMarkType': 'numbers'}),
        ("p’eng³yu", {'neutralToneMark': 'none', 'diacriticE': 'e',
            'wadeGilesApostrophe': '’', 'toneMarkType': 'superscriptNumbers'}),
        ("hsu¹", {'umlautU': 'u', 'toneMarkType': 'superscriptNumbers'}),
        ("nueh1", {'umlautU': 'u', 'toneMarkType': 'numbers'}),
        ("yu³", {'umlautU': 'ü', 'toneMarkType': 'superscriptNumbers'}),
        ("Cheng Ho", {'diacriticE': 'e', 'neutralToneMark': 'zero'}),
            # either zero or five to enable tone "None" for all syllables
        ]

class GROperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'GR'

    DIALECTS = crossDict(
        [{}, {'strictSegmentation': True}],
        [{}, {'abbreviations': False}],
        [{}, {'grRhotacisedFinalApostrophe': "'"}],
        [{}, {'grSyllableSeparatorApostrophe': "'"}],
        [{}, {'optionalNeutralToneMarker': '₀'}],
        [{}, {'case': 'lower'}],
        )

    @staticmethod
    def testUpperCase(dialect):
        return dialect.get('case', None) != 'lower'

    def cleanDecomposition(self, decomposition, reading, **options):
        if not hasattr(self, '_operators'):
            self._operators = []
        for operatorReading, operatorOptions, op in self._operators:
            if reading == operatorReading and options == operatorOptions:
                break
        else:
            op = self.f.createReadingOperator(reading, **options)
            self._operators.append((reading, options, op))

        return op.removeApostrophes(decomposition)

    def testValidAbbreviatedEntitiesAccepted(self):
        """
        Test if all abbreviated reading entities returned by
        ``getAbbreviatedEntities()`` are accepted by ``isAbbreviatedEntity()``.
        """
        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            grOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            entities = grOperator.getAbbreviatedEntities()
            for entity in entities:
                self.assertTrue(
                    grOperator.isAbbreviatedEntity(entity),
                    "Abbreviated entity %s not accepted" % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

    def testAbbreviatedEntitiesConsistency(self):
        """
        Test if all abbreviated reading entities returned by
        ``getAbbreviatedEntities()`` are accepted by ``isAbbreviatedEntity()``.
        """
        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            grOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            fullEntities = grOperator.getFullReadingEntities()
            abbrevEntities = grOperator.getAbbreviatedEntities()
            # test abbreviated entity is not a full form
            for entity in abbrevEntities:
                self.assertTrue(entity not in fullEntities,
                    "Abbreviated entity %s is a full form" % repr(entity) \
                        + ' (reading %s, dialect %s)' \
                            % (self.READING_NAME, dialect))

            # test forms have valid entities
            for form in grOperator.getAbbreviatedForms():
                for entity in form:
                    self.assertTrue(entity in abbrevEntities \
                        or entity in fullEntities,
                        "Form %s has invalid entity %s" \
                            % (repr(form), repr(entity)) \
                            + ' (reading %s, dialect %s)' \
                                % (self.READING_NAME, dialect))

    @attr('quiteslow')
    def testRhotacisedEntitesBackConversion(self):
        """
        Test if complement methods ``getBaseEntitiesForRhotacised()`` and
        ``getRhotacisedTonalEntity()`` are consistent.
        """
        forms = []
        forms.extend(self.DIALECTS)
        if {} not in forms:
            forms.append({})
        for dialect in forms:
            grOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            plainEntities = grOperator.getPlainReadingEntities()

            rhotacisedDict = {}
            for plainEntity in plainEntities:
                for tone in grOperator.getTones():
                    try:
                        rhotacisedForm = grOperator.getRhotacisedTonalEntity(
                            plainEntity, tone)
                        if rhotacisedForm not in rhotacisedDict:
                            rhotacisedDict[rhotacisedForm] = set()
                        rhotacisedDict[rhotacisedForm].add(
                            (plainEntity, tone))
                    except exception.UnsupportedError:
                        pass

            # now check that back conversion gives us all the possible entities
            for rhotacisedForm in rhotacisedDict:
                entityPairs = grOperator.getBaseEntitiesForRhotacised(
                    rhotacisedForm)
                self.assertEqual(entityPairs, rhotacisedDict[rhotacisedForm])


#TODO
class GROperatorReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'GR'

    DECOMPOSITION_REFERENCES = [
        ({}, [
            ("tian’anmen", ["tian", "’", "an", "men"]),
            ("Beeijing", ["Beei", "jing"]),
            ("faan-guohlai", ["faan", "-", "guoh", "lai"]),
            ('"Haeshianq gen Muh.jianq"', ['"', "Hae", "shianq", " ", "gen",
                " ", "Muh", ".jianq", '"']),
            ("keesh", ["kee", "sh"]),
            ("yeou ideal", ["yeou", " ", "i", "deal"]),
            ("TIAN’ANMEN", ["TIAN", "’", "AN", "MEN"]),
            ("sherm.me", ["sherm", ".me"]),
            ("ig", ["i", "g"]),
            ]),
        ({'abbreviations': False}, [
            ("tian’anmen", ["tian", "’", "an", "men"]),
            ("Beeijing", ["Beei", "jing"]),
            ("faan-guohlai", ["faan", "-", "guoh", "lai"]),
            ('"Haeshianq gen Muh.jianq"', ['"', "Hae", "shianq", " ", "gen",
                " ", "Muh", ".jianq", '"']),
            ("keesh", ["keesh"]),
            ("yeou ideal", ["yeou", " ", "i", "deal"]),
            ("TIAN’ANMEN", ["TIAN", "’", "AN", "MEN"]),
            ("sherm.me", ["sherm", ".me"]),
            ("ig", ["ig"]),
            ]),
        ]

    COMPOSITION_REFERENCES = [
        ({}, [
            (["tian", "an", "men"], "tian’anmen"),
            (["tian", "’", "an", "men"], "tian’anmen"),
            (["Beei", "jing"], "Beeijing"),
            (["yeou", " ", "i", "deal"], "yeou ideal"),
            (["faan", "-", "guoh", "lai"], "faan-guohlai"),
            (["TIAN", "AN", "MEN"], "TIAN’ANMEN"),
            (["yeou", " ", "i", "dea'l"], exception.CompositionError),
            (["jie", "’", "l"], exception.CompositionError),
            (["sherm", ".me"], "sherm.me"),
            (["san", "g"], "san’g"),
            (["i", "g"], "ig"),
            ]),
        ({'abbreviations': False}, [
            (["tian", "an", "men"], "tian’anmen"),
            (["tian", "’", "an", "men"], "tian’anmen"),
            (["Beei", "jing"], "Beeijing"),
            (["yeou", " ", "i", "deal"], "yeou ideal"),
            (["faan", "-", "guoh", "lai"], "faan-guohlai"),
            (["TIAN", "AN", "MEN"], "TIAN’ANMEN"),
            (["yeou", " ", "i", "dea'l"], exception.CompositionError),
            (["jie", "’", "l"], exception.CompositionError),
            (["sherm", ".me"], exception.CompositionError),
            ]),
        ]

    READING_ENTITY_REFERENCES = [
        ({}, [
            ("shau", True),
            ("shao", True),
            ("shaw", True),
            ("dea’l", False),
            ("jie’l", True),
            ("jie'l", False),
            ("˳shyh", True),
            ("sh", True),
            ("j", True),
            ("jemm", True),
            ("JEMM", True),
            ("tzeem.me", False),
            (".v", True),
            ]),
        ({'abbreviations': False}, [
            ("shau", True),
            ("shao", True),
            ("shaw", True),
            ("dea’l", False),
            ("jie’l", True),
            ("jie'l", False),
            ("˳shyh", True),
            ("sh", False),
            ("j", False),
            ("jemm", False),
            ("JEMM", False),
            ("tzeem.me", False),
            (".v", False),
            ]),
        ]

    GUESS_DIALECT_REFERENCES = []

    ABBREVIATED_READING_ENTITY_REFERENCES = [
        ({}, [
            ("sh", True),
            ("SH", True),
            ("x", True),
            ]),
        ]

    def testAbbreviatedEntitiesReferences(self):
        """
        Test if abbreviated reading entity references are accepted by
        ``isAbbreviatedEntity()``.
        """
        for dialect, references in self.ABBREVIATED_READING_ENTITY_REFERENCES:
            grOperator = self.f.createReadingOperator(self.READING_NAME,
                **dialect)
            for reference, target in references:
                result = grOperator.isAbbreviatedEntity(reference)

                self.assertEqual(result, target,
                    "Target %s of %s not reached: %s" \
                        % (repr(target), repr(reference), repr(result)) \
                    + ' (reading %s, dialect %s)' \
                        % (self.READING_NAME, dialect))

    # The following mappings are taken from the Pinyin-to-GR Conversion Tables
    #   written/compiled by Richard Warmington from 12 December 1998,
    #   http://home.iprimus.com.au/richwarm/gr/pygrconv.txt
    # Entry for 'ri' has been corrected for tones 1, 2, 'yo' removed as no
    #   source given and rhoticised finals have been added.
    SPECIAL_MAPPING = """
zhi             jy      jyr     jyy     jyh
chi             chy     chyr    chyy    chyh
shi             shy     shyr    shyy    shyh
ri              rhy     ry      ryy     ryh
zi              tzy     tzyr    tzyy    tzyh
ci              tsy     tsyr    tsyy    tsyh
si              sy      syr     syy     syh

ju              jiu     jyu     jeu     jiuh
qu              chiu    chyu    cheu    chiuh
xu              shiu    shyu    sheu    shiuh

yi              i       yi      yii     yih
ya              ia      ya      yea     yah
ye              ie      ye      yee     yeh
yai             iai     yai     -       -
yao             iau     yau     yeau    yaw
you             iou     you     yeou    yow
yan             ian     yan     yean    yann
yin             in      yn      yiin    yinn
yang            iang    yang    yeang   yanq
ying            ing     yng     yiing   yinq
yong            iong    yong    yeong   yonq

wu              u       wu      wuu     wuh
wa              ua      wa      woa     wah
wo              uo      wo      woo     woh
wai             uai     wai     woai    way
wei             uei     wei     woei    wey
wan             uan     wan     woan    wann
wen             uen     wen     woen    wenn
wang            uang    wang    woang   wanq
weng            ueng    -       woeng   wenq

yu              iu      yu      yeu     yuh
yue             iue     yue     yeue    yueh
yuan            iuan    yuan    yeuan   yuann
yun             iun     yun     yeun    yunn

er              el      erl     eel     ell

yir             iel     yel     yeel    yell
yar             ial     yal     yeal    yall
yer             ie'l    ye'l    yeel    yell
yair            -       yal     -       -
yaor            iaul    yaul    yeaul   yawl
your            ioul    youl    yeoul   yowl
yanr            ial     yal     yeal    yall
yinr            iel     yel     yeel    yell
yangr           iangl   yangl   yeangl  yanql
yingr           iengl   yengl   yeengl  yenql
yongr           iongl   yongl   yeongl  yonql

wur             ul      wul     wuul    wull
war             ual     wal     woal    wall
wor             uol     wol     wool    woll
wair            ual     wal     woal    wall
weir            uel     wel     woel    well
wanr            ual     wal     woal    wall
wenr            uel     wel     woel    well
wangr           uangl   wangl   woangl  wanql
wengr           uengl   -       woengl  wenql

yur             iuel    yuel    yeuel   yuell
yuer            iue'l   yue'l   -       yuell
yuanr           iual    yual    yeual   yuall
yunr            iuel    yuel    yeuel   yuell
"""

    # final mapping without line 'r'
    FINAL_MAPPING = """
a               a       ar      aa      ah              ha      a
o               o       or      oo      oh              ho      o
e               e       er      ee      eh              he      e
ai              ai      air     ae      ay              hai     ai
ei              ei      eir     eei     ey              hei     ei
ao              au      aur     ao      aw              hau     au
ou              ou      our     oou     ow              hou     ou
an              an      arn     aan     ann             han     an
en              en      ern     een     enn             hen     en
ang             ang     arng    aang    anq             hang    ang
eng             eng     erng    eeng    enq             heng    eng
ong             ong     orng    oong    onq             hong    ong

i               i       yi      ii      ih              hi      i
ia              ia      ya      ea      iah             hia     ia
ie              ie      ye      iee     ieh             hie     ie
iai             iai     yai     -       -               hiai    iai
iao             iau     yau     eau     iaw             hiau    iau
iu              iou     you     eou     iow             hiou    iou
ian             ian     yan     ean     iann            hian    ian
in              in      yn      iin     inn             hin     in
iang            iang    yang    eang    ianq            hiang   iang
ing             ing     yng     iing    inq             hing    ing
iong            iong    yong    eong    ionq            hiong   iong

u               u       wu      uu      uh              hu      u
ua              ua      wa      oa      uah             hua     ua
uo              uo      wo      uoo     uoh             huo     uo
uai             uai     wai     oai     uay             huai    uai
ui              uei     wei     oei     uey             huei    uei
uan             uan     wan     oan     uann            huan    uan
un              uen     wen     oen     uenn            huen    uen
uang            uang    wang    oang    uanq            huang   uang

u:              iu      yu      eu      iuh             hiu     iu
u:e             iue     yue     eue     iueh            hiue    iue
u:an            iuan    yuan    euan    iuann           hiuan   iuan
u:n             iun     yun     eun     iunn            hiun    iun

ar              al      arl     aal     all             hal     al
or              ol      orl     ool     oll             hol     ol
er              e'l     er'l    ee'l    ehl             he'l    e'l
air             al      arl     aal     all             hal     al
eir             el      erl     eel     ell             hel     el
aor             aul     aurl    aol     awl             haul    aul
our             oul     ourl    ooul    owl             houl    oul
anr             al      arl     aal     all             hal     al
enr             el      erl     eel     ell             hel     el
angr            angl    arngl   aangl   anql            hangl   angl
engr            engl    erngl   eengl   enql            hengl   engl
ongr            ongl    orngl   oongl   onql            hongl   ongl

ir              iel     yel     ieel    iell            hiel    iel
iar             ial     yal     eal     iall            hial    ial
ier             ie'l    ye'l    ieel    iell            hie'l   ie'l
iair            -       yal     -        -              -       -
iaor            iaul    yaul    eaul    iawl            hiaul   iaul
iur             ioul    youl    eoul    iowl            hioul   ioul
ianr            ial     yal     eal     iall            hial    ial
inr             iel     yel     ieel    iell            hiel    iel
iangr           iangl   yangl   eangl   ianql           hiangl  iangl
ingr            iengl   yengl   ieengl  ienql           hiengl  iengl
iongr           iongl   yongl   eongl   ionql           hiongl   iongl

ur              ul      wul     uul     ull             hul     ul
uar             ual     wal     oal     uall            hual    ual
uor             uol     wol     uool    uoll            huol    uol
uair            ual     wal     oal     uall            hual    ual
uir             uel     wel     oel     uell            huel    uel
uanr            ual     wal     oal     uall            hual    ual
unr             uel     wel     oel     uell            huel    uel
uangr           uangl   wangl   oangl   uanql           huangl  uangl
uengr           uengl   -       -       -               huengl  uengl

u:r             iuel    yuel    euel    iuell           hiuel   iuel
u:er            iue'l   yue'l   euel    iuell           hiue'l  iue'l
u:anr           iual    yual    eual    iuall           hiual   iual
u:nr            iuel    yuel    euel    iuell           hiuel   iuel
"""

    PINYIN_FINAL_MAPPING = {'iu': 'iou', 'ui': 'uei', 'un': 'uen', 'u:': 'ü',
        'u:e': 'üe', 'u:an': 'üan', 'u:n': 'ün', 'iur': 'iour',
        'uir': 'ueir', 'unr': 'uenr', 'u:r': 'ür', 'u:er': 'üer',
        'u:anr': 'üanr', 'u:nr': 'ünr'}

    INITIAL_REGEX = re.compile('^(tz|ts|ch|sh|[bpmfdtnlsjrgkh])?')

    INITIAL_MAPPING = {'b': 'b', 'p': 'p', 'f': 'f', 'd': 'd', 't': 't',
        'g': 'g', 'k': 'k', 'h': 'h', 'j': 'j', 'q': 'ch', 'x': 'sh', 'zh': 'j',
        'ch': 'ch', 'sh': 'sh', 'z': 'tz', 'c': 'ts', 's': 's', 'm': 'm',
        'n': 'n', 'l': 'l', 'r': 'r'}
    """Mapping of Pinyin intials to GR ones."""

    def setUp(self):
        super(GROperatorReferenceTest, self).setUp()

        self.converter = self.f.createReadingConverter('Pinyin',
            'GR', sourceOptions={'erhua': 'oneSyllable'},
            targetOptions={'grRhotacisedFinalApostrophe': "'"})
        self.pinyinOperator = self.f.createReadingOperator('Pinyin',
            erhua='oneSyllable')
        self.grOperator = self.f.createReadingOperator('GR',
            grRhotacisedFinalApostrophe="'")

        # read in plain text mappings
        self.grJunctionSpecialMapping = {}
        for line in self.SPECIAL_MAPPING.split("\n"):
            if line.strip() == "":
                continue
            matchObj = re.match(r"((?:\w|:)+)\s+((?:\w|')+|-)\s+" \
                + r"((?:\w|')+|-)\s+((?:\w|')+|-)\s+((?:\w|')+|-)", line)
            assert(matchObj is not None)
            pinyinSyllable, gr1, gr2, gr3, gr4 = matchObj.groups()

            self.grJunctionSpecialMapping[pinyinSyllable] = {1: gr1, 2: gr2,
                3: gr3, 4: gr4}

        self.grJunctionFinalMapping = {}
        self.grJunctionFinalMNLRMapping = {}
        for line in self.FINAL_MAPPING.split("\n"):
            matchObj = re.match(r"((?:\w|\:)+)\s+((?:\w|')+|-)\s+" \
                + r"((?:\w|')+|-)\s+((?:\w|')+|-)\s+((?:\w|')+|-)" \
                + r"\s+((?:\w|')+|-)\s+((?:\w|')+|-)", line)
            if not matchObj:
                continue

            pinyinFinal, gr1, gr2, gr3, gr4, gr1_m, gr2_m = matchObj.groups()

            if pinyinFinal in self.PINYIN_FINAL_MAPPING:
                pinyinFinal = self.PINYIN_FINAL_MAPPING[pinyinFinal]

            self.grJunctionFinalMapping[pinyinFinal] = {1: gr1, 2: gr2, 3: gr3,
                4: gr4}
            self.grJunctionFinalMNLRMapping[pinyinFinal] = {1: gr1_m, 2: gr2_m}

    def testGRJunctionTable(self):
        """Test if all GR syllables have a reference given."""
        grEntities = set(self.grOperator.getFullReadingEntities())
        # no neutral tone syllables
        for entity in grEntities.copy():
            if entity[0] in ['.', self.grOperator.optionalNeutralToneMarker]:
                grEntities.remove(entity)

        # remove syllables with entry '-' in GR Junction table
        grEntities = grEntities - set(['yeai', 'yay', 'weng'])

        pinyinEntities = self.pinyinOperator.getPlainReadingEntities()
        for pinyinPlainSyllable in pinyinEntities:
            pinyinInitial, pinyinFinal \
                = self.pinyinOperator.getOnsetRhyme(pinyinPlainSyllable)

            if pinyinPlainSyllable in ['zhi', 'chi', 'shi', 'zi', 'ci',
                'si', 'ri', 'ju', 'qu', 'xu', 'er'] \
                or (pinyinPlainSyllable[0] in ['y', 'w']) \
                and pinyinPlainSyllable in self.grJunctionSpecialMapping:

                for tone in [1, 2, 3, 4]:
                    target = self.grJunctionSpecialMapping[pinyinPlainSyllable]\
                        [tone]
                    if target == '-':
                        continue

                    pinyinSyllable = self.pinyinOperator.getTonalEntity(
                        pinyinPlainSyllable, tone)

                    syllable = self.converter.convert(pinyinSyllable)

                    self.assertEqual(syllable, target,
                        "Wrong conversion to GR %s for Pinyin syllable %s: %s" \
                            % (repr(target), repr(pinyinSyllable),
                                repr(syllable)))

                    # mark as seen
                    grEntities.discard(target)

            elif pinyinInitial in ['m', 'n', 'l', 'r'] \
                and pinyinFinal[0] != 'ʅ' \
                and pinyinFinal in self.grJunctionFinalMNLRMapping \
                and pinyinFinal in self.grJunctionFinalMapping:

                for tone in [1, 2]:
                    target = self.grJunctionFinalMNLRMapping[pinyinFinal][tone]
                    if target == '-':
                        continue

                    pinyinSyllable = self.pinyinOperator.getTonalEntity(
                        pinyinPlainSyllable, tone)
                    syllable = self.converter.convert(pinyinSyllable)

                    tonalFinal = self.INITIAL_REGEX.sub('', syllable)

                    self.assertEqual(tonalFinal, target,
                        "Wrong conversion to GR %s for Pinyin syllable %s: %s" \
                            % (repr(target), repr(pinyinSyllable),
                                repr(syllable)))

                    # mark as seen
                    fullTarget = pinyinInitial + target
                    grEntities.discard(fullTarget)

                for tone in [3, 4]:
                    target = self.grJunctionFinalMapping[pinyinFinal][tone]
                    if target == '-':
                        continue

                    pinyinSyllable = self.pinyinOperator.getTonalEntity(
                        pinyinPlainSyllable, tone)
                    syllable = self.converter.convert(pinyinSyllable)

                    tonalFinal = self.INITIAL_REGEX.sub('', syllable)

                    self.assertEqual(tonalFinal, target,
                        "Wrong conversion to GR %s for Pinyin syllable %s: %s" \
                            % (repr(target), repr(pinyinSyllable),
                                repr(syllable)))

                    # mark as seen
                    if pinyinInitial:
                        initialTarget = self.INITIAL_MAPPING[pinyinInitial]
                    else:
                        initialTarget = ''
                    grEntities.discard(initialTarget + target)

            #elif pinyinInitial not in ['z', 'c', 's', 'zh', 'ch', 'sh', ''] \
                #and pinyinFinal not in ['m', 'ng', 'mr', 'ngr', u'ʅ', u'ʅr']:
            elif pinyinFinal not in ['m', 'n', 'ng', 'mr', 'nr', 'ngr', 'ʅ',
                'ʅr', 'ɿr', 'ê', 'êr'] \
                and pinyinFinal in self.grJunctionFinalMapping:

                for tone in [1, 2, 3, 4]:
                    target = self.grJunctionFinalMapping[pinyinFinal][tone]
                    if target == '-':
                        continue

                    pinyinSyllable = self.pinyinOperator.getTonalEntity(
                        pinyinPlainSyllable, tone)
                    syllable = self.converter.convert(pinyinSyllable)

                    tonalFinal = self.INITIAL_REGEX.sub('', syllable)

                    self.assertEqual(tonalFinal, target,
                        "Wrong conversion to GR %s for Pinyin syllable %s: %s" \
                            % (repr(target), repr(pinyinSyllable),
                                repr(syllable)))

                    # mark as seen
                    if pinyinInitial:
                        initialTarget = self.INITIAL_MAPPING[pinyinInitial]
                    else:
                        initialTarget = ''
                    grEntities.discard(initialTarget + target)

        self.assertTrue(len(grEntities) == 0,
            'Not all GR entities have test cases: %s' % repr(grEntities))


class MandarinBrailleOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'MandarinBraille'

    DIALECTS = crossDict(
        [{}, {'toneMarkType': 'none'}, {'missingToneMark': 'fifth'}],
        )


# TODO
#class MandarinBrailleReferenceTest(ReadingOperatorReferenceTest,
    #unittest.TestCase):
    #READING_NAME = 'MandarinBraille'

    #DECOMPOSITION_REFERENCES = []

    #COMPOSITION_REFERENCES = []

    #READING_ENTITY_REFERENCES = []


class MandarinIPAOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'MandarinIPA'

    DIALECTS = crossDict(
        [{}, {'toneMarkType': 'numbers'}, {'toneMarkType': 'chaoDigits'},
            {'toneMarkType': 'numbers', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'chaoDigits', 'missingToneMark': 'ignore'},
            #{'toneMarkType': 'diacritics'}, # TODO NotImplementedError
            #{'toneMarkType': 'diacritics', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'none'}],
        )

    @staticmethod
    def testUpperCase(dialect):
        return False

    def cleanDecomposition(self, decomposition, reading, **options):
        return [entity for entity in decomposition if entity != '.']


# TODO
#class MandarinIPAReferenceTest(ReadingOperatorReferenceTest,
    #unittest.TestCase):
    #READING_NAME = 'MandarinIPA'

    #DECOMPOSITION_REFERENCES = []

    #COMPOSITION_REFERENCES = []

    #READING_ENTITY_REFERENCES = []


class ShanghaineseIPAOperatorConsistencyTest(ReadingOperatorConsistencyTest,
    unittest.TestCase):
    READING_NAME = 'ShanghaineseIPA'

    DIALECTS = crossDict(
        [{}, #{'toneMarkType': 'numbers'},
            {'toneMarkType': 'chaoDigits'},
            {'toneMarkType': 'superscriptChaoDigits'},
            #{'toneMarkType': 'numbers', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'chaoDigits', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'superscriptChaoDigits',
                'missingToneMark': 'ignore'},
            #{'toneMarkType': 'diacritics'}, # TODO NotImplementedError
            #{'toneMarkType': 'diacritics', 'missingToneMark': 'ignore'},
            {'toneMarkType': 'none'}],
        )

    @staticmethod
    def testUpperCase(dialect):
        return False

    def cleanDecomposition(self, decomposition, reading, **options):
        return [entity for entity in decomposition if entity != '.']


class ShanghaineseIPAReferenceTest(ReadingOperatorReferenceTest,
    unittest.TestCase):
    READING_NAME = 'ShanghaineseIPA'

    DECOMPOSITION_REFERENCES = [
        ({'toneMarkType': 'superscriptChaoDigits'}, [
            ('ɦi⁵³ ɦɑ̃⁵³.ʦɤ lɛ⁵³ gəˀ¹²', ['ɦi⁵³', ' ', 'ɦɑ̃⁵³', '.', 'ʦɤ',
                ' ', 'lɛ⁵³', ' ', 'gəˀ¹²']),
            ]),
        ]

    COMPOSITION_REFERENCES = [
        ({'toneMarkType': 'superscriptChaoDigits'}, [
            (['ɦi⁵³', ' ', 'ɦɑ̃⁵³', 'ʦɤ', ' ', 'lɛ⁵³', ' ', 'gəˀ¹²'],
                'ɦi⁵³ ɦɑ̃⁵³.ʦɤ lɛ⁵³ gəˀ¹²'),
            ]),
        ]

    READING_ENTITY_REFERENCES = [
        ({'toneMarkType': 'chaoDigits'}, [
            ("tʰi53", True),
            ("tʰi34", True),
            ("di23", True),
            ("tʰiɪˀ55", True),
            ("diɪˀ12", True),
            ("noŋ53", True),
            ("diɪˀ1", False),
            ("diɪˀ23", True),
            ("diɪˀ55", True), # YinRu
            ]),
        ({'toneMarkType': 'superscriptChaoDigits'}, [
            ("tʰi⁵³", True),
            ("tʰi³⁴", True),
            ("di²³", True),
            ("tʰiɪˀ⁵⁵", True),
            ("diɪˀ¹²", True),
            ("noŋ⁵³", True),
            ("diɪˀ¹", False),
            ]),
        ({'toneMarkType': 'ipaToneBar'}, [
            ("tʰi˥˧", True),
            ("tʰi˧˦", True),
            ("di˨˧", True),
            ("tʰiɪˀ˥˥", True),
            ("diɪˀ˩˨", True),
            ("noŋ˥˧", True),
            ("tʰi˥", False),
            ]),
        ({'toneMarkType': 'chaoDigits', 'constrainEntering': True}, [
            ("tʰi53", True),
            ("tʰi34", True),
            ("di23", True),
            ("tʰiɪˀ55", True),
            ("diɪˀ12", True),
            ("noŋ53", True),
            ("diɪˀ1", False),
            ("diɪˀ23", False), # YangQu
            ("diɪˀ55", True),  # YinRu
            ("di55", False),   # YinRu
            ]),
        ({'toneMarkType': 'chaoDigits', 'constrainToneCategories': True}, [
            ("tʰi53", True),
            ("tʰi34", True),
            ("di23", True),
            ("tʰiɪˀ55", True),
            ("diɪˀ12", True),
            ("noŋ53", False),  # Voiced + YinPing
            ("diɪˀ1", False),
            ("diɪˀ23", True),  # Voiced + YangQu
            ("diɪˀ55", False), # Voiced + YinRu
            ("di55", False),   # Voiced + YinRu
            ]),
        ({'toneMarkType': 'chaoDigits', 'constrainEntering': True,
            'constrainToneCategories': True}, [
            ("tʰi53", True),
            ("tʰi34", True),
            ("di23", True),
            ("tʰiɪˀ55", True),
            ("diɪˀ12", True),
            ("noŋ53", False),  # Voiced + YinPing
            ("diɪˀ1", False),
            ("diɪˀ23", False), # Voiced + YangQu
            ("diɪˀ55", False), # Voiced + YinRu
            ("di55", False),   # Voiced + YinRu
            ]),
    ]

    GUESS_DIALECT_REFERENCES = [
        ("zã˥˧", {'toneMarkType': 'ipaToneBar'}),
        ("zã53", {'toneMarkType': 'chaoDigits'}),
        ("ɦɑ⁵³.ʦɤ", {'toneMarkType': 'superscriptChaoDigits'}),
        ]
