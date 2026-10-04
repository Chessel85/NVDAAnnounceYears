# Announce Years (NVDA add-on)

Speaks four-digit numbers as years when the context says they are years.

By default, NVDA reads "It was built in 1523" as "one thousand five hundred and twenty-three". With this add-on it says "fifteen twenty-three". Numbers that aren't years, such as "1523 people" or "page 1523", are left alone.

## Examples

| Text | Spoken as |
|---|---|
| It was built in 1523. | fifteen twenty-three |
| September 2026 | September twenty twenty-six |
| in the year 1905 | nineteen oh five |
| from 1914 to 1918 | nineteen fourteen to nineteen eighteen |
| the 1990s | the nineteen nineties |
| Copyright 1998 | Copyright nineteen ninety-eight |
| 1523 people | one thousand five hundred and twenty-three people *(unchanged)* |
| page 1523, $1523, 1,523 | *(unchanged)* |

## How it decides

The add-on looks at the words around each four-digit number:

- **Always a year:** after a month name ("Sept 2026", "29 September 2026"), in a numeric date ("29/09/2026"), after "year", "copyright", "©" or "Q3", next to "AD", "BC" or "CE", or with a decade suffix ("1990s").
- **Usually a year:** after words such as "in", "since", "during", "born", "founded" or "circa", or alone in brackets ("Alien (1979)"). These only count for numbers from 1000 to 2099, and not when a counted noun follows ("in 1523 cases").
- **Never a year:** part of a larger number ("1,523", "1.523"), after a currency symbol, after words such as "page", "room", "PIN" or "about", or before a unit ("1523 km", "1523 hours").

When unsure, it leaves the number alone. The full rule set is in [docs/viability.md](docs/viability.md).

## Settings

Open the NVDA menu, then Preferences, Settings, and choose the **Announce Years** category.

- **Speak four-digit numbers as years when the context suggests a year:** turns the add-on on or off.
- **Speak years 2010 to 2099 as:** "twenty twenty-six" or "two thousand and twenty-six" (the voice's own reading).

There's also a command to turn the add-on on and off quickly. It has no gesture by default; assign one in NVDA's Input Gestures dialog, under the **Announce Years** category.

## Things to know

- **English only.** Text read in other languages is not changed.
- **Speech only.** Braille output is not affected.
- **Spelling is not affected.** Reading character by character still says "one, five, two, three".
- **Some voices already do this.** Microsoft OneCore and SAPI voices sometimes read years correctly on their own. eSpeak NG benefits most.
- **It will sometimes be wrong.** "In 1969 man landed on the Moon" stays a number, because "man" looks like something being counted.
- **Other number add-ons.** Add-ons that also rewrite numbers, such as Number Processing, may interact with this one.

## Requirements

NVDA 2025.1 or later. Tested with NVDA 2026.2.

## Installation

<!-- TODO: replace with the Add-on Store once the add-on is published. -->
Download the latest `.nvda-addon` file from the [releases page](https://github.com/Chessel85/NVDAAnnounceYears/releases) and open it. NVDA asks you to confirm, then restart.

## Reporting a misreading

If a number is read the wrong way, please [open an issue](https://github.com/Chessel85/NVDAAnnounceYears/issues) with the sentence that was misread and how you expected it to sound.

## For developers

The detection logic is in `addon/globalPlugins/yearsAsDates/yearDetector.py`. It's plain Python with no NVDA imports, so it can be tested on its own:

```
python -m unittest discover -s tests
```

To build the add-on package:

```
python build.py
```

This creates `NVDAAnnounceYears-<version>.nvda-addon`.

## Licence

GPL-2.0. Author: Chessel85.
