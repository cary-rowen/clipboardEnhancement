import time

from . import constants, sxtwl


def getTime():
	d = time.localtime()
	return f'{d.tm_hour}点{d.tm_min}分{d.tm_sec}秒'


def getDate():
	d = time.localtime()
	return f'{d.tm_year}年{d.tm_mon}月{d.tm_mday}日,星期{constants.WeekCn[d.tm_wday]}, 第{d.tm_yday}天'


def get_jieqi_time(day):
	# 当日是否有节气
	if day.hasJieQi():
		# 获取节气的儒略日数
		jd = day.getJieQiJD()
		# 将儒略日数转换成年月日时秒
		t = sxtwl.JD2DD(jd)
		# 注意，t.s是小数，需要四舍五入
		tt = "时刻:%d:%d:%d" % (t.h, t.m, round(t.s))
		return f'今日{constants.jqmc[day.getJieQi()]}, {tt}'
	else:
		for i in range(2, 32):
			day = day.before(1)
			if day.hasJieQi():
				jq = constants.jqmc[day.getJieQi()]
				return f'{jq}第{i}天'


def get_lunar_month_days(day):
	# 一个农历月的天数
	year = day.getLunarYear(False)
	month = day.getLunarMonth()
	isRun = True if day.isLunarLeap() else False
	daynum = sxtwl.getLunarMonthNum(year, month, isRun)
	r = '小' if daynum < 30 else '大'
	return '%s%s月%s' % ("闰" if isRun else "", constants.Ymc[day.getLunarMonth()], r)


def get_lunar_date(day):
	# 以立春为界的农历
	s = "%s%s月%s" % (  # day.getLunarYear(False),
		'闰' if day.isLunarLeap() else '', constants.Ymc[day.getLunarMonth()], constants.rmc[day.getLunarDay() - 1])
	return s


def get_gz(day, tm):
	# 以立春为界的天干地支 （注，如果没有传参，或者传false，是以立春为界的。刚好和getLunarYear相反）
	yTG = day.getYearGZ()
	# 年干支
	ygz = constants.Gan[yTG.tg] + constants.Zhi[yTG.dz]
	shx = "生肖:" + constants.ShX[yTG.dz]
	# 月干支
	mTG = day.getMonthGZ()
	mgz = constants.Gan[mTG.tg] + constants.Zhi[mTG.dz]
	# 日干支
	dTG = day.getDayGZ()
	dgz = constants.Gan[dTG.tg] + constants.Zhi[dTG.dz]
	# 时干支,传24小时制的时间，分早晚子时
	hour = tm.tm_hour
	sTG = day.getHourGZ(hour)
	sgz = constants.Gan[sTG.tg] + constants.Zhi[sTG.dz]
	return f'{ygz}年,{mgz}月,{dgz}日,{sgz}时。\n{shx}'


def get_jieqi_before(day):
	while True:
		day = day.before(1)
		# hasJieQi的接口比getJieQiJD速度要快，你也可以使用getJieQiJD来判断是否有节气。
		if day.hasJieQi():
			jq = constants.jqmc[day.getJieQi()]
			jqDay = '农历' + get_lunar_date(day)
			return f'{day.getSolarMonth()}月{day.getSolarDay()}日  {jq}, {jqDay}'


def get_jieqi_after(day):
	while True:
		day = day.after(1)
		if day.hasJieQi():
			jq = constants.jqmc[day.getJieQi()]
			jqDay = '农历' + get_lunar_date(day)
			return f'{day.getSolarMonth()}月{day.getSolarDay()}日  {jq}, {jqDay}'


'''
1.获取某日的前几天或者后几天的信息 （可以用到很多场景中）
# 获取某天的后面几天
num = 1    #你喜欢写多少天 也多少天，可以写负数，相当于往前
day = day.after(num)  #获取num天后的日信息
s = "公历:%d年%d月%d日" % (day.getSolarYear(), day.getSolarMonth(), day.getSolarDay())
print(s)
# 同上
day = day.before(num)
s = "公历:%d年%d月%d日" % (day.getSolarYear(), day.getSolarMonth(), day.getSolarDay())
print(s)
1.获取一年中的闰月
# 获取一年中的闰月
year = 2020
month = sxtwl.getRunMonth(year)
if month >= 0:
    print("%d年的闰月是%d"%(year, month) )
else:
    print("没有闰月")
1.获取一个农历月的天数
# 一个农历月的天数
year = 2020 #农历年
month  = 4 #农历月
isRun = False #是否是闰月
daynum = sxtwl.getLunarMonthNum(year, month, isRun)
print("农历%d年%s%d月的天数:"%(year, '闰'if isRun else '', month), daynum)
1.儒略日数与公历的互转
#儒略日数转公历
jd = sxtwl.J2000
t = sxtwl.JD2DD(jd )
#公历转儒略日
jd = sxtwl.toJD(t)
1.查找某日之前或者之后的节气
# 查找某日前后的节气,此例为之后，之前把after替换成before
while True:
    # 这里可以使用after或者before，不用担心速度，这里的计算在底层仅仅是+1这么简单
    day = day.after(1)
    # hasJieQi的接口比getJieQiJD速度要快，你也可以使用getJieQiJD来判断是否有节气。
    if day.hasJieQi():
        print('节气：%s'% constants.jqmc[day.getJieQi()])
        #获取节气的儒略日数， 如果说你要计算什么时间的相距多少，直接比对儒略日要方便，相信我。
        jd = day.getJieQiJD()
        # 将儒略日数转换成年月日时秒
        t = sxtwl.JD2DD(jd )
        # 注意，t.s是小数，需要四舍五入
        print("节气时间:%d-%d-%d %d:%d:%d"%(t.Y, t.M, t.D, t.h, t.m, round(t.s)))
        break
1.四柱反查 (好像还有bug，待修复)
# 四柱反查工具方法
# 实际项目中不要这样子搞哈，因为汉字utf-8，GBK2312不同的编码。建议还是直接使用天干地支的数字索引
def getGZ(gzStr):
    tg = -1
    dz = -1
    for i, v in enumerate(constants.Gan):
        if gzStr[0]  == v:
            tg = i
            break
    for i, v in enumerate(constants.Zhi):
        if  gzStr[1] == v:
            dz = i
            break
    return sxtwl.GZ(tg, dz)
# 四注反查 分别传的是年天干，月天干，日天干，时天干， 开始查询年，结束查询年  返回满足条件的儒略日数
jds = sxtwl.siZhu2Year(getGZ('辛丑'), getGZ('己亥'), getGZ('丙寅'), getGZ('癸巳'), 2003, 2029);
for jd in jds:
    t = sxtwl.JD2DD(jd )
    print("符合条件的时间:%d-%d-%d %d:%d:%d"%(t.Y, t.M, t.D, t.h, t.m, round(t.s)))
'''


def makeDay():
	tm = time.localtime()  # 返回的是命名元组
	# 从公历年月日获取一天的信息
	day = sxtwl.fromSolar(tm.tm_year, tm.tm_mon, tm.tm_mday)
	# 从农历年月日获取一天的信息
	# day = sxtwl.fromLunar(2020, 12, 1)
	return day, tm


def getLunarDate():
	day, tm = makeDay()
	return '。\n'.join((
		get_lunar_date(day),
		get_lunar_month_days(day),
		get_gz(day, tm)
	))


def getJieQi():
	day, _ = makeDay()
	return '。\n'.join([
		get_jieqi_time(day),
		get_jieqi_before(day),
		get_jieqi_after(day)
	])


def get_constellation():
	# 星座(有bug?待修复)
	day, _ = makeDay()
	return constants.XiZ[day.getConstellation()] + '座'
