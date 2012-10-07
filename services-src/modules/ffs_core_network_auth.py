import time, logging
from core import Network, ffservices, config
from core.event import Event
from core.IRCMessage import IRCMessage
from core.Server import Server

log=logging.getLogger(__name__)
is_authed=False
connected_protoctl=None
#The core depends on some specific behaviors of this module -- specifically, when
#the connection is authenticated it must trigger the Network/LinkEstablished event
#and set Network.isAuthed to true

def module_start():
	return True

def module_stop():
	return True

@Event.listen("Network/Connect")
def do_net_send_auth(event):
	Network.sendMsg(IRCMessage(None, None, 'pass', config.get("Network/Password")))
	pctl=list(ffservices.protoctl)
	pctl.append("NICKCHARS=%s" % ",".join(ffservices.pro_nickchars))
	Network.sendMsg(IRCMessage(None, None, 'protoctl', *pctl))
	Network.sendMsg(IRCMessage(None, None, 'server',
		config.get("Server/Name"),
		'1',
		"U%d-%s-%d %s" % (
			ffservices.unrealProtocol,
			"".join(ffservices.flags),
			config.get("Server/Numeric"),
			config.get("Server/Description")
			)
		))

@Event.listen("Network/Disconnect")
def do_net_disconnect(event):
	global is_authed
	is_authed=False
	Server.removeAllServers()

@Event.listen("Message/Incoming/PROTOCTL", "Message/Incoming/PASS", "Message/Incoming/SERVER")
def do_incoming_auth(event, message):
	global is_authed, connected_protoctl
	if(message.command=="PROTOCTL"):
		connected_protoctl=message
	elif(message.command=="PASS"):
		if(message.parameters[0]!=config.get("Network/Password")):
			log.critical("Password mismatch!  Expected '%s', got '%s'", config.get("Network/Password"), message.parameters[0])
			Network.sendMsg(IRCMessage(':', config.get("Server/Name"), "ERROR", "Closing link: password mismatch"))
			#Network.disconnect() #this is done in the main file
			ffservices.shutdown(1)
	elif(message.command=="SERVER"):
		if(is_authed): return
		is_authed=True
		Server.addServer(Server.createServerFromMessage(message, connected_protoctl))
		Event.trigger("Network/LinkEstablished")
		Network.isAuthed=True
		#anything that watches for this event should do things like send user info (NICK),
		#channel membership, channel info, modes, etc at this point
		Network.sendMsg(IRCMessage(None, None, "netinfo", 0, int(time.time()), ffservices.unrealProtocol, "*", 0, 0, 0, config.get("Network/Name")))
		#TODO: keep track of my max known global users?
		Network.sendMsg(IRCMessage(None, None, "eos"))
		event.stop()
