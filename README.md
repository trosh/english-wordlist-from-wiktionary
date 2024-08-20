This script aims to build a wordlist to be used in a
[word game](https://woggle.mobi) I've been working on. After some time
searching through existing wordlists, I decided to take a slightly
different approach. My requirements are as follows:

* This list is a validation list for player moves, and I want the player
  to be rewarded for finding unusual words. As a result, the list should
  be very permissive.

* It should still, however, have a similar design to the Scrabble
  dictionary: no proper nouns, no composite words or phrases, no
  obsolete word, etc. Words must be representable by Scrabble tiles.

* The words can be any length, but I'd rather the very short words be
  generally acceptable as valid word-game words. That is, no scientific
  symbols or US state codes.

* It's hard to draw limits on word count or loan words in English, so
  I'm fine with pretty much every loan word, as long as it's not
  obsolete, slang, etc.

* I want words to have a Wiktionary definition so players can easily get
  some form of explanation.

So I decided to start from all of the English Wiktionary and then use
the mostly correct labels provided in the definitions to automatically
whittle it down to a word-game worthy list.

Getting the English Wiktionary
==============================

You can download the latest dumps from Wikimedia at
[the Wikimedia Downloads page](https://dumps.wikimedia.org/),
which has reasonable caps and should be treated respectfully.
Consider using a mirror.
The specific file containing all English Wiktionary articles can be
found under *enwiktionary* (for the latest completed dump date) with a
filename containing `pages-articles.xml`; it can then be decompressed
into a chonky XML:

    $ du -h enwiktionary-*.bz2
    1.3GB   enwiktionary-20240801-pages-articles.xml.bz2
    $ bunzip2 $!
    $ du -h enwiktionary-*.xml
    9.7GB   enwiktionary-20240801-pages-articles.xml

* The sizes are valid at the time of writing (August 2024).

* I did this project under Termux on an Android tablet, good thing
  *less(1)* and *grep(1)* don't load the whole file in memory!

filterxml.py
============

The Python script does two passes over this XML to find acceptable
words. This uses the default provided XML parser (`xml.parsers.expat`)
because I don't expect a billion laughs attack from Wikimedia.
(Maybe I should?)

Files are opened without `with` to facilitate interop with expat and
calling `tell()` from functions… and there's no error management
anyway.

* Page titles are checked to be decomposable into only latin letters
  and, optionally, primary
  [diacritics](https://en.wikipedia.org/wiki/Combining_Diacritical_Marks).
  This makes sense for my game which represents words with Boggle dice.
  The wordlist, however, keeps the original title in UTF-8.

* Once decomposed, and diacritics removed, page titles containing
  consecutive uppercase letters are removed. This efficiently removes
  a vast array of symbols and acronyms. Should I have tried to keep
  the word *OK*? An approach could be to build the wordlist without
  filtering words containing consecutive uppers, accepting *alternative
  case form of* variants, and then filtering on the result. But 
  *altcase* is a rat's nest in my opinion.

* I used the English Wiktionary's
  [list of *form-of* templates](https://en.wiktionary.org/wiki/Category:Form-of_templates)
  as a reference guide to remove definitions which include some such
  descriptions, and to select variants definitions. There are many
  templates, quite a few don't apply to any English words, not all
  aliases are in the summary table, and I had to grep through the XML
  manually numerous times to understand a bunch of them. Thank
  BurntSushi `{{honorific alternative case form of|en|burntsushi}}` for
  ripgrep!

* Definitions containing *lbl*s within a given set (such as *obsolete*
  or *short for*) are removed. There is no fixed list of these that I'm
  aware of. There's probably quite a few missing.

* Apart from some categories of colloquialisms such as *IRC* or *baby
  talk*, I've deliberately avoided removing most
  activity/location-specific categories.

* These labels are often more complex than a simple set of categories,
  and there realistically is no way to automatically deal with that
  complexity. (See the use of modifiers and other multi-parameter
  descriptions.)

* Some effort is made to take translingual definitions into account,
  though few apply.

* I haven't yet properly bothered getting philogenetic taxonomy terms.

* I haven't tried adapting this script to the French Wiktionary either.

english-wordlist.txt
====================

The resulting 6.0MB wordlist contains 544,269 words (381,727 1st pass
plus 162,542 2nd pass). It's somewhat excessively loaded with dubious
specific words and loan words, but each word is at least based on some
definition that passes some basic conformity. A *sort(1)*-ed version
is provided as well.

The word game then requires cross-referencing this wordlist with some
appropriately constructed frequency list for the hidden words.
