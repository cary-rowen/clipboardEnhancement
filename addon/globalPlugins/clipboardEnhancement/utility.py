import api
from api import copyToClip
from ui import message
from os.path import basename, join, dirname, isfile, getsize
import re
import webbrowser
from datetime import datetime as dt
from json import loads
from threading import Thread
from ctypes import windll, WINFUNCTYPE, c_int, c_void_p, c_buffer, sizeof, wstring_at
import ctypes.wintypes as w
import sys
from os import walk
from winsound import PlaySound, SND_FILENAME, SND_ASYNC
from time import sleep

def fileLists(files):
	l = len(files)
	for i in range(l):
		yield f'{basename(files[i])}, 第{i+1}之{l}项， {files[i]}'

m = re.compile(r"[\u4e00-\uf95a]+|[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z])|[0-9]+|[A-Z]+(?![A-Z])")
def segmentWord(text):
	words = []
	positions = []
	for word in m.finditer(text):
		start = word.start()
		end = word.end()
		words.append(word.string[start:end])
		positions.append(start)
	if not words:
		words.append(text)
		positions.append(0)
	return words, positions

def charPToWordP(word_P, char_P):
	temp_Char =0
	for i in range(len(word_P)):
		if i==len(word_P)-1 and char_P>=word_P[i]:
			temp_Char=i
			break
		if char_P >= word_P[i] and char_P < word_P[i+1]:
			temp_Char=i
			break
	return temp_Char


def isAlpha(text):
	for c in text:
		o = ord(c)
		if not (97<=o<=122): return False
	return True

def loadJson():
	with open(join(dirname(__file__), 'Dict.json')) as f:
		Dict_Json = loads(f.read())
	return Dict_Json

def translateWord(dict, word):
	result = dict.get(word, dict.get(re.sub('(ing|ed|s)$', '', word)))
	return result

_pattern_URL = re.compile(r'(https?|ftp|nvdaremote|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]')
def tryOpenURL(text: str) -> bool:
	if not isinstance(text, str):
		return False
	match = _pattern_URL.search(text)
	if match:
		return webbrowser.open(match.group(0))
	return False

CF_UNICODETEXT = 0xD
CF_HDROP = 0xF
CF_UPDATE = 0x031d
PASTED = 0x7ffe
u32 = windll.user32
k32 = windll.kernel32
s32 = windll.shell32

OpenClipboard = u32.OpenClipboard
OpenClipboard.argtypes = w.HWND,
OpenClipboard.restype = w.BOOL
GetClipboardData = u32.GetClipboardData
GetClipboardData.argtypes = w.UINT,
GetClipboardData.restype = w.HANDLE
GlobalLock = k32.GlobalLock
GlobalLock.argtypes = w.HGLOBAL,
GlobalLock.restype = w.LPVOID
GlobalUnlock = k32.GlobalUnlock
GlobalUnlock.argtypes = w.HGLOBAL,
GlobalUnlock.restype = w.BOOL
CloseClipboard = u32.CloseClipboard
CloseClipboard.argtypes = None
CloseClipboard.restype = w.BOOL
DragQueryFile = s32.DragQueryFile
DragQueryFile.argtypes = [w.HANDLE, w.UINT, c_void_p, w.UINT]

class ClipboardMonitor:
	SOUND = join(dirname(__file__), 'Copy.wav')

	def __init__(self, handle=None):
		self.handle = handle
		self.__pre_handle = 0
		self.work = True
		self.__mhf = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int)(self.MsgHandleFunc)
		self.data = None

	def customization(self):
		pass

	def getData(self):
		return self.data

	def workReset(self):
		sleep(0.1)
		self.work = True

	def MsgHandleFunc(self, hwnd, msg, wParam, lParam):
		if msg == PASTED:
			self.work = True
		elif msg == CF_UPDATE and self.work:
			self.work = False
			Thread(target=ClipboardMonitor.workReset, args=(self,)).start()
			Thread(target=ClipboardMonitor.get_clipboard_data, args=(self,)).start()
			PlaySound(self.SOUND, SND_FILENAME|SND_ASYNC)
		return windll.user32.CallWindowProcA(self.__pre_handle, hwnd, msg, wParam, lParam)

	def StartMonitor(self):
		u32.AddClipboardFormatListener(self.handle)
		self.__pre_handle = windll.user32.SetWindowLongA(self.handle, -4, self.__mhf)

	def Stop(self):
		u32.RemoveClipboardFormatListener(self.handle)
		self.__pre_handle = windll.user32.SetWindowLongA(self.handle, -4, 0)

	def get_clipboard_data(self):
		if not OpenClipboard(self.handle): return
		formats = []
		n = 0
		while True:
			n = windll.user32.EnumClipboardFormats(n)
			if n ==0: break
			formats.append(n)
		CloseClipboard()
		if 13 in formats:
			try:
				self.data = self.get_clip_text()
			except:
				self.data = None
		elif 15 in formats:
			try:
				self.data = self.get_clip_file_list()
			except:
				self.data = None
		elif 2 in formats:
			self.data = b''
		else:
			self.data = None
		self.customization()

	def get_clip_text(self):
		text = ""
		if not OpenClipboard(self.handle): return None
		h_clip_mem = GetClipboardData(CF_UNICODETEXT)
		text = wstring_at(GlobalLock(h_clip_mem))
		GlobalUnlock(h_clip_mem)
		CloseClipboard()
		return text

	def get_clip_file_list(self):
		files = []
		if not OpenClipboard(self.handle): return None
		h_hdrop = GetClipboardData(CF_HDROP)
		if not h_hdrop: return
		FS_ENCODING = sys.getfilesystemencoding()
		file_count = DragQueryFile(h_hdrop, -1, None, 0)
		for index in range(file_count):
			buf = c_buffer(260)
			DragQueryFile(h_hdrop, index, buf, sizeof(buf))
			try:
				files.append(buf.value.decode('gbk'))
			except:
				try:
					files.append(buf.value.decode(FS_ENCODING))
				except:
					files = None
		CloseClipboard()
		return files

	def calc(self, files):
		size=f = d = 0
		for i in files:
			if isfile(i):
				f+=1
				size+=getsize(i)
			else:
				d+=1
				for root, dd, ff in walk(i):
					for n in ff:
						size += getsize(join(root,n))
		t = '{}个文件夹,'.format(d) if d else ''
		t1=f'{f}个文件' if f else ''
		size = self.convert(size)
		return t+t1+'共{}'.format(size)

	def convert(self, s):
		if s<1024: return f'{s}字节'
		for i in ('KB', 'MB', 'GB'):
			s= s/1024
			if s<1024: return str(round(s, 2))+i
		return str(round(s, 2))+i

def pasteBack(obj):
	sleep(0.1)
	j = 0
	while j <10:
		try:
			copyToClip(obj.text)
			obj.flg = 0
			message(obj.spoken.rstrip('\r\n'))
			break
		except:
			j += 1
			sleep(0.05)
	windll.user32.PostMessageW(obj.editor.GetHandle(), PASTED, 0, 0)