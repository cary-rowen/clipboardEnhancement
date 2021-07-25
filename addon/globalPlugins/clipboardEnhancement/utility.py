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

def getTime():
	d = dt.today()
	return '{}点{}分{}秒'.format(d.hour, d.minute, d.second)

week = '日一二三四五六'
def getDate(d=None):
	if d is None:
		d = dt.today()
	w = ''.join(('星期', week[int(d.strftime('%w'))]))
	wth = ''.join(('第', d.strftime('%W'), '周'))
	return '{}年{}月{}日， {}， {}'.format(d.year, d.month, d.day, w, wth)

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
# ******
p1 = re.compile(u"[一-龥！-｠–—‘’“”…、-〃〈-〗]|[a-zA-Z]+|[0-9]+|[,\.\?\!\:\"\'@\~\#\$\%\^\&\*\(\)\+\-\/\\\<\>_]+")
p2 = re.compile(
	u"([一-龥！-｠–—‘’“”…、-〃〈-〗]|[a-zA-Z]+|[0-9]+|[,.?\!\:\"\'@\~\#\$\%\^\&\*\(\)\+\-\/\\\<\>_]+)[^一-龥！-｠–—‘’“”…、-〃〈-〗\w,\.\?\!\:\"\'@\~\#\$\%\^\&\*\(\)\+\-\/\\\<\>]*$")
p3 = re.compile(
	u"(((https?|ftp):\/\/([\w-]+\.)*)|((www|bbs)\.))[\w-]+\.[a-zA-Z]{2,6}(\/[\w\&%\.-~]+)*(\?[\w\&%\.-~\?]+)?")
wk = u"日一二三四五六"
ds = [5982750, 1919025, 3839014, 5843292, 1649710, 2780194, 5593368, 1419307, 2974752, 6113429, 1919016, 7116189,
	  2921520, 2698276, 5418329, 2798636, 1419298, 2991254, 3580969, 7752159, 3557426, 3445798, 6894939, 2709550,
	  710691, 5690647, 1789995, 3843104, 8013974, 3819560, 3447197, 1354799, 2710564, 4905305, 2975788, 1789986,
	  3876055, 1909801, 5918174, 2772017, 1354790, 2715034, 2798637, 1419299, 7165208, 3051563, 2958368, 6966421,
	  2774056, 5551580, 1366063, 2798628, 5679450, 1493036, 3576865, 7669975, 3483690, 2774558, 2776112, 1398822,
	  2807195, 2839597, 1787939, 3839256, 3839019, 1648672, 3300564, 2780199, 5597661, 1419311, 2991140, 6113626,
	  2967597, 2921505, 5844246, 2698281, 5418526, 701488, 1422373, 2991515, 3580974, 3557411, 7640344, 3445803,
	  6895264, 2709554, 710695, 1496476, 1791023, 3875876, 8014170, 3819565, 3446818, 2709718, 2710568, 5462558, 878641,
	  1791013, 5973339, 1909806, 1723427, 5549335, 1354794, 2714655, 5597333, 1419303, 7165404, 3051568, 2958373,
	  6966617, 2774060, 1356833, 2798870, 2798632, 5679710, 1525809, 3576870, 7678363, 3483694, 3298339, 5552408,
	  1398826, 2806815, 5687445, 1787944, 3843484, 1872943, 1649700, 3300697, 3320875, 1402913, 2840790, 2991145,
	  5589726, 2967601, 2921510, 6892955, 2698285, 1223714, 1404247, 1487914, 2992159, 7162005, 3557416, 7640541,
	  3445807, 2708516, 5420377, 1234988, 1496096, 3582166, 3875881, 8014367, 3819569, 3446822, 2709915, 2710573,
	  1398818, 1791255, 1922090, 1909792, 3820756, 1723431, 5549532, 1354799, 617507, 5597529, 1419308, 889889, 6105366,
	  2959401, 6968862, 2774065, 1356837, 2799002, 2806829, 1484835, 3052823, 1479722, 3483680, 7492821, 3299367,
	  6633948, 1398831, 2806820, 5687641, 1787948, 3839009, 3746071, 1715240, 3300893, 1223728, 1403941, 2840986,
	  2992173, 1919011, 6067480, 2954282, 2763807, 5401748, 1223719]
mn = u"正二三四五六七八九十冬腊"
dn = [u"初一", u"初二", u"初三", u"初四", u"初五", u"初六", u"初七", u"初八", u"初九", u"初十", u"十一", u"十二", u"十三", u"十四", u"十五", u"十六",
	  u"十七", u"十八", u"十九", u"二十", u"二十一", u"二十二", u"二十三", u"二十四", u"二十五", u"二十六", u"二十七", u"二十八", u"二十九", u"三十"]
m1 = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
m2 = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366]
jqn = [u"立春", u"雨水", u"惊蛰", u"春分", u"清明", u"谷雨", u"立夏", u"小满", u"芒种", u"夏至", u"小暑", u"大暑", u"立秋", u"处暑", u"白露", u"秋分",
	   u"寒露", u"霜降", u"立冬", u"小雪", u"大雪", u"冬至", u"小寒", u"大寒"]
e = {202601: -1, 208403: 1, 200807: 1, 201610: 1, 200212: 1, 208917: 1, 208918: 1, 202121: -1, 201922: -1, 208223: 1}
formatConfig = {
	"detectFormatAfterCursor": True,
	"reportFontName": False,
	"reportFontSize": False,
	"reportFontAttributes": False,
	"reportColor": False,
	"reportRevisions": False,
	"reportEmphasis": False,
	"reportStyle": False,
	"reportAlignment": False,
	"reportSpellingErrors": False,
	"reportGrammarErrors": False,
	"reportPage": True,
	"reportLineNumber": True,
	"reportParagraphIndentation": False,
	"reportTables": False,
	"reportLinks": False,
	"reportHeadings": False,
	"reportLists": False,
	"reportBlockQuotes": False,
	"reportComments": False,
	"reportLineSpacing": False,
	"reportBorderStyle": False,
}
c = [3.87, 18.73, 5.63, 20.646, 4.81, 20.1, 5.52, 21.04, 5.678, 21.37, 7.108, 22.83, 7.5, 23.13, 7.646, 23.042, 8.318,
	 23.438, 7.438, 22.36, 7.18, 21.94, 5.4055, 20.12]
cy1 = u"甲乙丙丁戊己庚辛壬癸"
cy2 = u"子丑寅卯辰巳午未申酉戌亥"


def ymd(yy, dd):
	di = ds[yy - 1900]
	for i in range(10, 23):
		dm = 30 if di & pow(2, i) > 0 else 29
		if dd >= dm:
			dd -= dm
		else:
			i -= 10
			rm = (di & 960) / 64
			s = u""
			if rm > 0:
				if rm < i:
					i -= 1
				elif rm == i:
					i -= 1
					s += u"闰"
			return s + mn[i] + u"月" + dn[int(dd)]


def md(yy, mm, dd, ys=False):
	if yy % 4 == 0 and (yy % 100 != 0 or yy % 400 == 0):
		dd += m2[mm]
	else:
		dd += m1[mm]
	sp = ds[yy - 1900] & 63
	s = (((u"" + cy1[(yy - 184) % 10] + cy2[(yy - 184) % 12]) if dd >= sp else (
			u"" + cy1[(yy - 185) % 10] + cy2[(yy - 185) % 12])) + u"年") if ys else u""
	if dd >= sp:
		return s + ymd(yy, dd - sp)
	else:
		yy2 = yy - 1
		sp = ds[yy2 - 1900] & 63
		dd += m2[12] if yy2 % 4 == 0 and (yy2 % 100 != 0 or yy2 % 400 == 0) else m1[12]
		return s + ymd(yy2, dd - sp)


def jq(yy, mm, dd):
	if yy <= 2000:
		return u""
	yy -= 2000
	i = mm * 2 + (-2 if dd <= 15 else -1)
	r = yy / 4 if i > 1 else (yy - 1) / 4
	d = int(yy * 0.2422 + c[i]) - r - 1
	if i < 0:
		i += 24
	if (yy + 2000) * 100 + i in e.keys():
		d += e[(yy + 2000) * 100 + i]
	if d == dd:
		return u" 今日" + jqn[i]
	elif d == dd - 1:
		return u" 昨日" + jqn[i]
	elif d == dd + 1:
		return u" 明日" + jqn[i]
	return u""

def jq2(yy, mm, dd):
	if yy <= 2000:
		return u""
	yy -= 2000
	i = mm * 2 + (-2 if dd <= 15 else -1)
	r = yy / 4 if i > 1 else (yy - 1) / 4
	d = int(yy * 0.2422 + c[i]) - r - 1
	if i < 0:
		i += 24
	if (yy + 2000) * 100 + i in e.keys():
		d += e[(yy + 2000) * 100 + i]
	if d <= dd:
		if i % 2 == 0:
			i2 = i + 1
			yy2 = yy
			mm2 = mm
		elif i == 21:
			i2 = 22
			yy2 = yy + 1
			mm2 = 0
		else:
			i2 = i + 1 if i < 23 else 0
			yy2 = yy
			mm2 = mm + 1
		r2 = yy2 / 4 if 1 < i2 < 22 else (yy2 - 1) / 4
		d2 = int(yy2 * 0.2422 + c[i2]) - r2 - 1
		if i2 < 0:
			i2 += 24
		if (yy2 + 2000) * 100 + i2 in e.keys():
			d2 += e[(yy2 + 2000) * 100 + i2]
		return md(yy + 2000, mm, d) + jqn[i] + md(yy2 + 2000, mm2, d2) + jqn[i2]
	else:
		if i % 2 == 1:
			i2 = i - 1
			yy2 = yy
			mm2 = mm
		elif i == 22:
			i2 = 21
			yy2 = yy - 1
			mm2 = 11
		else:
			i2 = i - 1 if i > 0 else 23
			yy2 = yy
			mm2 = mm - 1
		r2 = yy2 / 4 if i2 > 1 and i2 < 22 else (yy2 - 1) / 4
		d2 = int(yy2 * 0.2422 + c[i2]) - r2 - 1
		if i2 < 0:
			i2 += 24
		if (yy2 + 2000) * 100 + i2 in e.keys():
			d2 += e[(yy2 + 2000) * 100 + i2]
		return md(yy2 + 2000, mm2, d2) + jqn[i2] + md(yy + 2000, mm, d) + jqn[i]

def getLunar():
	d = dt.today()
	yy, mm, dd = d.year, d.month, d.day
	if yy < 1900 or yy > 2100:
		return u""
	return md(yy, mm - 1, dd - 1, True) + jq(yy, mm - 1, dd - 1)

def getJq():
	d = dt.today()
	return jq2(d.year, d.month-1, d.day-1)



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
