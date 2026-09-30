"""Speak four-digit numbers as years when the surrounding text says they are years.

The detection rules live in yearDetector.py, which has no NVDA dependencies.
This module only hooks NVDA's speech pipeline and provides settings.
"""

import re

import addonHandler
import config
import globalPluginHandler
import gui
import ui
import wx
from gui import guiHelper
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from logHandler import log
from scriptHandler import script
from speech import getCurrentLanguage
from speech.commands import CharacterModeCommand, LangChangeCommand
from speech.extensions import filter_speechSequence

from . import yearDetector

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	pass  # Running from the scratchpad rather than as an installed add-on.

SECTION = "yearsAsDates"

config.conf.spec[SECTION] = {
	"enabled": "boolean(default=True)",
	"twentyStyle": 'option("split", "thousand", default="split")',
}

# (config value, label) for how 2010-2099 are spoken.
TWENTY_STYLES = (
	# Translators: How years 2010 to 2099 are spoken.
	("split", _("twenty twenty-six")),
	# Translators: How years 2010 to 2099 are spoken.
	("thousand", _("two thousand and twenty-six (the voice's own reading)")),
)

# Cheap check so sequences without four digits in a row skip all the work.
FOUR_DIGITS_RE = re.compile(r"\d{4}")

# Translators: Name of the add-on's settings panel and input gestures category.
ADDON_NAME = _("Years as Dates")


def convertSpeechSequence(speechSequence):
	"""Return ``speechSequence`` with year-like numbers in its strings spoken as years.

	Consecutive strings are converted together so that context split across
	them ("September", "2026") is still seen. Strings spoken in character mode
	or in a non-English language are left alone.
	"""
	if not any(isinstance(item, str) and FOUR_DIGITS_RE.search(item) for item in speechSequence):
		return speechSequence
	twentyStyle = config.conf[SECTION]["twentyStyle"]
	defaultLanguage = getCurrentLanguage() or ""
	language = defaultLanguage
	characterMode = False
	result = []
	run = []

	def flushRun():
		if not run:
			return
		if language.lower().startswith("en") and not characterMode:
			joined = " ".join(run)
			converted = yearDetector.convertYears(joined, twentyStyle)
			if converted != joined:
				log.debug(f"Years as Dates: {joined!r} -> {converted!r}")
				result.append(converted)
				run.clear()
				return
		result.extend(run)
		run.clear()

	for item in speechSequence:
		if isinstance(item, str):
			run.append(item)
			continue
		flushRun()
		if isinstance(item, LangChangeCommand):
			language = item.lang or defaultLanguage
		elif isinstance(item, CharacterModeCommand):
			characterMode = item.state
		result.append(item)
	flushRun()
	return result


class YearsAsDatesPanel(SettingsPanel):
	title = ADDON_NAME

	def makeSettings(self, settingsSizer):
		helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.enabledCheckBox = helper.addItem(
			# Translators: Checkbox in the Years as Dates settings panel.
			wx.CheckBox(self, label=_("&Speak four-digit numbers as years when the context suggests a year")),
		)
		self.enabledCheckBox.SetValue(config.conf[SECTION]["enabled"])
		self.twentyStyleChoice = helper.addLabeledControl(
			# Translators: Label for the choice of how years 2010 to 2099 are spoken.
			_("Speak years 2010 to 2099 as:"),
			wx.Choice,
			choices=[label for value, label in TWENTY_STYLES],
		)
		values = [value for value, label in TWENTY_STYLES]
		self.twentyStyleChoice.SetSelection(values.index(config.conf[SECTION]["twentyStyle"]))

	def onSave(self):
		config.conf[SECTION]["enabled"] = self.enabledCheckBox.IsChecked()
		config.conf[SECTION]["twentyStyle"] = TWENTY_STYLES[self.twentyStyleChoice.GetSelection()][0]


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		filter_speechSequence.register(self._filterSpeechSequence)
		NVDASettingsDialog.categoryClasses.append(YearsAsDatesPanel)

	def terminate(self):
		filter_speechSequence.unregister(self._filterSpeechSequence)
		NVDASettingsDialog.categoryClasses.remove(YearsAsDatesPanel)
		super().terminate()

	def _filterSpeechSequence(self, speechSequence, *args, **kwargs):
		if not config.conf[SECTION]["enabled"]:
			return speechSequence
		try:
			return convertSpeechSequence(speechSequence)
		except Exception:
			# Never let a bug here stop NVDA from speaking.
			log.exception("Years as Dates: conversion failed")
			return speechSequence

	@script(
		# Translators: Description of the toggle command in the Input Gestures dialog.
		description=_("Turns speaking four-digit numbers as years on or off"),
		category=ADDON_NAME,
	)
	def script_toggle(self, gesture):
		enabled = not config.conf[SECTION]["enabled"]
		config.conf[SECTION]["enabled"] = enabled
		# Translators: Reported when the add-on is turned on or off.
		ui.message(_("Years as dates on") if enabled else _("Years as dates off"))
