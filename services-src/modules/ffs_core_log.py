from core import log
from core.event import Event
import re

mode_to_text={'A':'Server Admins', 'a':'Services Admins', 'C':'Co-Admins', 'h':'HelpOps', 'N':'Net Admins', 'O':'Local Opers', 'o':'Global Opers'}
op_msg_to_text={"WALLOPS":"umode +w", "GLOBOPS":"global opers", "CHATOPS":"all opers", "LOCOPS":"local opers", "ADCHAT":"admins", "NACHAT":"netadmins"}

def module_start():
	return True

def module_stop():
	return True

@Event.listen("Message/Incoming/SMO")
def handle_umode_messages(event, message):
	mode, msg=message.parameters
	msg=re.sub("[\002-\010\012-\037]", "", msg)
	mode=mode_to_text[mode] if mode_to_text.has_key(mode) else "umode "+mode
	log.info("[To %s:] %s", mode, msg)

@Event.listen("Message/Incoming/WALLOPS", "Message/Incoming/GLOBOPS", "Message/Incoming/CHATOPS",
		"Message/Incoming/LOCOPS", "Message/Incoming/ADCHAT", "Message/Incoming/NACHAT")
def handle_op_msgs(event, message):
	msgtype=event.eventName.split("/")[-1]
	log.info("[To %s:] %s", op_msg_to_text[msgtype] if op_msg_to_text.has_key(msgtype) else msgtype, message.parameters[-1])
