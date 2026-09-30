"""Decide whether four-digit numbers in English text should be spoken as years.

Pure Python with no NVDA imports, so it can be unit tested outside NVDA and
dropped into a global plugin unchanged. The public entry point is
``convertYears(text)``, which returns the text with year-like numbers
replaced by their spoken form in words ("1523" -> "fifteen twenty-three").
"""

import re

# Classification strengths.
NONE = 0
MEDIUM = 1  # Year only if the following word doesn't look like a counted noun.
STRONG = 2  # Year regardless of what follows.

# A four-digit number not glued to letters or other digits, optionally
# followed by a plural/possessive "s" ("1990s", "1990's", "1966's").
CANDIDATE_RE = re.compile(r"(?<![\w])(\d{4})('?s)?(?![\w])")

# Numeric dates: 29/09/2026, 29.09.2026, 29-09-2026 and ISO 2026-09-29.
NUMERIC_DATE_BEFORE_RE = re.compile(r"(?<![\w.,])\d{1,2}([./-])\d{1,2}\1$")
NUMERIC_DATE_AFTER_RE = re.compile(r"^-\d{1,2}-\d{1,2}(?![\w])")

# Part of a larger number: 1,523 / 1.523 / 12,1523 / 1523.5 / 1523,000.
IN_LARGER_NUMBER_BEFORE_RE = re.compile(r"\d[.,]$")
IN_LARGER_NUMBER_AFTER_RE = re.compile(r"^[.,]\d")

# Month names must be capitalised so that "may", "march" etc. used as
# ordinary words don't trigger. An optional day may sit between the month and
# the year: "September 2026", "Sept. 2026", "September 29, 2026",
# "29 September 2026", "29th of Sept 2026".
_MONTH = (
	r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
	r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
	r"|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEPT?|OCT|NOV|DEC)"
)
MONTH_BEFORE_RE = re.compile(
	rf"\b{_MONTH}\.?(?:\s+\d{{1,2}}(?:st|nd|rd|th)?)?,?\s+$"
)

# Words directly before the number that make it a year on their own.
STRONG_BEFORE_RE = re.compile(
	r"(?:\b(?:years?|yr|FY|fiscal\s+year|class\s+of|vintage|copyright|anno|"
	r"A\.?D\.?|C\.?E\.?|Q[1-4]|H[12])\s*|©\s*|\(c\)\s*)$",
	re.IGNORECASE,
)

# Words directly after the number that make it a year on their own.
STRONG_AFTER_RE = re.compile(r"^\s*(?:A\.D\.|B\.C\.(?:E\.)?|C\.E\.|AD|BCE?|CE)(?![\w])")

# Prepositions and similar that usually introduce a year, but also introduce
# counts ("in 1523 cases"), so they only count when followed by something
# that isn't a counted noun (see _followedByCountedNoun).
MEDIUM_BEFORE_RE = re.compile(
	r"\b(?:in|since|until|till|til|during|before|after|by|from|through|"
	r"between|circa|c\.|ca\.|around|of|early|mid|late|born|died|founded|"
	r"established|est\.|published|released|dated|spring|summer|autumn|fall|"
	r"winter|Christmas|Easter)[\s-]+$",
	re.IGNORECASE,
)

# Contexts that mean "this is a quantity or identifier, not a year". These
# override every positive signal.
NEGATIVE_BEFORE_RE = re.compile(
	r"(?:[$£€¥#×+]\s*|(?:^|\s)[-−]|\b(?:no\.?|nos\.?|number|page|pages|p\.|pp\.|"
	r"room|flight|route|bus|version|v\.?|model|pin|code|ext\.?|extension|unit|"
	r"suite|apt\.?|box|tel\.?|phone|line|step|item|chapter|section|verse|"
	r"exactly|about|approximately|nearly|over|under|only)\s+)$",
	re.IGNORECASE,
)
NEGATIVE_AFTER_RE = re.compile(
	r"^\s*(?:%|×|°|percent\b|per\s+cent\b|(?:km|kg|g|m|mm|cm|mi|ft|lbs?|oz|"
	r"hz|khz|mhz|ghz|kb|mb|gb|tb|px|pt|rpm|mph|kph|kcal|ml|hrs?)(?![\w])|"
	r"(?:miles?|feet|metres?|meters?|pounds|dollars|euros|yen|hours|minutes|"
	r"seconds|calories|times|pages|words|people|men|women|children|"
	r"items|units|votes|points)\b)",
	re.IGNORECASE,
)

# Words that may follow a year in running text. A lowercase word outside this
# set after a MEDIUM signal is taken to be a counted noun: "in 1523 cases".
FOLLOWING_FUNCTION_WORDS = frozenset("""
	a an the and or but nor so yet as at on to for with by of in into from
	after before until till when while where which who whom whose that this
	these those there then than he she it they we i you his her its their our
	my your was were is are be been being had has have did do does will would
	could should might must can may saw became began ended came went
	alone only onwards onward
""".split())

WORD_AFTER_RE = re.compile(r"^\s*([A-Za-z][\w'-]*)")

# Ranges. If either end of a range is a year, both are.
RANGE_JOIN_RE = re.compile(r"^\s*(?:[-–—]|to|and|or|until|till|through|thru)\s*$", re.IGNORECASE)
# Short-form range "1914-18": a year when the two-digit end is later.
SHORT_RANGE_AFTER_RE = re.compile(r"^[-–](\d{2})(?![\w])")

PLAUSIBLE_MEDIUM = range(1000, 2100)

_ONES = (
	"zero one two three four five six seven eight nine ten eleven twelve "
	"thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
).split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
_TENS_PLURAL = "_ tens twenties thirties forties fifties sixties seventies eighties nineties".split()


def _twoDigits(n):
	if n < 20:
		return _ONES[n]
	tens, ones = divmod(n, 10)
	return _TENS[tens] + ("-" + _ONES[ones] if ones else "")


def yearToWords(n, suffix="", twentyStyle="split"):
	"""Spoken form of year ``n``, or None to leave it for the synthesizer.

	``suffix`` is "", "s", "'s". A plural suffix on a year ending in 0 is a
	decade or century ("1990s" -> "nineteen nineties").
	``twentyStyle`` is "split" ("twenty twenty-six") or "thousand" (leave
	2010-2099 to the synthesizer, which says "two thousand and twenty-six").
	"""
	hi, lo = divmod(n, 100)
	plural = suffix in ("s", "'s") and n % 10 == 0
	if twentyStyle == "thousand" and 2010 <= n <= 2099:
		return None
	if plural:
		if n % 1000 == 0:
			return None  # "2000s": synthesizer's "two thousands" is fine.
		if lo == 0:
			return _twoDigits(hi) + " hundreds"
		if hi % 10 == 0 and lo < 10:
			return None
		lead = _twoDigits(hi)
		if lo < 20:
			return lead + " " + ("tens" if lo == 10 else _ONES[lo] + "s")
		return lead + " " + _TENS_PLURAL[lo // 10]
	possessive = "'s" if suffix == "'s" else ""
	if hi % 10 == 0 and lo < 10:
		# 1000-1009, 2000-2009, 3000: "two thousand and five" is already right.
		return None
	if lo == 0:
		words = _twoDigits(hi) + " hundred"
	elif lo < 10:
		words = _twoDigits(hi) + " oh " + _ONES[lo]
	else:
		words = _twoDigits(hi) + " " + _twoDigits(lo)
	return words + possessive


def _followedByCountedNoun(after):
	match = WORD_AFTER_RE.match(after)
	if not match:
		return False  # Punctuation or end of text.
	word = match.group(1)
	if word[0].isupper():
		return False  # "In 1969 Apollo 11 landed".
	return word.lower() not in FOLLOWING_FUNCTION_WORDS


def classify(text, start, end, suffix=""):
	"""Strength of the evidence that text[start:end] (four digits) is a year."""
	before = text[:start]
	after = text[end:]
	value = int(text[start:end])
	if text[start] == "0":
		return NONE
	if IN_LARGER_NUMBER_BEFORE_RE.search(before) and not NUMERIC_DATE_BEFORE_RE.search(before):
		return NONE
	if IN_LARGER_NUMBER_AFTER_RE.match(after):
		return NONE
	if NEGATIVE_BEFORE_RE.search(before) or NEGATIVE_AFTER_RE.match(after):
		return NONE
	if (
		NUMERIC_DATE_BEFORE_RE.search(before)
		or NUMERIC_DATE_AFTER_RE.match(after)
		or MONTH_BEFORE_RE.search(before)
		or STRONG_BEFORE_RE.search(before)
		or STRONG_AFTER_RE.match(after)
	):
		return STRONG
	if (suffix == "'s" or suffix and value % 10 == 0) and value in PLAUSIBLE_MEDIUM:
		return STRONG  # "the 1990s", "the 1500s", "1966's World Cup".
	shortRange = SHORT_RANGE_AFTER_RE.match(after)
	if shortRange and int(shortRange.group(1)) > value % 100 and value in PLAUSIBLE_MEDIUM:
		return STRONG  # "1914-18".
	if value not in PLAUSIBLE_MEDIUM:
		return NONE
	if before.endswith("(") and after.startswith(")"):
		return MEDIUM  # Citation or film year: "Smith (2019)", "Alien (1979)".
	if MEDIUM_BEFORE_RE.search(before):
		return NONE if _followedByCountedNoun(after) else MEDIUM
	return NONE


def findYears(text):
	"""Return [(start, end, value, suffix)] for each number judged to be a year.

	``end`` includes the suffix.
	"""
	candidates = []
	for match in CANDIDATE_RE.finditer(text):
		suffix = match.group(2) or ""
		strength = classify(text, match.start(1), match.end(1), suffix)
		candidates.append([match.start(), match.end(), int(match.group(1)), suffix, strength])

	# Ranges: "from 1914 to 1918", "1914–1918", "between 1914 and 1918".
	for left, right in zip(candidates, candidates[1:]):
		if not RANGE_JOIN_RE.match(text[left[1]:right[0]]):
			continue
		bothPlausible = left[2] in PLAUSIBLE_MEDIUM and right[2] in PLAUSIBLE_MEDIUM
		if left[4] or right[4]:
			if bothPlausible and not _isBlocked(text, left) and not _isBlocked(text, right):
				left[4] = right[4] = max(left[4], right[4], MEDIUM)
		elif (
			bothPlausible
			and text[left[1]:right[0]].strip() in "-–—"
			and 0 < right[2] - left[2] < 300
			and not _isBlocked(text, left)
			and not _isBlocked(text, right)
		):
			left[4] = right[4] = MEDIUM  # Bare "1914–1918".

	return [(s, e, v, suf) for s, e, v, suf, strength in candidates if strength]


def _isBlocked(text, candidate):
	start, end = candidate[0], candidate[1]
	return bool(
		NEGATIVE_BEFORE_RE.search(text[:start])
		or NEGATIVE_AFTER_RE.match(text[end:])
		or IN_LARGER_NUMBER_AFTER_RE.match(text[start + 4:])
	)


def convertYears(text, twentyStyle="split"):
	"""Replace year-like four-digit numbers in ``text`` with spoken words."""
	parts = []
	last = 0
	for start, end, value, suffix in findYears(text):
		words = yearToWords(value, suffix, twentyStyle)
		if words is None:
			continue
		parts.append(text[last:start])
		parts.append(words)
		last = end
	parts.append(text[last:])
	return "".join(parts)
