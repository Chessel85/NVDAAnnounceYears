import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins", "yearsAsDates"))

from yearDetector import convertYears, yearToWords  # noqa: E402

# (input, expected output). Unchanged text means "stay a number".
CASES = [
	# Rules from the brief.
	("It was built in 1523.", "It was built in fifteen twenty-three."),
	("It was built in the year 1523.", "It was built in the year fifteen twenty-three."),
	("September 2026", "September twenty twenty-six"),
	("Sept 2026", "Sept twenty twenty-six"),
	("There were 1,523 of them.", "There were 1,523 of them."),
	("The value is 1.523 today.", "The value is 1.523 today."),
	("It cost 1523 pounds.", "It cost 1523 pounds."),
	# Months with a day.
	("September 29, 2026", "September 29, twenty twenty-six"),
	("29 September 2026", "29 September twenty twenty-six"),
	("the 29th of Sept. 2026", "the 29th of Sept. twenty twenty-six"),
	("you may 2000", "you may 2000"),
	# Numeric dates.
	("Due 29/09/2026.", "Due 29/09/twenty twenty-six."),
	("Due 29.09.2026.", "Due 29.09.twenty twenty-six."),
	("Due 2026-09-29.", "Due twenty twenty-six-09-29."),
	# Other strong signals.
	("Copyright 1998 Acme", "Copyright nineteen ninety-eight Acme"),
	("© 1998 Acme", "© nineteen ninety-eight Acme"),
	("class of 1985", "class of nineteen eighty-five"),
	("FY 2025 results", "FY twenty twenty-five results"),
	("AD 1066", "AD ten sixty-six"),
	("1066 AD", "ten sixty-six AD"),
	("the 1990s", "the nineteen nineties"),
	("the 1990's", "the nineteen nineties"),
	("the 1500s", "the fifteen hundreds"),
	("the 1910s", "the nineteen tens"),
	("1966's World Cup", "nineteen sixty-six's World Cup"),
	# Prepositions and similar, checked against the following word.
	("since 1985 we have", "since nineteen eighty-five we have"),
	("In 1969, Apollo", "In nineteen sixty-nine, Apollo"),
	("In 1969 Apollo 11 landed", "In nineteen sixty-nine Apollo 11 landed"),
	("in 1523 cases", "in 1523 cases"),
	("by 2030 the", "by twenty thirty the"),
	("born 1920 in Leeds", "born nineteen twenty in Leeds"),
	("the summer of 1976", "the summer of nineteen seventy-six"),
	("circa 1450.", "circa fourteen fifty."),
	("Alien (1979)", "Alien (nineteen seventy-nine)"),
	# Ranges.
	("from 1914 to 1918", "from nineteen fourteen to nineteen eighteen"),
	("between 1914 and 1918", "between nineteen fourteen and nineteen eighteen"),
	("the war of 1914–1918", "the war of nineteen fourteen–nineteen eighteen"),
	("1914–1918", "nineteen fourteen–nineteen eighteen"),
	("1914-18", "nineteen fourteen-18"),
	("pp. 1523-1530", "pp. 1523-1530"),
	# Stays a number.
	("1523", "1523"),
	("There are 1523 items.", "There are 1523 items."),
	("page 1523", "page 1523"),
	("$1523", "$1523"),
	("#1523", "#1523"),
	("PIN 1523", "PIN 1523"),
	("room 1523", "room 1523"),
	("about 1500 people", "about 1500 people"),
	("in 1500 words", "in 1500 words"),
	("1920x1080", "1920x1080"),
	("A1523", "A1523"),
	("15234", "15234"),
	("0523", "0523"),
	("1523.5", "1523.5"),
	("at 1523 hours", "at 1523 hours"),
	("in 4500 years", "in 4500 years"),
	("-1523", "-1523"),
	# Left to the synthesizer, which already says these well.
	("in 2005", "in 2005"),
	("in the year 2000", "in the year 2000"),
	("the 2000s", "the 2000s"),
]


class ConvertYearsTest(unittest.TestCase):
	def test_cases(self):
		for text, expected in CASES:
			with self.subTest(text=text):
				self.assertEqual(convertYears(text), expected)

	def test_thousandStyleLeavesTwentyTensAlone(self):
		self.assertEqual(convertYears("in 2026 we", twentyStyle="thousand"), "in 2026 we")


class YearToWordsTest(unittest.TestCase):
	def test_words(self):
		for value, expected in [
			(1523, "fifteen twenty-three"),
			(1905, "nineteen oh five"),
			(1900, "nineteen hundred"),
			(1100, "eleven hundred"),
			(1010, "ten ten"),
			(2010, "twenty ten"),
			(2026, "twenty twenty-six"),
			(2005, None),
			(1000, None),
		]:
			with self.subTest(value=value):
				self.assertEqual(yearToWords(value), expected)


if __name__ == "__main__":
	unittest.main()
