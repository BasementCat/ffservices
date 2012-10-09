import signal

all_handlers={}

def sighandler(signo):
	def sighandler_internal(callback):
		global all_handlers
		all_handlers[getattr(signal, signo) if isinstance(signo, str) else signo]=callback
		return callback
	return sighandler_internal

def installSignalHandlers():
	global all_handlers
	for signo, callback in all_handlers.items():
		signal.signal(signo, callback)