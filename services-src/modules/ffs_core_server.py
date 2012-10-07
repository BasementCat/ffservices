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

@Event.listen("Message/Incoming/SERVER")
def handle_new_server(event, message):
	if(ffservices.protoctl["NS"]):
		source=Server.findByNumeric(message.source)
		server=Server(message.parameters[0], message.parameters[1], message.parameters[-1], message.parameters[2])
	else:
		source=Server.findByName(message.source)
		server=Server(message.parameters[0], message.parameters[1], message.parameters[-1])
	
	Server.addServer(server)
	log.info("Server connecting at %s: %s (numeric %d, %d hops): %s", source.name if source is not None else "[None]", server.name, server.numeric, server.hopcount, server.description)

@Event.listen("Message/Incoming/SQUIT", "Message/Incoming/ERROR")
def handle_squit(event, message):
	servername=message.parameters[0]
	if(message.command=="ERROR" or servername==config.get("Server/Name")):
		log.info("Shutting down: %s", message.parameters[-1])
		ffservices.shutdown(0)
		return
	
	server=Server.findByName(servername)
	if(server is None): return
	if(server.hopcount==1):
		log.info("Removing pseudoserver %s: requested by %s: %s", server.name, message.source, message.parameters[-1])
		Server.removeServer(server)
	else:
		log.info("Server exiting: %s: SQUIT from %s: %s", server.name, message.source, message.parameters[-1])
		#luckily as long as we don't specify NOQUIT in our protoctl, unreal will notify
		#us of each user that is going away BEFORE sending us the SQUIT message, meaning
		#that the existing code for removing users is used rather than having to figure
		#out which users are exiting here.
		Server.removeServer(server)

@Event.listen("Message/Incoming/SDESC")
def handle_sdesc(event, message):
	server=Server.findByName(message.parameters[0])
	server.description=message.parameters[-1]
