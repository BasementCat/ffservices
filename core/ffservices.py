from utils import lookup
import os, time

configFileName		=	"servicesconfig.yml"
version				=	"1.0.0"
secondsPerTick		=	0.10
recvSize			=	8192
exitCode			=	None
unrealProtocol		=	2309
cwd					=	os.getcwd()
startTime			=	int(time.time())
DEBUG				=	True

stats				=	{
	"normal": 0,
	"invisible": 0,
	"servers": 0,
	"opers": 0,
	"channels": 0
	}

def shutdown(code):
	global exitCode
	exitCode=code

protoctl			=	lookup(
	#"NOQUIT",
	"NICKv2",
	"VL",
	"SJ3",
	#"NS",
	"NICKIP",
	"CLK"
	)
pro_nickchars		=	[]

#see http://www.unrealircd.com/files/docs/technical/serverprotocol.html for details on meaning of flags
flags				=	["h"]
#if command line config file location is used, add flag C
if(DEBUG): flags.append("D")
#if we're on windows, append flag W
#if we log to syslog, append flag Y
#if we support ipv6, append flag 6
#if we have ssl support, add flag e
#if we implement ziplinks, add flag Z

def formatTimeDiff(old_time, new_time, short=True):
	diff_s=new_time-old_time
	parts=[]
	part_names_long=("year", "month", "day", "hour", "minute", "second")
	part_names_short=("Y", "M", "D", "h", "m", "s")

	parts.append(int(diff_s/31536000.0))
	diff_s=diff_s%31536000.0
	
	parts.append(int(diff_s/1033967.213114754))
	diff_s=diff_s%1033967.213114754
	
	parts.append(int(diff_s/86400.0))
	diff_s=diff_s%86400.0
	
	parts.append(int(diff_s/3600.0))
	diff_s=diff_s%3600.0
	
	parts.append(int(diff_s/60.0))
	diff_s=diff_s%60.0
	
	parts.append(int(diff_s))
	
	r=[]
	for part_num in range(0, 6):
		part_val=parts[part_num]
		if(part_val==0): continue
		plural="s" if (not short and part_val!=1) else ""
		r.append("%d%s%s%s"%(
			part_val,
			" " if not short else "",
			(part_names_short if short else part_names_long)[part_num],
			plural
			))
	return (" " if short else ", ").join(r)
