# Years as dates: viability and rules

## Verdict

Viable, and small. The detection logic is about 250 lines of pure Python (`addon/globalPlugins/yearsAsDates/yearDetector.py`), already passing a table of 60+ cases. The NVDA side is a global plugin of a few dozen lines that runs each spoken string through `convertYears()` before it reaches the synthesizer. That plugin is now written: `addon/globalPlugins/yearsAsDates/`.

## How it plugs into NVDA

- **Hook:** register a handler on `speech.extensions.filter_speechSequence` (added in NVDA 2024.2, confirmed present in NVDA 2026.2). It receives the speech sequence, a list of strings and command objects, and returns a modified list. On older NVDA versions the fallback is to wrap `speech.speech.speak`, which works but is fragile.
- **Change only the strings:** leave command objects alone. Skip strings spoken in character mode (after a `CharacterModeCommand(True)`) so spelling out "1523" still says "one five two three".
- **Output is words:** "1523" becomes "fifteen twenty-three", not "15 23". Words sound the same on every synthesizer. Splitting the digits would depend on how each voice reads "15 23", and would mangle "1905" into "nineteen five".
- **Braille is unaffected,** because the hook only changes speech.
- **English only:** read the current synthesizer's language and do nothing unless it starts with `en`. The month names, prepositions and number words are all English.

## Limitations to accept

1. **Context is limited to one speech string.** When reading line by line, "September" at the end of one line and "2026" at the start of the next arrive separately, so the year isn't detected. Say All and paragraph reading usually give whole sentences, so this mainly affects line and word navigation. Moving by word ("2026" on its own) always stays a number, which is arguably correct.
2. **Some voices already do this.** Microsoft OneCore and SAPI voices apply their own text normalisation and may already say "in 1523" as a year. Because the add-on hands them words, nothing gets converted twice, but the benefit varies by voice. Test with each synthesizer you use. eSpeak NG is the most likely to gain.
3. **Heuristics will sometimes be wrong.** The mistakes are mild, though: "fifteen hundred cases" still means 1500, and it's only when the last two digits aren't zero ("fifteen twenty-three cases") that the listener has to translate. The rules below lean towards leaving numbers alone when unsure.
4. **An NVDA speech dictionary could do part of this without an add-on:** for example, a regex entry that rewrites `\b(in|year) (1\d)(\d\d)\b`. The add-on is worth it for what a regex entry can't do well: checking the following word, ranges, decades, "oh" years such as 1905, and exclusions.

## Prior work (checked 2026-09-29)

No existing add-on decides from context whether a number is a year. Checked: the NVDA add-on store catalogue for NVDA 2026.2 (411 add-ons), GitHub, and the NVDA and eSpeak NG issue trackers.

- **num2words_nvda** (nvda-es): its real-time mode rewrites every number as a plain cardinal. It has a "Year" conversion, but only as a manual option applied to text you choose. Last commit May 2024, and it isn't listed in the store for NVDA 2026.2.
- **Number Processing** (ABuffEr) and **number_announce_nvda_addon** (larry801): read numbers digit by digit. They don't detect years.
- **Indian Number System**: groups numbers into lakh and crore. It doesn't detect years.
- **dateParser**, **Day of the week**, **Clock**: commands you run on purpose. They don't change how text is read.
- **eSpeak NG issue #92** "Detect and support different number forms (years, times, fractions)": open since 2016. Its maintainer notes that the hard part is telling from context which form a number is in.

Conflict to watch: num2words' real-time mode and Number Processing both rewrite digits too. num2words hooks the speech manager, which runs after `filter_speechSequence`, so years are already words by the time it sees them. I haven't checked where Number Processing hooks in.

## Rules

Each four-digit number (not attached to letters or other digits, optional `s`/`'s` suffix) gets one of three verdicts:

- **Strong:** a year no matter what follows.
- **Medium:** a year unless the next word looks like a counted noun.
- **None:** leave it as a number.

Exclusions are checked first and override everything.

### Exclusions (always a number)

| Context | Examples |
|---|---|
| Part of a larger number | `1,523` `1.523` `1523.5` `15234` |
| Leading zero | `0523` (PINs, codes) |
| Glued to letters | `A1523` `1920x1080` |
| Currency or symbol before | `$1523` `£1523` `#1523` `-1523` `×1523` |
| Identifier word before | page, pp., no., number, room, flight, route, version, model, PIN, code, ext, unit, suite, box, phone, chapter, section, step |
| Quantity word before | about, approximately, nearly, exactly, over, under, only |
| Unit or counted noun after | %, °, km, kg, MB, hours, miles, pounds, dollars, people, words, pages, votes |

### Strong signals

| Signal | Examples |
|---|---|
| Month name, full or abbreviated, capitalised, optional day | `September 2026` `Sept. 2026` `September 29, 2026` `29th of Sept 2026` |
| Numeric date | `29/09/2026` `29.09.2026` `2026-09-29` |
| Year words | `year 1523` `the year 1523` `FY 2025` `fiscal year` `class of 1985` `vintage` |
| Copyright | `Copyright 1998` `© 1998` `(c) 1998` |
| Era markers | `AD 1066` `1066 AD` `500 BC`* `1066 CE` |
| Quarter or half | `Q3 2026` `H1 2026` |
| Decade or century suffix | `1990s` `1990's` `1500s` |
| Possessive | `1966's World Cup` |
| Short range | `1914-18` |

*Only four-digit numbers are handled, so `500 BC` itself is out of scope.

Month names must be capitalised, so "you may 2000" stays a number.

### Medium signals (range 1000–2099 only)

Words before: in, since, until, till, during, before, after, by, from, through, between, circa, c., ca., around, of, early, mid, late, born, died, founded, established, est., published, released, dated, and the seasons and festivals (spring, summer, autumn, fall, winter, Christmas, Easter).

Also a number alone in brackets: `Smith (2019)`, `Alien (1979)`.

**Following-word check:** a medium signal only makes a year if the number is followed by punctuation, the end of the text, a capitalised word, or a common function word (the, and, was, when, he, …). A lowercase word outside that list is taken to be a counted noun:

- `built in 1523.` → year
- `In 1969 Apollo 11 landed` → year
- `in 1523 cases` → number
- `In 1969 man landed` → number (a missed year, accepted as the cost of caution)

### Ranges

Two numbers joined by `-`, `–`, `—`, to, and, or, until or through: if either end is a year, both are (`from 1914 to 1918`, `between 1914 and 1918`). A bare en-dash or hyphen range with both ends in 1000–2099, the second later than the first by less than 300 years, counts as medium (`1914–1918`). `pp. 1523-1530` stays numbers because of the `pp.` exclusion.

### Plausible range

Medium signals and bare ranges only apply to 1000–2099. Strong signals accept any four-digit number, so "the year 2525" still works. "in 4500 years" stays a number.

## Pronunciation

| Number | Spoken | Rule |
|---|---|---|
| 1523 | fifteen twenty-three | Split into two pairs |
| 1905 | nineteen oh five | Second pair 01–09 → "oh" |
| 1900 | nineteen hundred | Second pair 00 |
| 1066 | ten sixty-six | |
| 2026 | twenty twenty-six | Setting: or leave as "two thousand and twenty-six" |
| 2005, 2000, 1005, 3000 | *(unchanged)* | The synthesizer's "two thousand and five" is already right |
| 1990s | nineteen nineties | |
| 1500s | fifteen hundreds | |
| 1910s | nineteen tens | |

## Possible settings

- On/off toggle, with a gesture to switch quickly.
- 2010–2099 style: "twenty twenty-six" or "two thousand and twenty-six".
- Include the bracketed-number rule (it's the weakest signal).
