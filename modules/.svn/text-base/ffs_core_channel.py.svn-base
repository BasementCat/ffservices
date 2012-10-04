from core import event, Network, log, config, ffservices
from core.Server import Server
from core.Client import Client
from core.Channel import Channel
from core.IRCMessage import IRCMessage
import re, time

sjoin_prefix_to_mode={"*":"q", "~":"a", "@":"o", "%":"h", "+":"v", "&":"b", "\"":"E", "'":"I"}

#logically, SAJOIN, SAPART, and SAMODE should be implemented here.  However, as this
#is a services server, we should never receive them from a server -- if we do they
#would be targeted at one of our clients and should be ignored anyway.
#INVITE should be implemented here as well -- probably not though, since we don't need to respond to invites ourself

def module_start():
	event.addHandler("Message/Incoming/SJOIN", handle_sjoin)
	event.addHandler("Message/Incoming/JOIN", handle_join)
	event.addHandler("Message/Incoming/PART", "Message/Incoming/KICK", handle_leave)
	event.addHandler("Message/Incoming/TOPIC", handle_topicchg)
	return True

def module_stop(): return True

def handle_sjoin(eventname, message):
	chan_name=message.parameters[1]
	timestamp=message.parameters[0]
	chan=Channel.findByName(chan_name)
	if(chan is None):
		chan=Channel(chan_name, timestamp)
		Channel.addChannel(chan)
	p_idx=2
	if(message.parameters[p_idx][0]=="+"):
		#we have modes
		if(chan.timestamp==timestamp):
			#merge modes
			chan.setModes(message.parameters[p_idx], message.parameters[p_idx+1:-1], True)
		elif(chan.timestamp>timestamp):
			#clear existing modes and use sjoin modes
			chan.clearModes()
			chan.setModes(message.parameters[p_idx], message.parameters[p_idx+1:-1])
		#else ignore sjoin modes
	
	new_modes=[]
	new_params=[]
	for item in message.parameters[-1].split():
		#this could be a channel member, ban, exemption, or invex -- very confusing!
		# *~@%+ are user statuses qaohv, respectively
		# & is a ban, " is an exemption, ' is an invex
		item_type=item[0]
		if(sjoin_prefix_to_mode.has_key(item_type)):
			item=item[1:]
			new_modes.append(sjoin_prefix_to_mode[item_type])
			new_params.append(item)
		
		if(not sjoin_prefix_to_mode.has_key(item_type) or item_type in ("*", "~", "@", "%", "+")):
			member=Client.findByNick(item)
			if(not member is None):
				log.debug("SJOIN: %s to %s", member.nick, chan.name)
				chan.addClient(member)
	
	if(len(new_modes)>0): chan.setModes("+"+"".join(new_modes), new_params)

def handle_join(eventname, message):
	client=Client.findByNick(message.source)
	if(client is None): return
	chan=Channel.findByName(message.parameters[0])
	if(chan is None):
		chan=Channel(message.parameters[0], time.time())
		Channel.addChannel(chan)
	chan.addClient(client)
	log.debug("%s has joined %s", client.nick, chan.name)

def handle_leave(eventname, message):
	source=Client.findByNick(message.source)
	if(source is None): source=Server.findByName(message.source)
	if(source is None): return
	targetchan=Channel.findByName(message.parameters[0])
	if(targetchan is None): return
	if(message.command=="PART"):
		targetuser=source
		reason=message.parameters[-1] if len(message.parameters)>1 else "[none]"
	elif(message.command=="KICK"):
		targetuser=Client.findByNick(message.parameters[1])
		if(targetuser is None): return
		reason=message.parameters[-1]
	log.debug("%s has left %s: %s: %s",
		targetuser.nick,
		targetchan.name,
		"kicked by "+(source.nick if source.__class__.__name__=="Client" else source.name) if message.command=="KICK" else "PART",
		reason
		)
	targetchan.removeClient(targetuser)

def handle_topicchg(eventname, message):
	chan_name, who, ts, topic=message.parameters
	chan=Channel.findByName(chan_name)
	if(chan is None): return
	chan.setTopic(topic, who, ts)
