#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Provides a class to create a syllable table with initial and final sounds of a
romanisation drawn on the axis.

Example
=======

Generate a table for Pinyin following the ISO 7098 Annex A table::
    >>> import syllabletable
    >>> gen = syllabletable.SyllableTableBuilder()
    >>> table, notIncluded = gen.build('ISO 7098')

Write an HTML table:
    >>> import codecs
    >>> def s(c): return c if c else ''
    ... 
    >>> table, notIncluded = gen.buildWithHead('ISO 7098')
    >>> f = codecs.open('/tmp/table.html', 'w', 'utf8')
    >>> print >> f, "<html><body><table>"
    >>> print >> f, "\n".join(("<tr>%s</tr>" % ''.join(
    ...     ('<td>%s</td>' % s(c)) for c in row)) for row in table)
    >>> print >> f, "</table>"
    >>> print >> f, "Not included are %s" % ", ".join(notIncluded.keys())
    >>> print >> f, "</body></html>"
    >>> f.close()

2008 Christoph Burgmer (cburgmer@ira.uka.de)

License: MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

@todo Impl: Generalise for readings without tones.
"""

from cjklib import reading

class InitialFinalIterator:
    """Base class for placement rules."""
    def __init__(self, initialFinalIterator):
        self.initialFinalIterator = initialFinalIterator

class PinyinYeIterator(InitialFinalIterator):
    """
    Converts Pinyin syllable I{ye} to I{yê} (points out pronunciation [ɛ]).
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final == 'e' and initial == 'y':
                yield('y', 'ê', syllable)
            else:
                yield(initial, final, syllable)

class PinyinRemoveSpecialEIterator(InitialFinalIterator):
    """
    Removes special syllable I{ê}. This is useful when it collides with I{e} in
    the case where it points out exceptional pronunciation [ɛ].
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final == 'ê' and initial == '':
                yield('', '', syllable)
            else:
                yield(initial, final, syllable)

class PinyinEVowelIterator(InitialFinalIterator):
    """
    Adds a second form I{ê} for I{e} (points out exceptional pronunciation [ɛ]).
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final == 'e' and initial == '':
                yield('', 'e', syllable)
                yield('', 'ê', syllable)
            else:
                yield(initial, final, syllable)

class PinyinIExtendedVowelIterator(InitialFinalIterator):
    """
    Converts Pinyin finals for I{'zi'}, I{'ci'}, I{'si'}, I{'zhi'}, I{'chi'},
    I{'shi'} and I{ri} to I{ɿ} and I{ʅ} to separate them from finals
    pronounced equal to I{yi}.
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final == 'i' and initial in ['z', 'c', 's']:
                yield(initial, 'ɿ', syllable)
            elif final == 'i' and initial in ['zh', 'ch', 'sh', 'r']:
                yield(initial, 'ʅ', syllable)
            else:
                yield(initial, final, syllable)

class PinyinIVowelIterator(InitialFinalIterator):
    """
    Converts Pinyin finals for I{'zi'}, I{'ci'}, I{'si'}, I{'zhi'}, I{'chi'},
    I{'shi'} and I{ri} to I{-i} to separate them from finals pronounced equal to
    I{yi}.
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final == 'i' and initial in ['z', 'c', 's', 'zh', 'ch',
                'sh', 'r']:
                yield(initial, '-i', syllable)
            else:
                yield(initial, final, syllable)

class PinyinVVowelIterator(InitialFinalIterator):
    """
    Converts Pinyin finals which coda includes the I{ü} (IPA [y]) vowel but is
    written I{u} to a representation with I{ü}.
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final in ['u', 'ue', 'uan', 'un'] \
                and initial in  ['y', 'j', 'q', 'x']:
                final = 'ü' + final[1:]
                yield(initial, final, syllable)
            else:
                yield(initial, final, syllable)

class PinyinOEFinalIterator(InitialFinalIterator):
    """
    Merges finals I{o} and I{e} together to final I{o/e}, omitting zero initial
    I{o} and all other syllables with final I{o} with initial not in I{b}, I{p},
    I{m}, I{f}. In return syllables with initials I{b}, I{p}, I{m}, I{f} and
    final I{e} remain unchanged.
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if (final == 'o' and initial in ['b', 'p', 'm', 'f']) \
                or (final == 'e' and initial not in ['b', 'p', 'm', 'f']):
                yield(initial, 'o/e', syllable)
            else:
                yield(initial, final, syllable)

class PinyinUnpronouncedInitialsIterator(InitialFinalIterator):
    """
    Converts Pinyin forms with initials I{y} and I{w} to initial-less forms.
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if initial in ['y', 'w'] and (final[0] in ['i', 'u', 'ü']):
                yield('', final, syllable)
            elif initial == 'y' and final == 'ou':
                yield('', 'iu', syllable)
            elif initial == 'w' and final == 'en':
                yield('', 'un', syllable)
            elif initial == 'w' and final == 'ei':
                yield('', 'ui', syllable)
            elif initial == 'y':
                yield('', 'i' + final, syllable)
            elif initial == 'w':
                yield('', 'u' + final, syllable)
            else:
                yield(initial, final, syllable)

class RemoveSyllabicDiacriticIterator(InitialFinalIterator):
    """
    Removes a syllabic indicator in form of the combining diacritic U+0329.
    """
    def __iter__(self):
        for initial, final, syllable in self.initialFinalIterator:
            if final == '':
                yield(initial.replace('\u0329', ''), final, syllable)
            else:
                yield(initial, final, syllable)

class SyllableTableBuilder:
    """
    Builds a table of syllables with initials and finals on the axis.
    """
    INITIAL_MAPPING = {'Pinyin': ['b', 'p', 'm', 'f', 'd', 't', 'n',
            'l', 'z', 'c', 's', 'zh', 'ch', 'sh', 'r', 'j', 'q', 'x',
            'g', 'k', 'h', 'w', 'y', ''],
        'Jyutping': ['', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g',
            'k', 'ng', 'h', 'gw', 'kw', 'w', 'z', 'c', 's', 'j'],
        'ShanghaineseIPA': ['ŋ', 'b', 'd', 'ɲ', 'ɕ', 'ʥ', 'ʑ', 'ɦ',
            'ʦ', 'ʦʰ', 'ʨʰ', 'ʨ', 'f', 'g', 'h', 'k', 'kʰ', 'l',
            'm', 'm\u0329', 'n', 'p', 'pʰ', 's', 't', 'tʰ', 'v', 'z',
            '']}
    FINAL_MAPPING = {'Pinyin': ['a', 'ao', 'ai', 'an', 'ang', 'o', 'ou',
            'ong', 'u', 'ü', 'ua', 'uai', 'uan', 'uang', 'ue', 'üe',
            'un', 'uo', 'ui', 'e', 'er', 'ei', 'en', 'eng', 'i', 'ia',
            'iao', 'iu', 'ie', 'ian', 'in', 'iang', 'ing', 'iong', 'n',
            'ng', 'm', 'ê'],
        'Jyutping': ['i', 'ip', 'it', 'ik', 'im', 'in', 'ing', 'iu',
            'yu', 'yut', 'yun', 'u', 'up', 'ut', 'uk', 'um', 'un',
            'ung', 'ui', 'e', 'ep', 'et', 'ek', 'em', 'en', 'eng',
            'ei', 'eu', 'eot', 'eon', 'eoi', 'oe', 'oet', 'oek',
            'oeng', 'oei', 'o', 'ot', 'ok', 'om', 'on', 'ong', 'oi',
            'ou', 'ap', 'at', 'ak', 'am', 'an', 'ang', 'ai', 'au',
            'aa', 'aap', 'aat', 'aak', 'aam', 'aan', 'aang', 'aai',
            'aau', 'm', 'ng'],
        'ShanghaineseIPA': ['', 'a', 'ã', 'aˀ', 'ø', 'ɿ', 'ɤ', 'ɑ',
            'ɔ', 'ə', 'ɛ', 'əŋ', 'ɑˀ', 'ɔˀ', 'əˀ', 'ɑ̃', 'əl',
            'en', 'ən', 'i', 'ia', 'iɤ', 'iɑ', 'iɔ',
            'iɪˀ', 'iɑˀ', 'iɑ̃', 'in', 'ioŋ', 'ioˀ', 'o', 'oŋ',
            'oˀ', 'u', 'uɑ', 'uɛ', 'uən', 'uɑˀ', 'uəˀ',
            'uɑ̃', 'y', 'yø', 'yɪˀ', 'yəˀ', 'yn']}

    SCHEME_MAPPING = {'ISO 7098': ('Pinyin', ['', 'y', 'w', 'b', 'p', 'm',
            'f', 'd', 't', 'n', 'l', 'z', 'c', 's', 'zh', 'ch', 'sh',
            'r', 'j', 'q', 'x', 'g', 'k', 'h'],
            ['a', 'o', 'e' , 'ê', '-i', 'er', 'ai', 'ei', 'ao', 'ou',
            'an', 'en', 'ang', 'eng', 'ong', 'i', 'ia', 'iao', 'ie',
            'iu', 'ian', 'in', 'iang', 'ing', 'iong', 'u', 'ua', 'uo',
            'uai', 'ui', 'uan', 'un', 'uang', 'ü', 'üe', 'üan', 'ün'],
            [PinyinRemoveSpecialEIterator, PinyinYeIterator,
            PinyinEVowelIterator, PinyinIVowelIterator, PinyinVVowelIterator]),
        'Praktisches Chinesisch': ('Pinyin', ['', 'b', 'p', 'm', 'f', 'd',
            't', 'n', 'l', 'z', 'c', 's', 'zh', 'ch', 'sh', 'r', 'j',
            'q', 'x', 'g', 'k', 'h'],
            ['a', 'o', 'e' , 'ê', '-i', 'er', 'ai', 'ei', 'ao', 'ou',
            'an', 'en', 'ang', 'eng', 'ong', 'i', 'ia', 'iao', 'ie',
            'iu', 'ian', 'in', 'iang', 'ing', 'iong', 'u', 'ua', 'uo',
            'uai', 'ui', 'uan', 'un', 'uang', 'ueng', 'ü', 'üe', 'üan',
            'ün'],
            [PinyinRemoveSpecialEIterator, PinyinEVowelIterator,
            PinyinIVowelIterator, PinyinVVowelIterator,
            PinyinUnpronouncedInitialsIterator]),
        'Pinyin.info': ('Pinyin', ['b', 'p', 'm', 'f', 'd',
            't', 'n', 'l', 'g', 'k', 'h', 'z', 'c', 's', 'zh', 'ch',
            'sh', 'r', 'j', 'q', 'x', '', ],
            ['a', 'o', 'e', 'ai', 'ei', 'ao', 'ou', 'an', 'ang', 'en',
            'eng', 'ong', 'u', 'ua', 'uo', 'uai', 'ui', 'uan', 'uang',
            'un', 'ueng', 'i', 'ia', 'ie', 'iao', 'iu', 'ian', 'in',
            'ing', 'iang', 'iong', 'ü', 'üe', 'üan', 'ün'],
            [PinyinVVowelIterator, PinyinUnpronouncedInitialsIterator]),
        'Pinyin dewiki': ('Pinyin', ['b', 'p', 'm', 'f', 'd', 't', 'n',
            'l', 'z', 'c', 's', 'zh', 'ch', 'sh', 'r', 'j', 'q', 'x',
            'g', 'k', 'h', 'w', 'y', ''],
            ['a', 'ao', 'ai', 'an', 'ang', 'o', 'ou', 'ong', 'u', 'ü',
            'ua', 'uai', 'uan', 'uang', 'ue', 'üe', 'un', 'uo', 'ui',
            'e', 'er', 'ei', 'en', 'eng', 'i', 'ia', 'iao', 'iu',
            'ie', 'ian', 'in', 'iang', 'ing', 'iong'],
            []),
        'PinyinExtendedScheme': ('Pinyin', ['', 'b', 'p', 'm', 'f', 'd',
            't', 'n', 'l', 'z', 'c', 's', 'zh', 'ch', 'sh', 'r', 'j',
            'q', 'x', 'g', 'k', 'h'],
            ['a', 'o', 'e' , 'ê', 'ɿ', 'ʅ', 'er', 'ai', 'ei', 'ao',
            'ou', 'an', 'en', 'ang', 'eng', 'ong', 'i', 'ia', 'iao',
            'ie', 'iu', 'iai', 'ian', 'in', 'iang', 'ing', 'io',
            'iong', 'u', 'ua', 'uo', 'uai', 'ui', 'uan', 'un', 'uang',
            'ueng', 'ü', 'üe', 'üan', 'ün', 'm', 'n', 'ng'],
            [PinyinIExtendedVowelIterator, PinyinVVowelIterator,
            PinyinUnpronouncedInitialsIterator]),
        'Introduction1972': ('Pinyin', ['', 'b', 'p', 'm', 'f', 'z',
            'c', 's', 'd', 't', 'n', 'l', 'zh', 'ch', 'sh', 'r', 'j',
            'q', 'x', 'g', 'k', 'h'],
            ['a', 'ai', 'an', 'ang', 'ao', 'o/e' , 'ei', 'en', 'eng',
            'ou', 'er', 'ɿ', 'ʅ', 'i', 'ia', 'ian', 'iang', 'iao',
            'ie', 'in', 'ing', 'iu', 'u', 'ua', 'uai', 'uan', 'uang',
            'uo', 'ui', 'un', 'ong', 'ü', 'üan', 'üe', 'ün', 'iong'],
            [PinyinIExtendedVowelIterator, PinyinVVowelIterator,
            PinyinUnpronouncedInitialsIterator, PinyinOEFinalIterator]),
        'CUHK': ('Jyutping', ['', 'b', 'p', 'm', 'f', 'd', 't', 'n',
            'l', 'g', 'k', 'ng', 'h', 'gw', 'kw', 'w', 'z', 'c', 's',
            'j'],
            ['i', 'ip', 'it', 'ik', 'im', 'in', 'ing', 'iu', 'yu',
            'yut', 'yun', 'u', 'up', 'ut', 'uk', 'um', 'un', 'ung',
            'ui', 'e', 'ep', 'et', 'ek', 'em', 'en', 'eng', 'ei',
            'eu', 'eot', 'eon', 'eoi', 'oe', 'oet', 'oek', 'oeng', 'o',
            'ot', 'ok', 'on', 'ong', 'oi', 'ou', 'ap', 'at', 'ak',
            'am', 'an', 'ang', 'ai', 'au', 'aa', 'aap', 'aat', 'aak',
            'aam', 'aan', 'aang', 'aai', 'aau', 'm', 'ng'],
            []),
        'CUHK extended': ('Jyutping', ['', 'b', 'p', 'm', 'f', 'd', 't',
            'n', 'l', 'g', 'k', 'ng', 'h', 'gw', 'kw', 'w', 'z', 'c',
            's', 'j'],
            ['i', 'ip', 'it', 'ik', 'im', 'in', 'ing', 'iu', 'yu',
            'yut', 'yun', 'u', 'up', 'ut', 'uk', 'um', 'un', 'ung',
            'ui', 'e', 'ep', 'et', 'ek', 'em', 'en', 'eng', 'ei',
            'eu', 'eot', 'eon', 'eoi', 'oe', 'oet', 'oek', 'oeng',
            'oei', 'o', 'ot', 'ok', 'om', 'on', 'ong', 'oi', 'ou',
            'ap', 'at', 'ak', 'am', 'an', 'ang', 'ai', 'au', 'aa',
            'aap', 'aat', 'aak', 'aam', 'aan', 'aang', 'aai', 'aau',
            'm', 'ng'],
            []),
        'FullShanghainese': ('ShanghaineseIPA', ['',
            'ɦ', 'h',
            'ŋ', 'k', 'kʰ', 'g',
            'ɲ', 'ʨ', 'ʨʰ', 'ʥ', 'ɕ', 'ʑ',
            'm', 'b', 'p', 'pʰ',
            'l',
            'n', 't', 'tʰ', 'd', 'ʦ', 'ʦʰ', 's', 'z',
            'f', 'v'],
            ['', 'ɑ', 'ɑ̃', 'ã', 'ɑˀ',
            'ɛ', 'əˀ', 'ən', 'əl', 'ɿ', 'ɤ',
            'i', 'iɑ', 'iɑ̃', 'iɑˀ', 'iɤ', 'iɔ', 'iɪˀ', 'in',
            'ioˀ', 'ioŋ',
            'o', 'oˀ', 'oŋ', 'ø', 'ɔ', 'ɔˀ',
            'u', 'uɑ̃', 'uɑ', 'uɑˀ', 'uɛ', 'uəˀ', 'uən',
            'y', 'yn', 'yø', 'yɪˀ', 'yəˀ'],
            [RemoveSyllabicDiacriticIterator])}
    """
    Predefined schemes based on:
        - ISO 7098, the Pinyin syllable table given in Annex A.
        - Praktisches Chinesisch, Band I, Kommerzieller Verlag, Beijing 2001,
            ISBN 7-100-01675-4.
        - Pinyin.info, Mark Swofford: Combinations of initials and finals,
            Pinyin.info, U{http://www.pinyin.info/rules/initials_finals.html}.
        - Pinyin dewiki, table from Wikipedia article
            U{http://de.wikipedia.org/wiki/Pinyin}.
        - PinyinExtendedScheme, based on "Praktisches Chinesisch", extended to
            include all syllables, distinction between -i in zi and zhi.
        - Introduction1972, based on "An Introduction to the Pronunciation of
            Chinese". Francis D.M. Dow, Edinburgh, 1972, missing finals 'm',
            'n', 'ng', 'ê', 'iai', 'io', 'ueng'.
        - CUHK, Research Centre for Humanities Computing of the Research
            Institute for the Humanities (RIH), Faculty of Arts, The Chinese
            University of Hong Kong - 粵音節表 (Table of Cantonese Syllables):
            U{http://humanum.arts.cuhk.edu.hk/Lexis/Canton2/syllabary/}.
        - CUHK extended, same as CUHK except finals I{oei} and I{om} being
            added.
    """

    class SyllableIterator:
        """Defines a simple Iterator for a given syllable list."""
        def __init__(self, syllableList, initialSet, finalSet):
            self.syllableList = syllableList
            self.initialSet = initialSet
            self.finalSet = finalSet
            self.unresolvedSyllables = set()

        def __iter__(self):
            for syllable in self.syllableList:
                syllableResolved = False
                for i in range(0, len(syllable)+1):
                    initial = syllable[0:i]
                    final = syllable[i:]
                    if initial in self.initialSet and final in self.finalSet:
                        yield(initial, final, syllable)
                        syllableResolved = True
                if not syllableResolved:
                    self.unresolvedSyllables.add(syllable)

        def getUnresolvedSyllables(self):
            """
            Returns a set of unresolved syllables.

            During iteration some syllables might not be resolved, due to
            missing initial of final values. These syllables are returned by
            this method.
            """
            return self.unresolvedSyllables

    def __init__(self, databaseSettings={}, dbConnectInst=None):
        """
        Initialises the SyllableTableBuilder.

        If no parameters are given default values are assumed for the connection
        to the database. Other options can be either passed as dictionary to
        databaseSettings, or as an instantiated L{DatabaseConnector} given to
        dbConnectInst, the latter one will be preferred.

        @type databaseSettings: dictionary
        @param databaseSettings: database settings passed to the
            L{DatabaseConnector}, see there for feasible values
        @type dbConnectInst: object
        @param dbConnectInst: instance of a L{DatabaseConnector}
        """
        # get reading factory
        self.readingFactory = reading.ReadingFactory(databaseSettings,
            dbConnectInst)
        self.initialMapping = {}
        self.finalMapping = {}
        for romanisation in self.INITIAL_MAPPING:
            self.setInitials(romanisation, self.INITIAL_MAPPING[romanisation])
        for romanisation in self.FINAL_MAPPING:
            self.setFinals(romanisation, self.FINAL_MAPPING[romanisation])

    def setInitials(self, romanisation, initialList):
        """
        Adds a list of initials for the given romanisation used in
        decomposition.

        @type romanisation: string
        @param romanisation: name of romanisation according to L{cjklib} naming
        @type initialList: list of strings
        @param initialList: list of syllable initials
        """
        self.initialMapping[romanisation] = initialList

    def setFinals(self, romanisation, finalList):
        """
        Adds a list of finals for the given romanisation used in decomposition.

        @type romanisation: string
        @param romanisation: name of romanisation according to L{cjklib} naming
        @type finalList: list of strings
        @param finalList: list of syllable finals
        """
        self.finalMapping[romanisation] = finalList

    def addScheme(self, romanisation, schemeName, initialList, finalList,
        ruleList):
        """
        Adds a table scheme to the builder.

        @type romanisation: string
        @param romanisation: name of romanisation according to L{cjklib} naming
        @type schemeName: string
        @param schemeName: name of new Scheme
        @type initialList: list of strings
        @param initialList: list of syllable initials
        @type finalList: list of strings
        @param finalList: list of syllable finals
        @type ruleList: list of functions
        @param ruleList: rules to process the syllables from database
        """
        if schemeName in self.SCHEME_MAPPING:
            raise ValueError("Scheme '" + schemeName + "' already exists")
        self.SCHEME_MAPPING[schemeName] = (romanisation, initialList, finalList,
            ruleList)

    def removeScheme(self, schemeName):
        """
        Removes a table scheme from the builder.

        @type schemeName: string
        @param schemeName: name of new Scheme
        """
        del self.SCHEME_MAPPING[schemeName]

    def build(self, schemeName):
        """
        Builds a table for all available syllables where different initials are
        grouped per row and finals grouped by column.

        @type schemeName: string
        @param schemeName: name of new Scheme
        @rtype: tuple (list of list of strings, dict)
        @return: two-dimensional table with initials in rows and finals in
            columns and dict of syllables including initial/finals that couldn't
            be inserted into the table.
        """
        romanisation, initialList, finalList, ruleList = \
            self.SCHEME_MAPPING[schemeName]
        # get syllables
        op = self.readingFactory.createReadingOperator(romanisation)
        baseIterator = SyllableTableBuilder.SyllableIterator(\
            op.getPlainReadingEntities(),
            set(self.initialMapping[romanisation]),
            set(self.finalMapping[romanisation]))
        ifIterator = baseIterator
        # stack up rules
        for classObj in ruleList:
            ifIterator = classObj(ifIterator)
        # build table
        table = [[None for final in finalList] for initial in initialList]
        notIncludedSyllables = {}
        for initial, final, syllable in ifIterator:
            try:
                initialIdx = initialList.index(initial)
                finalIdx = finalList.index(final)
            except ValueError:
                notIncludedSyllables[syllable] = (initial, final)
                continue
            if table[initialIdx][finalIdx] \
                and table[initialIdx][finalIdx] != syllable:
                raise ValueError("several syllables at cell '" + initial \
                    + "', '" + final + "' (initial, final) with '" \
                    + table[initialIdx][finalIdx] + "' and '" \
                    + syllable + "'")
            table[initialIdx][finalIdx] = syllable
        # get unresolved syllables
        for syllable in baseIterator.getUnresolvedSyllables():
            notIncludedSyllables[syllable] = None
        return table, notIncludedSyllables

    def buildWithHead(self, schemeName):
        """
        Builds a table for all available syllables where different initials are
        grouped per row and finals grouped by column including table header.

        @type schemeName: string
        @param schemeName: name of new Scheme
        @rtype: tuple (list of list of strings, list of strings)
        @return: two-dimensional table with initials in rows and finals in
            columns and dict of syllables including initial/finals that couldn't
            be inserted into the table.
        """
        table, notIncludedSyllables = self.build(schemeName)
        romanisation, initialList, finalList, ruleList = \
            self.SCHEME_MAPPING[schemeName]
        # add finals to first row
        firstRow = ['']
        firstRow.extend(finalList)
        headTable = [firstRow]
        for i, initial in enumerate(initialList):
            nextRow = [initial]
            nextRow.extend(table[i])
            headTable.append(nextRow)
        return headTable, notIncludedSyllables

def transposeTable(table):
    """Transposes the given table."""
    tableT = []
    for idx in range(0, len(table[0])):
        newLine = []
        for line in table:
            newLine.append(line[idx])
        tableT.append(newLine)
    return tableT
