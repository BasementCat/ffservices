from core import Network, log, config, ffservices
from core.event import Event
from core.Server import Server
from core.Client import Client
from core.IRCMessage import IRCMessage
import re

def module_start():
	return True

def module_stop():
	return True

@Event.listen("Message/Incoming/NICK")
def handle_nickchg(event, message):
	if(message.source is None or message.source==""):
		#new nick
		usermodes=virtualhost=cloakedhost=nickipaddr=None
		nick,hopcount,timestamp,username,hostname,server,servicestamp=message.parameters[0:7]
		if(ffservices.protoctl["NICKv2"]):
			usermodes,virtualhost=message.parameters[7:9]
			if(ffservices.protoctl["CLK"]):
				cloakedhost=message.parameters[9]
				if(ffservices.protoctl["NICKIP"]):
					nickipaddr=message.parameters[10]
			else:
				if(ffservices.protoctl["NICKIP"]):
					nickipaddr=message.parameters[9]
		realname=message.parameters[-1]
		c=Client(nick, hopcount, timestamp, username, hostname, server, servicestamp, usermodes, virtualhost, cloakedhost, nickipaddr, realname)
		log.info("Client connecting at %s: %s (%s@%s[%s])", c.server, c.nick, c.username, c.ip, c.hostname)
		if(not Client.addClient(c)):
			#if we can't add the client, that means that nick already exists.  If the
			#nick already exists, it is a services pseudoclient -- so we kill the
			#non-services client
			c.kill("Nick Collision")
	else:
		#nick change
		who=message.source
		newnick, timestamp=message.parameters
		client=Client.findByNick(who)
		if(client is None): return
		if(client.changeNick(newnick, timestamp)): return
		#nick collision
		client.kill("Nick Collision")

@Event.listen("Message/Incoming/QUIT")
def handle_quit(event, message):
	client=Client.findByNick(message.source)
	if(client is None): return
	log.info("Client exiting at %s: %s!%s@%s[%s]: %s", client.server, client.nick, client.username, client.ip, client.hostname, " ".join(message.parameters))
	Client.removeClient(client)

@Event.listen("Message/Incoming/KILL")
def handle_kill(event, message):
	#when a services client is killed they will have to be reintroduced to the network
	#because unreal will see the KILL message and treat it as though the client is
	#killed, even if we don't want that
	Network.sendToUmode(None, "o", "Attempt by %s to kill %s - killing services pseudoclients is not permitted."%(message.source, message.parameters[0]))
	serv_client=Client.findByNick(message.parameters[0])
	if(serv_client is None): return
	serv_client.introduce()

@Event.listen(
	"Message/Incoming/SETHOST", "Message/Incoming/CHGHOST",
	"Message/Incoming/SETIDENT", "Message/Incoming/CHGIDENT",
	"Message/Incoming/SETNAME", "Message/Incoming/CHGNAME")
def handle_user_info_chg(event, message):
	ev=event.eventName.split("/")[-1]
	action=ev[:3]
	prop=ev[3:]
	target=message.source if action=="SET" else message.parameters[0]
	client=Client.findByNick(target)
	if(client is None): return
	newvalue=message.parameters[0 if action=="SET" else 1]
	if(prop=="HOST"):
		client.changeModes("+xt")
		client.virtualhost=newvalue
	elif(prop=="IDENT"):
		client.username=newvalue
	elif(prop=="NAME"):
		client.realname=newvalue
