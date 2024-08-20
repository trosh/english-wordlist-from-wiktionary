#! /usr/bin/env python3
# vim: ts=8:sts=8:sw=8:noexpandtab

import xml.parsers.expat
import unicodedata
import re
import os

input_xml  = "enwiktionary-20240801-pages-articles.xml"
output_txt = "english-wordlist.txt"

curtitle = None
curlang = None
intitle = False
intext = False
numwords = 0
words = set()
infl_pass = False

diacritics = u"\u0300-\u036F" # primary Combining Diacritical Marks codepage
re_nonrepr   = re.compile(f"[^A-Za-z{diacritics}]") # search
re_acronym   = re.compile("[A-Z][A-Z]") # search
re_header    = re.compile("{{(en-|mul-|head\|en\||head\|mul\|)([^}|]+)") # match
re_def       = re.compile("(#+) ") # match
re_defcat    = re.compile("#+ {{lbl?\|[^}]*}}$") # match
re_inflof    = re.compile("#+ ({{lbl?\|[^}]*}})? ?({{[^}\|]*\|[^}]*}};? ?)+$") # match
re_infloftag = re.compile("{[^{}\|]* of\|") # findall
re_tag       = re.compile("{{[^}]*}}") # findall
re_subtag    = re.compile("[^|{}]+") # findall

keep_types = [
	"noun", "adj", "adjective", "verb",
	"adv", "adverb", "pron", "pronoun", "con", "det",
	"verb from", "comparative adjective", "noun form",
]

lb = ["label", "lb", "lbl"]
tlb = ["term-label", "tlb"]

keep_infls = [
	"adj form of",
	"agent noun of", "an of",
	"alternative plural of",
	"comparative of",
	"diminutive of", "dim of",
	"female equivalent of",
	"feminine of",
	"feminine singular of",
	"feminine singular past participle of",
	#"form of", if so, also check description…
	"former name of",
	"gerund of",
	"inflection of", "infl of",
	"literary form of",
	"masculine of",
	"masculine plural of",
	"noun form of",
	"participle of",
	"past participle of",
	"plural of",
	"rare spelling of",
	"singular of",
	"standard form of",
	"standard spelling of", "stand sp",
	"superlative of",
	"en-comparative of",
	"en-simple past of",
	"en-past of",
	"en-superlative of",
	"en-third-person singular of",
]

remove_infls = [
	"abbr of", "abbrev of", "abbreviation of",
	"acronym of",
	"alternative case form of", "alt case form of", "alt case form", "alt case of", "alt case", "altcase",
	"alternative form of", "alt form of", "alt form", "altform",
	"alternative spelling of", "alt sp of", "alt sp", "altsp",
	"aphetic form of",
	"apocopic form of", "apoc of",
	"archaic form of",
	"archaic inflection of",
	"archaic spelling of", "arc sp",
	"alternative typography of", "alt type",
	"clipping of", "clip of",
	"contraction of", "contr of",
	"dated form of", "dated form",
	"dated spelling of", "dated sp",
	"deliberate misspelling of",
	"eggcorn of",
	"ellipsis of",
	"elongated form of",
	"eye dialect of",
	"honorific alternative case form of", "honor alt case", "honour alt case",
	"informal form of", "informal", "if form",
	"informal spelling of",
	"initialism of", "init of",
	"misconstruction of",
	"misspelling of", "missp",
	"nonstandard form of", "nonstandard form", "nonst form", "ns form",
	"nonstandard spelling of", "nonstandard sp", "nonst sp", "ns sp",
	"obsolete form of", "obs form of", "obs form",
	"obsolete spelling of", "obs sp",
	"obsolete typography of", "obs typ",
	"pronunciation spelling of", "pron spelling of", "pron sp of", "pron sp",
	"rare form of", "rare form",
	"rare spelling of", "rare sp",
	"scribal abbreviation of", "scribal abbrev of", "scribal abbr of", "scrib abbrev of", "scrib abbr of", "scrib of",
	"short for",
	"syncopic form of",
	"uncommon form of", "uncommon form",
	"uncommon spelling of", "uncommon sp",
	"en-early modern spelling of",
]

remove_lbls = [
	"nonstandard", "proscribed", "bowdlerisation", "latn-def", "nonce", "archaic",
	"abbreviation", "abbreviation spelling", "acronym of",
	"stenoscript", "short for", "screenwriting",
	"internet", "computing", "leet", "trademark", "text messaging", "irc", "neologism",
	"childish", "baby talk", "child language", "infantile",
]

fin_bytes = os.path.getsize(input_xml)
fin  = open(input_xml, "rb")
fin_start = fin.tell()
fout = open(output_txt, "w")

def decomment(s):
	while True:
		start = s.find("<!--")
		if start == -1:
			return s
		end = s.find("-->", start+4)
		if end == -1:
			return s
		s = s[:start] + s[end+3:]
	return s

def start_element(name, attrs):
	if name == "title":
		global intitle
		intitle = True
	elif name == "text":
		global intext
		intext = True
		size = int(attrs["bytes"])
		if size > p.buffer_size:
			p.buffer_size = size

def end_element(name):
	global intitle, intext
	intitle = False
	intext = False

def char_data(data):
	global intitle, intext, curtitle, numwords, words, infl_pass, fin, fin_bytes
	if intitle:
		# Check all characters can be represented as ASCII
		decomposed = unicodedata.normalize("NFD", data)
		if re_nonrepr.search(decomposed) is None:
			# Remove diacritics
			nodiacritics = decomposed \
				.encode("ascii", "ignore") \
				.decode("utf-8")
			# Check there's no consecutive uppers
			if re_acronym.search(nodiacritics) is None:
				# Save original (UTF-8) title
				curtitle = data
				return
		curtitle = None
		return
	if not intext or curtitle is None:
		return
	if curtitle in words:
		return
	curtype = None
	headerlvlskip = None
	data = decomment(data)
	for line in data.splitlines():
		if line.startswith("{{"):
			s = re_header.match(line)
			if s is None:
				curtype = None
			else:
				curtype = s.group(2)
			continue
		def_match = re_def.match(line)
		if def_match is None:
			continue
		headerlvl = len(def_match.group(1))
		if headerlvlskip is not None \
		and headerlvl > headerlvlskip:
			continue
		headerlvlskip = None
		if curtype not in keep_types:
			continue
		defcat_match = re_defcat.match(line)
		inflof_match = re_inflof.match(line)
		if infl_pass:
			if inflof_match is None:
				continue
			for tag in re_tag.findall(line):
				subtags = re_subtag.findall(tag)
				tag0 = subtags[0].lower().strip()
				if tag0 in lb + tlb \
				or tag0 not in keep_infls:
					continue
				n = 1 if tag0.startswith("en-") else 2
				if len(subtags) <= n:
					continue
				base = subtags[n]
				if base in words:
					break
			else: # No base in words
				break
		elif inflof_match is not None:
			continue
		for tag in re_tag.findall(line):
			subtags = re_subtag.findall(tag)
			tag0 = subtags[0].lower().strip()
			if tag0 in remove_infls:
				break
			if tag0 in lb + tlb:
				for st in subtags[2:]:
					st = st.lower().strip()
					if st in remove_lbls \
					or "slang" in st \
					or "obsolete" in st:
						if tag0 in tlb:
							return
						break
				else:
					continue
				break
		else:
			if defcat_match is not None:
				continue
			words.add(curtitle)
			fout.write(curtitle+"\n")
			#fout.write(f"{curtitle:<20} {curtype:<8} {line}\n")
			numwords += 1
			if numwords % 100 == 0:
				print(f"{numwords:<8} ({100*fin.tell()/fin_bytes:.1f}%)", end="\r")
			curtitle = None
			return
		if defcat_match is not None:
			headerlvlskip = headerlvl

print("1st pass: Find words with an accepted definition")
p = xml.parsers.expat.ParserCreate()
p.StartElementHandler = start_element
p.EndElementHandler = end_element
p.CharacterDataHandler = char_data
p.buffer_text = True
p.buffer_size = 1024 # Will be expanded as needed
p.ParseFile(fin)
print(f"pass: {numwords}, total: {len(words)}")

print("2nd pass: Find words defined by an accepted reference (inflection, etc) to a word in the 1st pass")
fin.seek(fin_start, os.SEEK_SET)
infl_pass = True
numwords = 0
p = xml.parsers.expat.ParserCreate()
p.StartElementHandler = start_element
p.EndElementHandler = end_element
p.CharacterDataHandler = char_data
p.buffer_text = True
p.buffer_size = 1024
p.ParseFile(fin)
print(f"pass: {numwords}, total: {len(words)}")
