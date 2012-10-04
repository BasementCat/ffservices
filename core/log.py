import traceback, time
import ffservices

EDEBUG	=	1
DEBUG	=	2
INFO	=	4
WARNING	=	8
ERROR	=	16
FATAL	=	32

ll_to_text={
	1:	"EDEBUG ",
	2:	"DEBUG  ",
	4:	"INFO   ",
	8:	"WARNING",
	16:	"ERROR  ",
	32:	"FATAL  "
	}

def logf(call_stack_offset, level, format, *args):
	#stack=traceback.extract_stack()
	#caller=stack[-2]
	caller=traceback.extract_stack()[-2-call_stack_offset]
	message=format % args
	level_text="???    "
	if(ll_to_text.has_key(level)): level_text=ll_to_text[level]
	caller_info=" [in %s/%s():%d]" % (caller[0].replace(ffservices.cwd, ""), caller[2], caller[1])
	message_time=time.strftime("%Y-%m-%d %H:%M:%S")
	final_message="%s %s: %s%s" % (message_time, level_text, message, caller_info)
	print final_message

def edebug(format, *args): return logf(1, EDEBUG, format, *args)
def debug(format, *args): return logf(1, DEBUG, format, *args)
def info(format, *args): return logf(1, INFO, format, *args)
def warning(format, *args): return logf(1, WARNING, format, *args)
def error(format, *args): return logf(1, ERROR, format, *args)
def fatal(format, *args): return logf(1, FATAL, format, *args)
