import api
import wx
import os
import re
from . import reReplace
class MyFrame(wx.Frame):
	def __init__(self, *args, **kw):
		wx.Frame.__init__(self, *args, size=(600,460), **kw)
		self.isExit = False
		pnl = wx.Panel(self)
		self.edit = wx.TextCtrl(pnl, pos=(0, 0), style=wx.TE_PROCESS_TAB|wx.TE_MULTILINE|wx.TE_RICH2)
		menubar = wx.MenuBar()
		menu = wx.Menu()
		menu.Append(wx.ID_OPEN, '打开(&O)\tCtrl+O', '更新剪贴板数据')
		update = menu.Append(-1, '更新(&U)\tAlt+U')
		menu.Append(wx.ID_SAVE, '更新并关闭(&X)\tAlt+X')
		menu.Append(wx.ID_SAVEAS, '另存为(&A)\tAlt+A', '保存项目')
		menu.Append(wx.ID_EXIT, '关闭(&Q)\tAlt+Q', '退出程序')
		self.edit.Bind(wx.EVT_KEY_DOWN, self.OnKeydown)
		self.Bind(wx.EVT_MENU, self.OnOpen, id=wx.ID_OPEN)
		self.Bind(wx.EVT_MENU, self.OnUpdate, update)
		self.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
		self.Bind(wx.EVT_MENU, self.OnSaveAs, id=wx.ID_SAVEAS)
		self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
		menubar.Append(menu, '文件(&F)')
		menu2 = wx.Menu()
		find = menu2.Append(-1, '查找(&F)\tCtrl+F')
		self.Bind(wx.EVT_MENU, self.OnShowFind, find)
		replace = menu2.Append(-1, '替换(&H)\tCtrl+H')
		self.Bind(wx.EVT_MENU,self.OnShowReplace, replace)
		next = menu2.Append(-1, '查找下一个\tF3')
		self.Bind(wx.EVT_MENU, self.OnNext, next)
		goto = menu2.Append(-1, '转到(&G)\tCtrl+G')
		self.Bind(wx.EVT_MENU, self.OnGoto, goto)
		r=menu2.Append(-1, '正则替换(&R)\tCtrl+R')
		self.Bind(wx.EVT_MENU, self.OnRe, r)
		menubar.Append(menu2, '编辑(&E)')
		self.SetMenuBar(menubar)
		self.finddata = wx.FindReplaceData(wx.FR_DOWN)
		self.edit.SetFont(wx.FFont(7, wx.DEFAULT, wx.NORMAL))
		self.Bind(wx.EVT_SIZE, self.OnSize)
	def OnKeydown(self, evt):
		code = evt.GetKeyCode()
		if code == wx.WXK_ESCAPE:
			self.Show(False)
		evt.Skip()

	def OnUpdate(self, evt):
		text = self.edit.GetValue()
		if not text:
			self.clearClipboard()
		else:
			api.copyToClip(text)

	def OnRe(self, evt):
		dlg = ReReplace.ReDialog(self)
		if dlg.ShowModal() == wx.ID_OK:
			pattern = dlg.cb.GetValue()
			aim = dlg.cb2.GetValue()
			self.edit.SetValue(re.sub(pattern, aim, self.edit.GetValue()))
			self.SaveHistory(pattern, aim)
		dlg.Destroy()
	def SaveHistory(self, pattern, aim):
		pass
	def OnNext(self, e):
		if not self.finddata.GetFindString():
			self.OnShowFind(wx.EVT_MENU)
		else:
			self.OnFind(wx.EVT_FIND)
	def OnShowFind(self, event):
		dlg = wx.FindReplaceDialog(self, self.finddata, '查找')
		dlg.Bind(wx.EVT_FIND, self.OnFind)
		dlg.Bind(wx.EVT_FIND_NEXT, self.OnFind)
		dlg.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
		dlg.Show()
	def OnShowReplace(self, event):
		dlg = wx.FindReplaceDialog(self, self.finddata, '替换', wx.FR_REPLACEDIALOG)
		dlg.Bind(wx.EVT_FIND, self.OnFind)
		dlg.Bind(wx.EVT_FIND_REPLACE, self.OnReplace)
		dlg.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnReplaceAll)
		dlg.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
		dlg.Show()
	def OnFind(self, event):
		findtext = self.finddata.GetFindString()
		offset = self.edit.GetInsertionPoint()
		if self.finddata.GetFlags() & wx.FR_DOWN:
			if self.edit.GetStringSelection().lower()==findtext.lower():
				offset+=len(findtext)
			aimtext=self.edit.GetRange(offset, self.edit.GetLastPosition())
			if not self.finddata.GetFlags() & wx.FR_MATCHCASE:
				m= re.search(findtext, aimtext, re.I)
				if m:
					start = m.span()[0]
				else:
					start=-1
			else:
				start = aimtext.find(findtext)
		else:
			aimtext = self.edit.GetRange(0, offset)
			if not self.finddata.GetFlags() & wx.FR_MATCHCASE:
				m= re.findall(findtext, aimtext, re.I)
				if m:
					findtext = m[-1]
			start = aimtext.rfind(findtext)
		if start > -1:
			start += offset if self.finddata.GetFlags()&wx.FR_DOWN else 0
			self.edit.SetSelection(start, start+len(findtext))
		else:
			wx.MessageBox('找不到\"{}\"'.format(findtext), '提示')
	def OnReplace(self, event):
		findtext = self.finddata.GetFindString()
		replacetext = self.finddata.GetReplaceString()
		offset = self.edit.GetInsertionPoint()
		text = self.edit.GetRange(offset, self.edit.GetLastPosition())
		if not self.finddata.GetFlags() & wx.FR_MATCHCASE:
			m = re.search(findtext, text, re.I)
			start = m.span()[0] if m else -1
		else:
			start = text.find(findtext)
		if start > -1:
			start += offset
			self.edit.Replace(start, start+len(findtext), replacetext)
	def OnReplaceAll(self, event):
		findtext = self.finddata.GetFindString()
		replacetext = self.finddata.GetReplaceString()
		offset = 0
		if not self.finddata.GetFlags() & wx.FR_MATCHCASE:
			while True:
				text = self.edit.GetRange(offset, self.edit.GetLastPosition())
				m = re.search(findtext, text, re.I)
				start = m.span()[0] if m else -1
				if start == -1:
					break
				start += offset 
				self.edit.Replace(start, start+len(findtext), replacetext)
				offset = self.edit.GetInsertionPoint()
			return
		while True:
			text = self.edit.GetRange(offset, self.edit.GetLastPosition())
			start = text.find(findtext)
			if start == -1:
				break
			start += offset 
			self.edit.Replace(start, start+len(findtext), replacetext)
			offset = self.edit.GetInsertionPoint()
	def OnFindClose(self, event):
		event.GetDialog().Destroy()
	def OnGoto(self, event):
		line = self.edit.PositionToXY(self.edit.GetInsertionPoint())[2]
		dlg = wx.NumberEntryDialog(self, '', '行号(&L)', '转到指定行', line+1, 1, self.edit.GetNumberOfLines())
		if dlg.ShowModal() == wx.ID_OK:
			point = self.edit.XYToPosition(0, dlg.GetValue()-1)
			self.edit.SetInsertionPoint(point)
	def OnOpen(self, event):
		wildcard = 'txt文件(*.txt)|*.txt|' \
			'所有文件 (*.*)|*.*'
		filename = ''
		dlg = wx.FileDialog(self, message='选择一个文件', defaultDir='', defaultFile="", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
		dlg.Destroy()
		if not filename:
			return
		try:
			with open(filename) as f:
				self.edit.SetValue(f.read())
		except Exception as e:
			try:
				with open(filename, encoding = 'utf-8') as f:
					self.edit.SetValue(f.read())
			except Exception as e:
				wx.MessageBox(str(e), '错误')
		self.OpenFile(ext)
	def Destroy(self):
		if not self.isExit:
			self.Show(False)
			return 0
		else:
			return super().Destroy()

	def OnSaveAs(self, evt):
		text = self.edit.GetValue()
		wildcard = '文本文件 (*.txt)|*.txt|' \
			'所有文件 (*.*)|*.*'
		filepath = ''
		dlg = wx.FileDialog(self, message='文件另存为...', defaultDir='', defaultFile='', wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			filepath = dlg.GetPath()
		dlg.Destroy()
		if not filepath:
			return
		with open(filepath, 'wb') as f:
			f.write(text.encode('utf8'))

	def OnSave(self, event):
		text = self.edit.GetValue()
		if not text:
			self.clearClipboard()
		else:
			api.copyToClip(text)
		self.Destroy()

	def saveFile(self, filename, text):
		wildcard = '文本文件 (*.txt)|*.txt|' \
			'所有文件 (*.*)|*.*'
		filepath = ''
		dlg = wx.FileDialog(self, message='文件另存为...', defaultDir='', defaultFile=filename, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			filepath = dlg.GetPath()
		dlg.Destroy()
		if not filepath:
			return
		with open(filepath, 'wb') as f:
			f.write(text.encode('utf8'))
		self.SetTitle('-'.join((os.path.basename(filepath), self.name)))
		if self.filename and not self.edit.IsModified():
			self.CheckLatest100()
		self.filename = filepath
		self.mark= []
		self.index = -1
		self.edit.DiscardEdits()
	def OnExit(self, event):
		self.Show(False)
	def OnSize(self, event):
		self.edit.SetSize(self.GetClientSize())
		event.Skip()


	# 清空剪贴板
	def clearClipboard(self):
		import winUser
		with winUser.openClipboard():
			winUser.emptyClipboard()
