from core import event, Network, log, config, ffservices
from core.Server import Server
from core.Client import Client
from core.Channel import Channel
from core.IRCMessage import IRCMessage
import re, time

def module_start():
	event.addHandler("Message/Incoming/PING", handle_ping)
	event.addHandler("Message/Incoming/MODE", "Message/Incoming/UMODE2", handle_modechg)
	return True

def module_stop(): return True

def handle_ping(eventname, message):
	if(len(message.parameters)>1):
		Network.sendf("pong", *message.parameters.reverse())
	else:
		Network.sendf("pong", config.get("Server/Name"))

def handle_modechg(eventname, message):
	target_is_channel=False
	source=message.source
	target=modelist=None
	params=[]
	if(eventname.split("/")[-1]=="UMODE2"):
		target=source
		modelist=message.parameters[0]
	else:
		target=message.parameters[0]
		modelist=message.parameters[1]
		if(target[0] in ("#", "&", "+")):
			target_is_channel=True
			params=message.parameters[2:]
	
	if(target_is_channel):
		if(not Server.findByName(source) is None and params[-1].isdigit()):
			timestamp=long(params[-1])
		else:
			timestamp=time.time()
		
		channel=Channel.findByName(target)
		if(channel is None): return
		if(channel.timestamp==timestamp):
			channel.setModes(modelist, params, True)
		elif(channel.timestamp>timestamp):
			channel.clearModes()
			channel.setModes(modelist, params)
	else:
		client=Client.findByNick(target)
		if(client is None): return
		client.changeModes(modelist)
		log.edebug("%s changed modes of %s to %s", source, client.nick, client.usermodes)
