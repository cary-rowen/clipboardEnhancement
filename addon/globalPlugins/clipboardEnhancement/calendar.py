from datetime import datetime as dt
from . import constants

def getTime():
	d = dt.today()
	return '{}点{}分{}秒'.format(d.hour, d.minute, d.second)

def getDate(d=None):
	if d is None:
		d = dt.today()
	w = ''.join(('星期', constants.WEEK[int(d.strftime('%w'))]))
	wth = ''.join(('第', d.strftime('%W'), '周'))
	return '{}年{}月{}日， {}， {}'.format(d.year, d.month, d.day, w, wth)

def ymd(yy, dd):
	di = constants.DS[yy - 1900]
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
			return s + constants.MN[i] + u"月" + constants.DN[int(dd)]

def md(yy, mm, dd, ys=False):
	if yy % 4 == 0 and (yy % 100 != 0 or yy % 400 == 0):
		dd += constants.M2[mm]
	else:
		dd += constants.M1[mm]
	sp = constants.DS[yy - 1900] & 63
	s = (((u"" + constants.CY1[(yy - 184) % 10] + constants.CY2[(yy - 184) % 12]) if dd >= sp else (
			u"" + constants.CY1[(yy - 185) % 10] + constants.CY2[(yy - 185) % 12])) + u"年") if ys else u""
	if dd >= sp:
		return s + ymd(yy, dd - sp)
	else:
		yy2 = yy - 1
		sp = constants.DS[yy2 - 1900] & 63
		dd += constants.M2[12] if yy2 % 4 == 0 and (yy2 % 100 != 0 or yy2 % 400 == 0) else constants.M1[12]
		return s + ymd(yy2, dd - sp)

def jq(yy, mm, dd):
	if yy <= 2000:
		return u""
	yy -= 2000
	i = mm * 2 + (-2 if dd <= 15 else -1)
	r = yy / 4 if i > 1 else (yy - 1) / 4
	d = int(yy * 0.2422 + constants.C[i]) - r - 1
	if i < 0:
		i += 24
	if (yy + 2000) * 100 + i in constants.E.keys():
		d += constants.E[(yy + 2000) * 100 + i]
	if d == dd:
		return u" 今日" + constants.JQN[i]
	elif d == dd - 1:
		return u" 昨日" + constants.JQN[i]
	elif d == dd + 1:
		return u" 明日" + constants.JQN[i]
	return u""

def jq2(yy, mm, dd):
	if yy <= 2000:
		return u""
	yy -= 2000
	i = mm * 2 + (-2 if dd <= 15 else -1)
	r = yy / 4 if i > 1 else (yy - 1) / 4
	d = int(yy * 0.2422 + constants.C[i]) - r - 1
	if i < 0:
		i += 24
	if (yy + 2000) * 100 + i in constants.E.keys():
		d += constants.E[(yy + 2000) * 100 + i]
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
		d2 = int(yy2 * 0.2422 + constants.C[i2]) - r2 - 1
		if i2 < 0:
			i2 += 24
		if (yy2 + 2000) * 100 + i2 in constants.E.keys():
			d2 += constants.E[(yy2 + 2000) * 100 + i2]
		return md(yy + 2000, mm, d+1) + constants.JQN[i] + md(yy2 + 2000, mm2, d2+1) + constants.JQN[i2]
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
		d2 = int(yy2 * 0.2422 + constants.C[i2]) - r2 - 1
		if i2 < 0:
			i2 += 24
		if (yy2 + 2000) * 100 + i2 in constants.E.keys():
			d2 += constants.e[(yy2 + 2000) * 100 + i2]
		return md(yy2 + 2000, mm2, d2+1) + constants.JQN[i2] + md(yy + 2000, mm, d+1) + constants.JQN[i]

def getLunar():
	d = dt.today()
	yy, mm, dd = d.year, d.month, d.day
	if yy < 1900 or yy > 2100:
		return u""
	return md(yy, mm - 1, dd - 1, True) + jq(yy, mm-1 , dd-1)

def getJq():
	d = dt.today()
	return jq2(d.year, d.month-1, d.day-1)

