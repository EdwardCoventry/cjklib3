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
Creates a mapping between two readings based on a mapping of initial and final
parts.

2008 Christoph Burgmer (cburgmer@ira.uka.de)

Pinyin
======
It is important to deal with forms zi, ci, si / zhi, chi, shi, ri and forms with
a single e as de, te, e and others.

Source:
    - Hànyǔ Pǔtōnghuà Yǔyīn Biànzhèng (汉语普通话语音辨正). Page 15, Běijīng Yǔyán
        Dàxué Chūbǎnshè (北京语言大学出版社), 2003, ISBN 7-5619-0622-6.

Jyutping to Cantonese Yale
==========================
Sources:
    - Stephen Matthews, Virginia Yip: Cantonese: A Comprehensive Grammar.
        Routledge, 1994, ISBN 0-415-08945-X.
    - Parker Po-fei Huang, Gerard P. Kok: Speak Cantonese (Book I). Revised
        Edition, Yale University, 1999, ISBN 0-88710-094-5:

Entries were derived from the JyutpingSyllable using the mapping defined in
"Cantonese: A Comprehensive Grammar" where a final is mentioned in the source
'Speak Cantonese'.

The following finals found in some references for the LSHK's Jyutping are not
listed in the source 'Speak Cantonese':
    - -eu
    - -em
    - -en
    - -ep
    - -et

'Cantonese: A Comprehensive Grammar' though mentions finals -em, -up, -et,
-en, -um for Cantonese Yale (p. 20, chapter 1.3.1).

Jyutping to IPA
===============
Source:
    - Robert S. Bauer, Paul K. Benedikt: Modern Cantonese Phonology
        (摩登廣州話語音學). Walter de Gruyter, 1997, ISBN 3-11-014893-5.


Pinyin to GR
============
Source:
    - Yuen Ren Chao: A Grammar of Spoken Chinese. University of California
        Press, Berkeley, 1968, ISBN 0-520-00219-9.

@todo Lang: Support for Erhua.
"""

import sys
import locale
from cjklib.reading import ReadingFactory

# TABLE 1
INITIAL_RULES = {('Jyutping', 'CantoneseYale'): {'': '', 'b': 'b', 'p': 'p',
        'm': 'm', 'f': 'f', 'd': 'd', 't': 't', 'l': 'l', 'n': 'n', 'z': 'j',
        'c': 'ch', 's': 's', 'g': 'g', 'k': 'k', 'h': 'h', 'ng': 'ng',
        'gw': 'gw', 'kw': 'kw', 'j': 'y', 'w': 'w'},
    ('Pinyin', 'MandarinIPA'): {'': '', 'b': 'p', 'p': 'p‘', 'm': 'm',
        'f': 'f', 'd': 't', 't': 't‘', 'n': 'n', 'l': 'l',
        'z': 'ts', 'c': 'ts‘', 's': 's', 'zh': 'tʂ', 'ch': 'tʂ‘',
        'sh': 'ʂ', 'r': 'ʐ', 'j': 'tɕ', 'q': 'tɕ‘', 'x': 'ɕ',
        'g': 'k', 'k': 'k‘', 'h': 'x'},
    ('Jyutping', 'CantoneseIPA'): {'': '', 'b': 'p', 'p': 'pʰ', 'd': 't',
        't': 'tʰ', 'g': 'k', 'k': 'kʰ', 'gw': 'kʷ', 'kw': 'kʰʷ', 'm': 'm',
        'n': 'n', 'ng': 'ŋ', 'f': 'f', 's': 's', 'h': 'h', 'z': 'ts',
        'c': 'tsʰ', 'w': 'w', 'l': 'l', 'j': 'j'},
    ('Pinyin', 'GR'): {'': '', 'b': 'b', 'p': 'p', 'm': 'm', 'f': 'f', 'd': 'd',
        't': 't', 'n': 'n', 'l': 'l', 'g': 'g', 'k': 'k', 'h': 'h', 'j': 'j',
        'r': 'r', 's': 's', 'zh': 'j', 'q': 'ch', 'x': 'sh', 'z': 'tz',
        'c': 'ts', 'ch': 'ch', 'sh': 'sh'},
    ('Pinyin', 'WadeGiles'): {'': '', 'b': 'p', 'p': 'p’', 'm': 'm', 'f': 'f',
        'd': 't', 't': 't’', 'n': 'n', 'l': 'l', 'g': 'k', 'k': 'k’',
        'h': 'h', 'j': 'ch', 'q': 'ch’', 'x': 'hs', 'zh': 'ch', 'ch': 'ch’',
        'sh': 'sh', 'r': 'j', 'z': {'-ŭ': 'ts', 'ŭ': 'tz'},
        'c': {'-ŭ': 'ts’', 'ŭ': 'tz’'},
        's': {'-ŭ': 's', 'ŭ': 'ss'}},
    }
"""
Mapping of syllable initials.
For ambiguous pronunciations a non-injective mapping can be achieved by giving a
dictionary of possibilities, the key giving the name of the feature.
"""

# TABLE 1
FINAL_RULES = {('Jyutping', 'CantoneseYale'): {'aa': ('a', ''),
        'aai': ('aa', 'i'), 'aau': ('aa', 'u'), 'aam': ('aa', 'm'),
        'aan': ('aa', 'n'), 'aang': ('aa', 'ng'), 'aap': ('aa', 'p'),
        'aat': ('aa', 't'), 'aak': ('aa', 'k'), 'ai': ('a', 'i'),
        'au': ('a', 'u'), 'am': ('a', 'm'), 'an': ('a', 'n'),
        'ang': ('a', 'ng'), 'ap': ('a', 'p'), 'at': ('a', 't'),
        'ak': ('a', 'k'), 'e': ('e', ''), 'eng': ('e', 'ng'), 'ek': ('e', 'k'),
        'ei': ('e', 'i'), 'oe': ('eu', ''), 'oeng': ('eu', 'ng'),
        'oek': ('eu', 'k'), 'eoi': ('eu', 'i'), 'eon': ('eu', 'n'),
        'eot': ('eu', 't'), 'i': ('i', ''), 'iu': ('i', 'u'), 'im': ('i', 'm'),
        'in': ('i', 'n'), 'ip': ('i', 'p'), 'it': ('i', 't'),
        'ing': ('i', 'ng'), 'ik': ('i', 'k'), 'o': ('o', ''), 'oi': ('o', 'i'),
        'on': ('o', 'n'), 'ong': ('o', 'ng'), 'ot': ('o', 't'),
        'ok': ('o', 'k'), 'ou': ('o', 'u'), 'u': ('u', ''), 'ui': ('u', 'i'),
        'un': ('u', 'n'), 'ut': ('u', 't'), 'ung': ('u', 'ng'),
        'uk': ('u', 'k'), 'yu': ('yu', ''), 'yun': ('yu', 'n'),
        'yut': ('yu', 't'), 'm': ('', 'm'), 'ng': ('', 'ng')},
    ('Pinyin', 'MandarinIPA'): {'a': 'a', 'o': 'o',
        'e': {'Default': 'ɤ', '5thTone': 'ə'}, 'ê': 'ɛ', 'er': 'ər',
        'ai': 'ai', 'ei': 'ei', 'ao': 'au', 'ou': 'ou', 'an': 'an',
        'en': 'ən', 'ang': 'aŋ', 'eng': 'əŋ', 'ong': 'uŋ', 'i': 'i',
        'ia': 'ia', 'iao': 'iau', 'ie': 'iɛ', 'iou': 'iəu',
        'ian': 'iɛn', 'in': 'in', 'iang': 'iɑŋ', 'ing': 'iŋ',
        'iong': 'yŋ', 'u': 'u', 'ua': 'ua', 'uo': 'uo', 'uai': 'uai',
        'uei': 'uei', 'uan': 'uan', 'uen': 'uən', 'uang': 'uaŋ',
        'ueng': 'uəŋ', 'ü': 'y', 'üe': 'yɛ', 'üan': 'yan', 'ün': 'yn',
        'ɿ': 'ɿ', 'ʅ': 'ʅ'},
    ('Jyutping', 'CantoneseIPA'): {'i': 'iː', 'iu': 'iːw', 'im': 'iːm',
        'in': 'iːn', 'ip': 'iːp̚', 'it': 'iːt̚', 'yu': 'yː', 'yun': 'yːn',
        'yut': 'yːt̚', 'ei': 'ej', 'ing': 'eʲŋ', 'ik': 'eʲk̚', 'e': 'ɛː',
        'eu': 'ɛːw', 'em': 'ɛːm', 'en': 'ɛːn', 'eng': 'ɛːŋ', 'ep': 'ɛːp̚',
        'et': 'ɛːt̚', 'ek': 'ɛːk̚', 'oe': 'œː', 'oeng': 'œːŋ',
        'oek': 'œːk̚', 'eoi': 'ɵy', 'eon': 'ɵn', 'eot': 'ɵt̚', 'ai': 'ɐj',
        'au': 'ɐw', 'am': 'ɐm', 'an': 'ɐn', 'ang': 'ɐŋ', 'ap': 'ɐp̚',
        'at': 'ɐt̚', 'ak': 'ɐk̚', 'aa': 'aː', 'aai': 'aːj', 'aau': 'aːw',
        'aam': 'aːm', 'aan': 'aːn', 'aang': 'aːŋ', 'aap': 'aːp̚',
        'aat': 'aːt̚', 'aak': 'aːk̚', 'u': 'uː', 'ui': 'uːj', 'un': 'uːn',
        'ut': 'uːt̚', 'ou': 'ow', 'ung': 'oʷŋ', 'uk': 'oʷk̚', 'o': 'ɔː',
        'oi': 'ɔːj', 'on': 'ɔːn', 'ong': 'ɔːŋ', 'ot': 'ɔːt̚', 'ok': 'ɔːk̚',
        'm': 'm̩', 'ng': 'ŋ̩'},
    ('Pinyin', 'GR'): {'a': 'a', 'o': 'o', 'e': 'e', 'ai': 'ai',
        'ei': 'ei', 'ao': 'au', 'ou': 'ou', 'an': 'an', 'en': 'en',
        'ang': 'ang', 'eng': 'eng', 'ong': 'ong', 'er': 'el', 'i': 'i',
        'ia': 'ia', 'ie': 'ie', 'iai': 'iai', 'iao': 'iau', 'iou': 'iou',
        'ian': 'ian', 'in': 'in', 'iang': 'iang', 'ing': 'ing',
        'iong': 'iong', 'u': 'u', 'ua': 'ua', 'uo': 'uo', 'uai': 'uai',
        'uei': 'uei', 'uan': 'uan', 'uen': 'uen', 'uang': 'uang',
        'ü': 'iu', 'üe': 'iue', 'üan': 'iuan', 'ün': 'iun', 'ɿ': 'y',
        'ʅ': 'y', 'ueng': 'ueng'},
    ('Pinyin', 'WadeGiles'): {'a': 'a', 'ai': 'ai', 'an': 'an', 'ang': 'ang',
        'ao': 'ao', 'e': {'all_1': 'ê', 'k/k’/h': 'o'},
        'ê': {'all_1': 'ê', 'all_2': 'o'}, 'ei': 'ei',
        'en': 'ên', 'eng': 'êng', 'er': 'êrh', 'ʅ': 'ih', 'ɿ': 'ŭ',
        'i': 'i', 'ia': 'ia', 'ian': 'ien', 'iang': 'iang', 'iao': 'iao',
        'ie': 'ieh', 'in': 'in', 'ing': 'ing', 'iong': 'iung', 'iou': 'iu',
        'o': 'o', 'ong': 'ung', 'ou': 'ou', 'u': 'u', 'ua': 'ua', 'uai': 'uai',
        'uan': 'uan', 'uang': 'uang', 'uei': {'-k/k’/': 'ui', 'k/k’/': 'uei'},
        'uen': 'un', 'uo': {'k/k’/h/sh/': 'uo', '-k/k’/h/sh/': 'o'},
        'ü': 'ü', 'üan': 'üan', 'üe': 'üeh', 'ün': 'ün'},
    }
"""
Mapping of syllable finals.
For ambiguous pronunciations a non-injective mapping can be achieved by giving a
dictionary of possibilities, the key giving the name of the feature.

These finals included here don't necessarily represent the actual rendering, as
they might depend on the initial they combine with.
"""

# TABLE 1
EXTRA_SYLLABLES = {('Jyutping', 'CantoneseYale'): {'om': None, 'pet': None,
        'deu': None, 'lem': None, 'loet': None, 'loei': None, 'gep': None,
        'kep': None},
    ('Pinyin', 'MandarinIPA'): {'yai': None, 'yo': None, 'm': None,
        'n': None, 'ng': None, 'hm': None, 'hng': None},
    ('Jyutping', 'CantoneseIPA'): {'loet': None, 'loei': None, 'om': None,
        'zi': ('tʃ', 'iː'), 'ci': ('tʃʰ', 'iː'), 'zit': ('tʃ', 'iːt̚'),
        'cit': ('tʃʰ', 'iːt̚'), 'ziu': ('tʃ', 'iːw'),
        'ciu': ('tʃʰ', 'iːw'), 'zim': ('tʃ', 'iːm'),
        'cim': ('tʃʰ', 'iːm'), 'zin': ('tʃ', 'iːn'),
        'cin': ('tʃʰ', 'iːn'), 'zip': ('tʃ', 'iːp̚'),
        'cip': ('tʃʰ', 'iːp̚'), 'syu': ('ʃ', 'yː'), 'zyu': ('tʃ', 'yː'),
        'cyu': ('tʃʰ', 'yː'), 'syun': ('ʃ', 'yːn'), 'zyun': ('tʃ', 'yːn'),
        'cyun': ('tʃʰ', 'yːn'), 'syut': ('ʃ', 'yːt̚'),
        'zyut': ('tʃ', 'yːt̚'), 'cyut': ('tʃʰ', 'yːt̚'),
        'zoe': ('tʃ', 'œː'), 'zoek': ('tʃ', 'œːk̚'),
        'coek': ('tʃʰ', 'œːk̚'), 'zoeng': ('tʃ', 'œːŋ'),
        'coeng': ('tʃʰ', 'œːŋ'), 'zeoi': ('tʃ', 'ɵy'),
        'ceoi': ('tʃʰ', 'ɵy'), 'zeot': ('tʃ', 'ɵt̚'),
        'ceot': ('tʃʰ', 'ɵt̚'), 'zeon': ('tʃ', 'ɵn'),
        'ceon': ('tʃʰ', 'ɵn')},
    ('Pinyin', 'GR'): {'m': None, 'n': None, 'ng': None, 'hm': None,
        'hng': None, 'ê': None, 'yo': None},
    ('Pinyin', 'WadeGiles'): {'wen': ('', 'uên'), 'weng': ('', 'uêng'),
        'yi': ({'exceptSemiVowel': '', 'all_1': ''}, 'i'),
        'm': None, 'n': None, 'ng': None, 'hm': None, 'hng': None,
        'yai': None, 'yo': None},
    }
"""
Mapping for syllables with either no initial/final rules or with non standard
translation. Each entry consists of the syllable and a tuple of
initial and final if a mapping exists, else "None". For ambiguous pronunciations
a non-injective mapping can be achieved by giving a dictionary of possibilities,
the key giving the name of the feature.
"""

def getYaleSyllable(initial, final):
    nucleus, coda = final

    # syllable rule
    if initial == 'y' and nucleus.startswith('y'):
        # out of convenience Yale initial y and nucleus yu* are merged
        #   conventionally
        return nucleus + coda
    else:
        return initial + nucleus + coda

def makeYaleInitialNucleusCodaEntry(jyutpingSyllable, initial, final,
    initialFeature=None, finalFeature=None):
    yaleSyllable = getYaleSyllable(initial, final)
    nucleus, coda = final

    return "'" + yaleSyllable + "','" + initial + "','" + nucleus \
        + "','" + coda + "'"

def makeJyutpingYaleEntry(jyutpingSyllable, initial, final,
    initialFeature=None, finalFeature=None):
    yaleSyllable = getYaleSyllable(initial, final)

    return "'" + jyutpingSyllable + "','" + yaleSyllable + "'"

def getWadeGilesSyllable(initial, final):
    # syllable rule
    if not initial and final in ['i', 'in', 'ing']:
        return 'y' + final
    elif not initial and final.startswith('i') and final != 'i':
        return 'y' + final[1:]
    elif not initial and final == 'u':
        return 'w' + final
    elif not initial and final.startswith('u'):
        return 'w' + final[1:]
    elif not initial and final == 'ü':
        return 'y' + final
    elif not initial and final.startswith('ü'):
        return 'y' + final
    else:
        return initial + final

def checkFeature(syllablePart, feature):
    """
    Checks if the given initial or final fits to the given feature.

    E.g. if a final entry is given as {u'-k/k’/': 'ui', u'k/k’/': 'uei'},
    then the first feature is u'-k/k’/' which represents all finals except 'k',
    'k’' and '', so that e.g. checkFeature('d', u'-k/k’/') will return true and
    generate form 'dui'.
    """
    if feature:
        negative = False
        if feature.startswith('-'):
            feature = feature[1:]
            negative = True
        if feature.startswith('all_'):
            # all carry this
            return True
        mappings = feature.split('/')
        return (syllablePart in mappings and not negative) \
            or (syllablePart not in mappings and negative)
    return True

def makePinyinWadeGilesEntry(pinyinSyllable, initial, final,
    initialFeature=None, finalFeature=None):
    if initialFeature == 'exceptSemiVowel' and not initial:
        wadeGilesSyllable = final

        return "'" + pinyinSyllable + "','" + wadeGilesSyllable + "'"
    elif checkFeature(final, initialFeature) \
        and checkFeature(initial, finalFeature):
        # only generate entry if initial/final fits to features
        wadeGilesSyllable = getWadeGilesSyllable(initial, final)

        return "'" + pinyinSyllable + "','" + wadeGilesSyllable + "'"

def makeWadeGilesInitialFinalEntry(pinyinSyllable, initial, final,
    initialFeature=None, finalFeature=None):
    if initialFeature == 'exceptSemiVowel' and not initial:
        wadeGilesSyllable = final

        return "'" + wadeGilesSyllable + "','" + initial + "','" + final + "'"
    elif checkFeature(final, initialFeature) \
        and checkFeature(initial, finalFeature):
        # only generate entry if initial/final fits to features
        wadeGilesSyllable = getWadeGilesSyllable(initial, final)

        return "'" + wadeGilesSyllable + "','" + initial + "','" + final + "'"

def makeTargetInitialFinalEntry(sourceSyllable, initial, final,
    initialFeature=None, finalFeature=None):
    return "'" + initial + final + "','" + initial + "','" + final + "'"

def makeSourceTargetEntry(sourceSyllable, initial, final, initialFeature=None,
    finalFeature=None):
    targetSyllable = initial + final

    features = []
    if initialFeature:
        features.append(initialFeature)
    if finalFeature:
        features.append(finalFeature)

    if features:
        return "'" + sourceSyllable + "','" + targetSyllable + "','" \
            + ','.join(features) + "'"
    else:
        return "'" + sourceSyllable + "','" + targetSyllable + "',"

modi = {'YaleInitialFinal':('Jyutping', 'CantoneseYale',
        makeYaleInitialNucleusCodaEntry, {'toneMarkType': 'none'}),
    'JyutpingYaleMapping': ('Jyutping', 'CantoneseYale',
        makeJyutpingYaleEntry, {'toneMarkType': 'none'}),
    'MandarinIPAInitialFinal': ('Pinyin', 'MandarinIPA',
        makeTargetInitialFinalEntry, {'erhua': 'ignore',
            'toneMarkType': 'none'}),
    'PinyinIPAMapping': ('Pinyin', 'MandarinIPA', makeSourceTargetEntry,
        {'erhua': 'ignore', 'toneMarkType': 'none'}),
    'CantoneseIPAInitialFinal': ('Jyutping', 'CantoneseIPA',
        makeTargetInitialFinalEntry, {'toneMarkType': 'None'}),
    'JyutpingIPAMapping': ('Jyutping', 'CantoneseIPA', makeSourceTargetEntry,
        {'toneMarkType': 'none'}),
    'PinyinGRMapping': ('Pinyin', 'GR', makeSourceTargetEntry,
        {'erhua': 'ignore', 'toneMarkType': 'none'}),
    'PinyinWadeGilesMapping': ('Pinyin', 'WadeGiles', makePinyinWadeGilesEntry,
        {'erhua': 'ignore', 'toneMarkType': 'none'}),
    'WadeGilesInitialFinal': ('Pinyin', 'WadeGiles',
        makeWadeGilesInitialFinalEntry,
        {'erhua': 'ignore', 'toneMarkType': 'none'}),
    }

def main():
    language, output_encoding = locale.getdefaultlocale()

    if len(sys.argv) == 2:
        modus = sys.argv[1]
        if modus not in modi:
            print("invalid modus, choose one out of: " + ", ".join(list(modi.keys())))
            sys.exit(1)
    else:
        print("give a modus, choose one out of: " + ", ".join(list(modi.keys())))
        sys.exit(1)

    fromReading, toReading, entryFunc, readingOpt = modi[modus]

    initialRules = INITIAL_RULES[(fromReading, toReading)]
    finialRules = FINAL_RULES[(fromReading, toReading)]
    extraSyllables = EXTRA_SYLLABLES[(fromReading, toReading)]

    # entry set
    global entrySet
    entrySet = set()
    # build table and use scheme with almost perfect grouping according to
    #   pronunciation, then use headers to get the initial's and final's
    #   pronunciation.
    op = ReadingFactory().createReadingOperator(fromReading, **readingOpt)

    # get splitted syllables, finals in first row, initials in first column
    for syllable in op.getReadingEntities():
        initial, final = op.getOnsetRhyme(syllable)
        # only apply rules if syllable isn't given an extra mapping in
        #   EXTRA_SYLLABLES
        if not syllable in extraSyllables:
            # check if we have rules
            if initialRules[initial] != None and finialRules[final] != None:
                # check for ambiguous mappings
                if type(initialRules[initial]) == type({}):
                    initialFeatures = list(initialRules[initial].keys())
                else:
                    initialFeatures = [None]
                if type(finialRules[final]) == type({}):
                    finalFeatures = list(finialRules[final].keys())
                else:
                    finalFeatures = [None]

                # go through all mappings
                for initialFeature in initialFeatures:
                    for finalFeature in finalFeatures:
                        if initialFeature:
                            targetInitial \
                                = initialRules[initial][initialFeature]
                        else:
                            targetInitial = initialRules[initial]

                        if finalFeature:
                            targetFinal = finialRules[final][finalFeature]
                        else:
                            targetFinal = finialRules[final]

                        entry = entryFunc(syllable, targetInitial, targetFinal,
                            initialFeature, finalFeature)
                        if entry != None:
                            entrySet.add(entry)
            else:
                print(("missing rule(s) for syllable '" \
                    + syllable + "' with initial/final '" + initial + "'/'" \
                    + final + "'").encode(output_encoding), file=sys.stderr)

    # print extra syllables
    for syllable in extraSyllables:
        if extraSyllables[syllable]:
            initialRule, finalRule = extraSyllables[syllable]
            # check for ambiguous mappings
            if type(initialRule) == type({}):
                initialFeatures = list(initialRule.keys())
            else:
                initialFeatures = [None]
            if type(finalRule) == type({}):
                finalFeatures = list(finalRule.keys())
            else:
                finalFeatures = [None]

            # go through all mappings
            for initialFeature in initialFeatures:
                for finalFeature in finalFeatures:
                    if initialFeature:
                        targetInitial = initialRule[initialFeature]
                    else:
                        targetInitial = initialRule

                    if finalFeature:
                        targetFinal = finalRule[finalFeature]
                    else:
                        targetFinal = finalRule

                    entry = entryFunc(syllable, targetInitial, targetFinal,
                        initialFeature, finalFeature)
                    if entry != None:
                        entrySet.add(entry)

    notIncludedSyllables = [syllable for syllable in extraSyllables \
        if not extraSyllables[syllable]]
    if notIncludedSyllables:
        print(("Syllables not included in table: '" \
            + "', '".join(sorted(notIncludedSyllables)) + "'")\
            .encode(output_encoding), file=sys.stderr)

    entryList = list(entrySet)
    entryList.sort()
    print("\n".join(entryList).encode(output_encoding))

if __name__ == "__main__":
    main()
