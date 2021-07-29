import api
import globalPluginHandler
import scriptHandler
import ui
import gui
import textInfos

from core import callLater
from keyboardHandler import KeyboardInputGesture
from tones import beep
from logHandler import log
from time import sleep
from .calendar import *
from .utility import *
from . import constants
from .clipEditor import MyFrame

# compatibility with nvda 2021.1.
try:
	from speech import speech
except ImportError:
	import speech


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = "剪贴板增强"
	pt = pti = {}

	def __init__(self):
		super().__init__()
		self.flg = 1
		self.spoken2 = self.spoken = ""
		self.spoken_word = self.spoken_char = -1
		self.oldSpeak = speech.speak
		speech.speak = self.newSpeak
		self.text = ""
		self.files = []
		self.info = ""
		self.lines = ["无数据",]
		self.line = self.char = self.word =-1
		self.SpokenPreWordPos = -1 #self.preWordPos = 0
		self.monitor = None
		self.editor = None
		callLater(100, self.clipboard)
		self.Dict = None
		callLater(200, self.loadFiles)

	def clipboard(self):
		self.editor = MyFrame(gui.mainFrame, title="剪贴板编辑器")
		self.monitor = ClipboardMonitor(self.editor.GetHandle())
		self.monitor.customization = self.func
		callLater(100, self.monitor.get_clipboard_data)
		self.monitor.StartMonitor()

	def loadFiles(self):
		self.Dict = loadJson()

	def func(self):
		self.text = ""
		self.files = None
		self.info = "无数据"
		self.lines = ["无数据"]
		self.word = self.line = self.char = -1
		data = self.monitor.getData()
		if isinstance(data, str):
			self.text = data
			self.lines = data.split("\n")
		elif isinstance(data, list):
			self.files = data
			self.lines = list(fileLists(data))
		elif isinstance(data, bytes):
			self.lines = ["图片",]
			self.info = "图片"

	@scriptHandler.script(
		description=_("剪贴板综述"), 
		gestures=["kb(desktop):control+numpaddelete", "kb(laptop):NVDA+Alt+'"])
	def script_briefClip(self, gesture):
		if self.text:
			self.info = f'第{self.line+1}行， 共{len(self.lines)}行， {len("".join(self.lines))}个字'
		elif self.files is not None:
			self.info = self.monitor.calc(self.files)
		ui.message(self.info)

	@scriptHandler.script(
		description=_("剪贴板第一行"), 
		gestures=["kb(desktop):control+numpaddivide", "kb(laptop):NVDA+Alt+shift+UpArrow"])
	def script_firstLine(self, gesture):
		self.line = 0
		ui.message(self.lines[self.line])

	@scriptHandler.script(
		description=_("剪贴板最后一行"), 
		gestures=["kb(desktop):control+NumpadMultiply", "kb(laptop):NVDA+Alt+shift+DownArrow"])
	def script_lastLine(self, gesture):
		self.line = len(self.lines) - 1
		ui.message(self.lines[self.line])

	@scriptHandler.script(
		description=_("剪贴板上一行"), 
		gestures=["kb(desktop):control+numpad7", "kb(laptop):NVDA+Alt+UpArrow"])
	def script_previousLine(self, gesture):
		self.switchLine(-1)

	@scriptHandler.script(
		description=_("剪贴板下一行"), 
		gestures=["kb(desktop):control+numpad9", "kb(laptop):NVDA+Alt+DownArrow"])
	def script_nextLine(self, gesture):
		self.switchLine(1)

	@scriptHandler.script(
		description=_("剪贴板向上十行"), 
		gestures=["kb(desktop):control+NumpadMinus", "kb(laptop):NVDA+Shift+Alt+PageUp"])
	def script_previousLine10(self, gesture):
		self.switchLine(-10)

	@scriptHandler.script(
		description=_("剪贴板向下十行"), 
		gestures=["kb(desktop):control+NumpadPlus", "kb(laptop):NVDA+Shift+Alt+PageDown"])
	def script_nextLine10(self, gesture):
		self.switchLine(10)

	def switchLine(self, step):
		self.line += step
		if self.line < 0:
			self.line = 0
			beep(9800, 5)
		if self.line >= len(self.lines):
			self.line = len(self.lines) - 1
			beep(9800, 5)
		if self.files: beep(6500, 10)
		ui.message(self.lines[self.line])
		self.word = self.char = -1

	@scriptHandler.script(
		description=_("重复刚听到的内容"), 
		gestures=["kb(desktop):control+Windows+numpaddelete"])
	def script_repeatSpoken(self, gesture):
		ui.message(self.spoken)

	def newSpeak(self, sequence, *args, **kwargs):
		data = ""
		if isinstance(sequence, str):
			data=sequence
		else:
			data = "".join([i for i in sequence if isinstance(i, str)])
		if self.flg ==1: # 捕获最后依次的朗读
			self.spoken = data
			self.spoken_word = self.spoken_char = -1
			self.SpokenPreWordPos = -1
		elif self.flg == 2: # 捕获缓冲区中的朗读
			self.spoken2 = data
			self.flg = 1
		else: # 不补货
			self.flg = 1
		self.oldSpeak(sequence, *args, **kwargs)

	@scriptHandler.script(
		description=_("拷贝刚听到的内容"), 
		gesture=_("kb:NVDA+c"))
	def script_copySpoken(self, gesture):
		repeatCount = scriptHandler.getLastScriptRepeatCount()
		if repeatCount == 1:
			api.copyToClip(self.spoken2)
			self.flg = 0
			ui.message("拷贝")
		elif repeatCount == 0:
			api.copyToClip(self.spoken)
			self.flg = 0
			ui.message("拷贝")

	def _getClipText(self):
		text = ""
		try:
			text = api.getClipData()
		except:
			return text
		if isinstance(text, str) and text:
			return text
		return ""

	@scriptHandler.script(
		description=_("追加刚听到的内容到剪贴板"), 
		gesture="kb:NVDA+D")
	def script_append(self, gesture):
		clip ="" # self._getClipText()
		count = scriptHandler.getLastScriptRepeatCount()
		if count == 1:
			end = "\n" if not self.text.endswith("\n") and self.text else ""
			clip = end.join((self.text, self.spoken2))
			api.copyToClip(clip)
			self.flg = 0
			ui.message("添加")
		elif count == 0:
			end = "\n" if not self.text.endswith("\n") and self.text else ""
			clip = end.join((self.text, self.spoken))
			api.copyToClip(clip)
			self.flg = 0
			ui.message("添加")

	@scriptHandler.script(
		description=_("打开剪贴板编辑器"), 
		gesture="kb:NVDA+E")
	def script_clipEditor(self, gesture):
		if self.editor is None:
			self.editor = MyFrame(gui.mainFrame, title="剪贴板编辑器")
		self.editor.edit.SetValue(self.text.replace("\r\n", "\n"))
		self.editor.Show(True)
		self.editor.Maximize(True)
		self.editor.Raise()

	def switchSpokenWord(self, d=0):
		words = segmentWord(self.spoken)[0]
		if not words: return
		self.spoken_word += d
		l = len(words)
		if self.spoken_word>=l:
			self.spoken_word=l-1
			beep(13500, 4)
		if self.spoken_word<0:
			self.spoken_word=0
			beep(13500, 4)
		word = words[self.spoken_word].lower()
		self.flg = 2
		ui.message(word)
		# 解释当前单词
		if d == 0 and isAlpha(word):
			word = translateWord(self.Dict, word)
			if word:
				self.flg = 2
				ui.message(word)
		# 下一个单词
		elif d == 1:
			i = self.spoken.find(words[self.spoken_word], self.SpokenPreWordPos+1)
			self.spoken_char=i-1 if i>-1 else self.SpokenPreWordPos
			if i>-1: self.SpokenPreWordPos = i
		# 前一个单词
		elif d == -1:
			i = self.spoken.rfind(words[self.spoken_word], 0, self.SpokenPreWordPos)
			self.spoken_char= self.SpokenPreWordPos if i<0 else i-1
			if i>-1: self.SpokenPreWordPos = i

	@scriptHandler.script(
		description=_("刚听到内容的下一个词句"), 
		gestures=["kb(desktop):Control+Windows+Numpad6", "kb(laptop):NVDA+shift+Windows+RightArrow"])
	def script_nextSpokenWord(self, gesture):
		self.switchSpokenWord(1)

	@scriptHandler.script(
		description=_("刚听到内容的当前词句（解释英文单词）"), 
		gestures=["kb(desktop):control+Windows+Numpad5", "kb(laptop):NVDA+shift+Windows+."])
	def script_currentSpokenWord(self, gesture):
		self.switchSpokenWord()

	@scriptHandler.script(
		description=_("刚听到内容的上一个词句"), 
		gestures=["kb(desktop):Control+Windows+Numpad4", "kb(laptop):NVDA+shift+Windows+LeftArrow"])
	def script_previousSpokenWord(self, gesture):
		self.switchSpokenWord(-1)

	@scriptHandler.script(
		description=_("刚听到内容的下一个字"), 
		gestures=["kb(desktop):Control+Windows+Numpad3", "kb(laptop):NVDA+Windows+RightArrow"])
	def script_nextSpokenChar(self, gesture):
		if not self.spoken: return
		p = segmentWord(self.spoken)[1]
		self.spoken_char += 1
		self.spoken_word = charPToWordP(p, self.spoken_char)
		l = len(self.spoken)
		if self.spoken_char >= l: 
			self.spoken_char = l-1
			beep(13500, 4)
		self.flg = 2
		speech.speakSpelling(self.spoken[self.spoken_char])




	@scriptHandler.script(
		description=_("刚听到内容的上一个字"), 
		gestures=["kb(desktop):Control+Windows+Numpad1", "kb(laptop):NVDA+Windows+LeftArrow"])
	def script_previousSpokenChar(self, gesture):
		if not self.spoken: return
		p = segmentWord(self.spoken)[1]
		self.spoken_char -= 1
		self.spoken_word = charPToWordP(p, self.spoken_char)
		if self.spoken_char < 0: 
			self.spoken_char = 0
			beep(13500, 4)
		self.flg = 2
		speech.speakSpelling(self.spoken[self.spoken_char])

	@scriptHandler.script(
		description=_("刚听到内容的当前字（双击解释）"), 
		gestures=["kb(desktop):Control+Windows+numpad2", "kb(laptop):NVDA+windows+."])
	def script_currentSpokenChar(self, gesture):
		if not self.spoken: return
		if self.spoken_char < 0: self.spoken_char = 0
		self.flg = 2
		self._charExplanation(self.spoken[self.spoken_char])

	@scriptHandler.script(
		description=_("剪贴板当前字（双击解释）"), 
		gestures=["kb(desktop):Control+Numpad2", "kb(laptop):NVDA+Alt+."])
	def script_currentChar(self, gesture):
		if self.line < 0: self.line = 0
		text = self.lines[self.line]
		if not text: return ui.message("空白")
		if self.char < 0: self.char = 0
		self._charExplanation(text[self.char])

	def _charExplanation(self, c):
		n = scriptHandler.getLastScriptRepeatCount()
		if n ==1:
			speech.speakSpelling(c, useCharacterDescriptions=True)
		elif n == 0:
			speech.speakSpelling(c)

	@scriptHandler.script(
		description=_("剪贴板上一个字"), 
		gestures=["kb(desktop):Control+Numpad1", "kb(laptop):NVDA+Alt+LeftArrow"])
	def script_previousChar(self, gesture):
		self._switchChar(-1)

	@scriptHandler.script(
		description=_("剪贴板下一个字"), 
		gestures=["kb(desktop):Control+Numpad3", "kb(laptop):NVDA+Alt+RightArrow"])
	def script_nextChar(self, gesture):
		self._switchChar(1)

	def _switchChar(self, d):
		if self.line < 0: self.line = 0
		text = self.lines[self.line]
		self.char += d
		l = len(text)
# 如果到了行首
		if self.char < 0:
# 且当前不是第一行
			if self.line > 0:
# 则切换到前一行
				self.line -= 1
				text = self.lines[self.line]
# 字符位置从这一行的行末开始
				self.char = len(text)-1
				words = segmentWord(text)[0]
				self.word =  len(words) - 1
			else: # 如果移动到了第一行的行首
				self.char = 0
			beep(12000, 6)
# 如果到了行尾
		elif self.char >= l:
# 且当前不是最后一行
			if self.line < len(self.lines)-1:
# 则切换到后一行
				self.line +=1
				text = self.lines[self.line]
# 字符位置从这一行的行首开始
				self.char = 0
				self.word = 0
			else: # 如果移动到了最后一行的行尾
				self.char = l-1
			beep(12000, 6)

		if text:
			p = segmentWord(text)[1]
			self.word = charPToWordP(p, self.char)
			speech.speakSpelling(text[self.char])
		else:
			ui.message("空白")

	def _switchWord(self, d=0):
		if self.line < 0: self.line = 0
		text = self.lines[self.line]
		words = segmentWord(text)[0]
		l = len(words)
		self.word += d
		f = False

# 如果是本行内最后一个单词
		if self.word >= l:
# 且不是最后一行
			if self.line < len(self.lines)-1:
# 则切换到下一行
				self.line+=1
				text = self.lines[self.line]
				words = segmentWord(text)[0]
				self.word = 0
#				self.char = text.find(words[self.word])-1
				f = True
			else: # 如果是最后一行，定位到最后一个单词
				self.word = l -1
			beep(13500, 4)
# 如果是本行内第一个单词
		elif self.word < 0 and d!=0:
# 且不是第一行
			if self.line > 0:
# 则切换到前一行
				self.line -= 1
				text = self.lines[self.line]
				words = segmentWord(text)[0]
				self.word = len(words)-1
#				self.char = text.rfind(words[self.word])-1
				f = True
# 如果是第一行，定位到第一个单词
			else:
				self.word = 0
			beep(13500, 4)

		p = segmentWord(text)[1]
#		self.spoken_word = charPToWordP(p, self.spoken_char)
		self.char = p[self.word]-1
#		self.char = text.find(words[self.word])-1
		word = words[self.word]
		ui.message(word)
		word = word.lower()
		if d == 0 and isAlpha(word):
			word = translateWord(self.Dict, word)
			if word: ui.message(word)

		if f: return
		if d ==1:
			i = text.find(words[self.word], self.char)-1
			self.char = i if i>-1 else self.char

		elif d == -1:
			i = text.rfind(words[self.word], 0, self.char)-1
			self.char = i if i>-1 else self.char

	@scriptHandler.script(
		description=_("剪贴板上一个词句"), 
		gestures=["kb(desktop):Control+Numpad4", "kb(laptop):NVDA+Shift+Alt+LeftArrow"])
	def script_previousWord(self, gesture):
		self._switchWord(-1)

	@scriptHandler.script(
		description=_("剪贴板下一个词句"), 
		gestures=["kb(desktop):Control+Numpad6", "kb(laptop):NVDA+Shift+Alt+RightArrow"])
	def script_nextWord(self, gesture):
		self._switchWord(1)

	@scriptHandler.script(
		description=_("剪贴板当前词句（解释英文单词）"), 
		gestures=["kb(desktop):Control+Numpad5", "kb(laptop):NVDA+Shift+Alt+."])
	def script_currentWord(self, gesture):
		self._switchWord(0)

	@scriptHandler.script(
		description=_("从剪贴板当前行向下朗读"), 
		gestures=["kb(desktop):Control+Numpad8", "kb(laptop):NVDA+Alt+l"])
	def script_fromCurrentLine(self, gesture):
		if self.line < 0: self.line = 0
		text = self.lines[self.line:]
		speech.speak(text)

	@scriptHandler.script(
		description=_("打开URL"), 
		gestures=["kb(desktop):control+numpadEnter", "kb(laptop):NVDA+Alt+Enter"])
	def script_openURL(self, gesture):
		if not (tryOpenURL(self.spoken) or tryOpenURL(self.text)):
			ui.message("未找到可供打开的 URL")

	@scriptHandler.script(
	description=_("读出时间，双击读日期"),
	gesture="kb:NVDA+f12")
	def script_speakDateTime(self, gesture):
		if scriptHandler.getLastScriptRepeatCount() > 0:
			ui.message(getDate())
		else:
			ui.message(getTime())

	@scriptHandler.script(
		description=_("朗读农历时间"), 
		gesture="kb:NVDA+f11")
	def script_speakLunarDate(self, gesture):
		if scriptHandler.getLastScriptRepeatCount() > 0:
			ui.message(getJq())
		else:
			ui.message(getLunar())

	@scriptHandler.script(
		description=_("编辑文档的字数统计"), 
		gestures=["kb(desktop):windows+numpaddelete", "kb(laptop):NVDA+alt+="])
	def script_editInfo(self, gesture):
		pos = api.getReviewPosition().copy()
		log.info(pos)
		if not ('_startOffset' in dir(pos) or '_rangeObj' in dir(pos)):
			ui.message("未获取到相关信息")
			return
		if '_startOffset' in dir(pos):
			pos._endOffset = 387419741
			pos._startOffset = pos._endOffset - 1
		else:
			pos._rangeObj.End = 387419741
			pos._rangeObj.Start = pos._rangeObj.End - 1
		formatField = textInfos.FormatField()
		for field in pos.getTextWithFields(constants.formatConfig):
			if isinstance(field, textInfos.FieldCommand) and isinstance(field.field, textInfos.FormatField):
				formatField.update(field.field)
		repeats = scriptHandler.getLastScriptRepeatCount()
		if repeats == 0:
			text = speech.getFormatFieldSpeech(formatField, formatConfig=constants.formatConfig) if formatField else None
			if text:
				text = "".join(text)
				if text.find(u"页") >= 0:
					text = text[1:text.find(u"页") + 1]
				else:
					text = text.replace(u"行", u"") + u"航"
				if '_startOffset' in dir(pos):
					pos._startOffset = 0
				else:
					pos._rangeObj.Start = 0
				i = len(pos.clipboardText.replace("\r", "").replace("\n", ""))
				ui.message(u"共" + text + str(i) + u"字")
			else:
				ui.message("此处不支持")

	@scriptHandler.script(
		description=_("编辑文档的当前光标位置"), 
		gestures=["kb(desktop):windows+NumPad5", "kb(laptop):NVDA+alt+\\"])
	def script_editCurrent(self, gesture):
		pos = api.getReviewPosition().copy()
		if not '_startOffset' in dir(pos) and not '_rangeObj' in dir(pos):
			ui.message(u"无法获取位置")
		pos2 = api.getReviewPosition().copy()
		pos.expand(textInfos.UNIT_LINE)
		pos.setEndPoint(pos2, "endToEnd")
		column = len(pos.clipboardText)
		pos.expand(textInfos.UNIT_LINE)
		formatField = textInfos.FormatField()
		for field in pos.getTextWithFields(constants.formatConfig):
			if isinstance(field, textInfos.FieldCommand) and isinstance(field.field, textInfos.FormatField):
				formatField.update(field.field)
		repeats = scriptHandler.getLastScriptRepeatCount()
		if repeats == 0:
			text = speech.getFormatFieldSpeech(formatField, formatConfig=constants.formatConfig) if formatField else None
			if text:
				text = "， ".join(text)
#				if text.find(u"页") > 0:
#					text = text[1:len(text)]
#				ui.message(u"" + text.replace(u" ", u"").replace(u"行", u"") + u"航" + str(column) + u"列")
				ui.message("{}，列{}".format(text, column))
			else:
				ui.message("此处不支持")

	@scriptHandler.script(
		description=_("编辑文档标记开始点"), 
		gestures=["kb(desktop):windows+Numpad4", "kb(laptop):NVDA+alt+["])
	def script_markStart(self, gesture):
		self.pt[api.getFocusObject().windowThreadID] = api.getReviewPosition().copy()  # i2=obj.windowHandle
		ui.message("选择开始点")

	@scriptHandler.script(
		description=_("编辑文档标记结束点"), 
		gestures=["kb(desktop):windows+NumPad6", "kb(laptop):NVDA+alt+]"])
	def script_markEnd(self, gesture):
		id = api.getFocusObject().windowThreadID
		pos = api.getReviewPosition().copy()
		try:
			# if not self.pt.has_key(id):
			if not id in self.pt.keys():
				pos.move(textInfos.UNIT_CHARACTER, -381419741, endPoint="start")
			else:
				ptp = self.pt[id]
				if pos.compareEndPoints(ptp, "endToEnd") == 0:
					ui.message("不支持选择")
					return
				if pos.compareEndPoints(ptp, "endToEnd") > 0:
					pos.setEndPoint(ptp, "startToStart")
				else:
					pos.setEndPoint(ptp, "endToEnd")
			api.getReviewPosition().obj._selectThenCopyRange = pos
			pos.updateSelection()
			ui.message("选择结束点")
		except:
			pass


	@scriptHandler.script(
		description=_("追加已选文字到剪贴板"), 
		gestures=["kb:NVDA+alt+A"])
	def script_AppendTextToClipboard(self, gesture):
		self.AppendTextToClipboard()


	def AppendTextToClipboard(self):
		# 过滤连续手势
		repeatCount =scriptHandler.getLastScriptRepeatCount()
		if repeatCount:
			return

		ClipboardText = ""
		SelectedText = ""
		ResultText = ""
		info = ""

		obj=api.getFocusObject()
		treeInterceptor=obj.treeInterceptor
		if hasattr(treeInterceptor,'TextInfo') and not treeInterceptor.passThrough:
			obj=treeInterceptor
		try:
			info=obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info=None
		if not info or info.isCollapsed:
			ui.message("未选择文本")
			return
		else:
			SelectedText = info.text

		# 获取剪贴板文本
		try:
			ClipboardText = api.getClipData()
		except:
			api.copyToClip(SelectedText)
			ui.message("拷贝")
			return

		# 拼接要复制的文本
		ResultText = ClipboardText + "\n" + SelectedText
		try:
			api.copyToClip(ResultText)
			ui.message("已追加")
		except:
			ui.message("追加失败")


	def terminate(self):
		self.monitor.Stop()
		speech.speak = self.oldSpeak
		if self.editor:
			self.editor.isExit = True
			self.editor.Destroy()
		super().terminate()

	@scriptHandler.script(
		description=_("粘贴刚听到的内容"), 
		gestures=["kb:NVDA+`"])
	def script_pasteLastSpoken(self, gesture):
		self.monitor.work = False
		api.copyToClip(self.spoken.rstrip("\r\n"))
		KeyboardInputGesture.fromName("control+v").send()
		Thread(target = pasteBack, args=(self,)).start()
