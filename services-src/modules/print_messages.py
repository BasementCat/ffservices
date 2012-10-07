from core import event

def module_start():
	event.addHandler("Message", print_msgs)
	return True

def module_stop(): return True

def print_msgs(eventname, message):
	print "%s %s" % (
		"<<< " if (eventname.split("/")[1]=="Incoming") else " >>>",
		str(message).strip()
		)
