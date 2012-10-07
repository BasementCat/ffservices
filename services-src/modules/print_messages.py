from core.event import Event

def module_start():
	return True

def module_stop():
	return True

@Event.listen("Message")
def print_msgs(event, message):
	print "%s %s" % (
		"<<< " if (event.eventName.split("/")[1]=="Incoming") else " >>>",
		str(message).strip()
		)
