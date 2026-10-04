# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

An NVDA (NonVisual Desktop Access screen reader) add-on that speaks four-digit numbers as years when the context says they are years: "built in 1523" → "fifteen twenty-three" instead of "one thousand five hundred and twenty three". `requirements.txt` is the user's original brief in plain English, **not** a pip requirements file. The repo is https://github.com/Chessel85/NVDAAnnounceYears (public). Licence: GPL-2.0.

## Commands

Run the tests (standard-library `unittest`; pytest isn't installed):

```
python -m unittest discover -s tests
```

Run one test: `python -m unittest tests.test_yearDetector.ConvertYearsTest.test_cases`

## Architecture

- `addon/globalPlugins/yearsAsDates/__init__.py`: the NVDA global plugin. It registers on `speech.extensions.filter_speechSequence`, which runs before NVDA's symbol and dictionary processing, so the rules see raw text. `convertSpeechSequence()` joins consecutive strings (so "September", "2026" split across items still match) and skips character mode and non-English `LangChangeCommand` runs. Any exception is logged and the original sequence returned, so a bug can never silence speech. It also adds a settings panel, config section `yearsAsDates` (`enabled`, `twentyStyle`) and a toggle script with no default gesture.
- `addon/globalPlugins/yearsAsDates/yearDetector.py`: all detection and pronunciation logic, in pure Python with no NVDA imports so it runs under plain `unittest`. `convertYears(text)` is the entry point. Each four-digit candidate is classified by `classify()` as STRONG (year regardless), MEDIUM (year unless followed by a lowercase counted noun, range 1000–2099 only) or NONE. Negative contexts (currency, units, "page", "PIN", part of a larger number) are checked first and override everything. `findYears()` then spreads year status across ranges ("from 1914 to 1918"). `yearToWords()` produces English words, and returns None for numbers the synthesizer already says well (2000–2009, x000), which are then left untouched.
- `tests/test_yearDetector.py`: `CASES` is a table of (input, expected output). Add a row there for every new rule or reported misreading.
- `docs/viability.md`: the full rule set, the NVDA integration plan and known limitations. Keep it in sync when rules change.

The user runs NVDA 2026.2. The NVDA API names used were checked against its `library.zip`. `addon/manifest.ini` holds the add-on metadata (bump `version` there for a release). `python build.py` packages `addon/` into `NVDAAnnounceYears-<version>.nvda-addon`.

Code style follows NVDA conventions: tabs for indentation and camelCase names.

## Development environment

The user has a working NVDA scratchpad folder for loading development code. By default this is `%APPDATA%\nvda\scratchpad`, and "Enable loading custom code from Developer Scratchpad directory" must be on in NVDA's Advanced settings. Global plugin code goes in its `globalPlugins` subfolder. Reload plugins with NVDA+Ctrl+F3.

The repo copy is the source of truth. After editing, copy it over the scratchpad copy:

```
rm -rf "$APPDATA/nvda/scratchpad/globalPlugins/yearsAsDates" && cp -r addon/globalPlugins/yearsAsDates "$APPDATA/nvda/scratchpad/globalPlugins/"
```
