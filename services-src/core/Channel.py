import time, logging
from Server import Server
import ffservices

log=logging.getLogger(__name__)

class Channel:
	known_channels={}
	
	def __init__(self, name, timestamp):
		self.name=name
		self.timestamp=timestamp
		self.topic=""
		self.topicsetby=None
		self.topictimestamp=0
		self.modes={}
		self.members={}
		self.memberstatus={}
		self.banlist=[]
		self.exemptlist=[]
		self.invexlist=[]
		log.debug("Creating new channel: %s @%d", name, int(timestamp))
	
	def setTopic(topic, who, ts=None):
		self.topic=topic
		self.topicsetby=who
		self.topictimestamp=ts if not ts is None else time.time()
	
	def addClient(self, client):
		self.members[client.nick.lower()]=client
	
	def removeClient(self, client):
		if(self.members.has_key(client.nick.lower())): del self.members[client.nick.lower()]
		if(self.memberstatus.has_key(client.nick.lower())): del self.memberstatus[client.nick.lower()]
		if(len(self.members)==0):
			Channel.removeChannel(self)
	
	@classmethod
	def getModes(self, modes, params=[]):
		modedir="+"
		r=[]
		param_idx=0
		svr=Server.getLinkedServer()
		for modechar in modes:
			if(modechar in ("+", "-")):
				modedir=modechar
				continue
			#if this line makes it crash again, it's Unreal's fault -- svr.chanmodes contains *all* of the modes that it specified in PROTOCTL!
			#which, btw, does not include q, a, o, h, or v - no wonder >.>
			#print svr.chanmodes
			#print svr
			if(modechar in ("q", "a", "o", "h", "v")):
				#r[modeID]=params[param_idx]
				r.append([modedir, modechar, params[param_idx]])
				param_idx+=1
			elif(svr.chanmodes[modechar]=="boolean"):
				#r[modeID]=True
				r.append([modedir, modechar, True])
			elif(modedir=="+" or svr.chanmodes[modechar]=="paramrequired"):
				#r[modeID]=params[param_idx]
				r.append([modedir, modechar, params[param_idx]])
				params_idx+=1
		return r
	
	def clearModes(self):
		self.memberstatus=self.modes={}
		self.banlist=self.exemptlist=self.invexlist=[]
	
	def setModes(self, modes, params=[], merge=False):
		server=Server.getLinkedServer()
		#for mode, param in Channel.getModes(modes, params):
			#modedir, modechar=[c for c in mode]
		for modedir, modechar, param in Channel.getModes(modes, params):
			if(modedir=="+"):
				if(modechar in ("q", "a", "o", "h", "v")):
					if(not param.lower() in self.memberstatus):
						self.memberstatus[param.lower()]=[]
					
					if(modechar in self.memberstatus[param.lower()]): continue
					self.memberstatus[param.lower()].append(modechar)
				elif(server.chanmodes[modechar]=="boolean"):
					dontset=False
					if(merge):
						if(modechar=="p" and self.modes.has_key("s")):
							dontset=True
						elif(modechar=="s" and self.modes.has_key("p")):
							del self.modes["p"]
						elif(modechar=="S" and self.modes.has_key("c")):
							dontset=True
						elif(modechar=="c" and self.modes.has_key("S")):
							del self.modes["S"]
					if(dontset): continue
					self.modes[modechar]=True
				elif(server.chanmodes[modechar] in ("param", "paramrequired")):
					dontset=False
					if(merge):
						if(modechar in ("l", "k", "L", "F")):
							if(self.modes.has_key(modechar) and self.modes[modechar]>param): dontset=True
						elif(modechar=="j"):
							if(self.modes.has_key("j")):
								old_limit, old_time=self.modes["j"].split(":")
								new_limit, new_time=param.split(":")
								if(old_time==new_time):
									if(old_limit>new_limit): dontset=True
								elif(old_time>new_time): dontset=True
					if(dontset): continue
					self.modes[modechar]=param
				elif(server.chanmodes[modechar]=="list"):
					if(modechar=="b"):
						mlist=self.banlist
					elif(modechar=="E"):
						mlist=self.exemptlist
					elif(modechar=="I"):
						mlist=self.invexlist
					else:
						continue
					
					if(param.lower() in mlist): continue
					mlist.append(param.lower())
			elif(modedir=="-"):
				if(modechar in ("q", "a", "o", "h", "v")):
					if(not param.lower() in self.memberstatus): continue
					if(modechar in self.memberstatus[param.lower()]):
						self.memberstatus[param.lower()].remove(modechar)
				elif(server.chanmodes[modechar] in ("param", "boolean", "paramrequired")):
					if(self.modes.has_key(modechar)): del self.modes[modechar]
				elif(server.chanmodes[modechar]=="list"):
					if(modechar=="b"):
						mlist=self.banlist
					elif(modechar=="E"):
						mlist=self.exemptlist
					elif(modechar=="I"):
						mlist=self.invexlist
					else:
						continue
					
					if(not param.lower() in mlist): continue
					mlist.remove(param.lower())
	
	@classmethod
	def findByName(self, name):
		return self.known_channels[name.lower()] if self.known_channels.has_key(name.lower()) else None
	
	@classmethod
	def addChannel(self, channel):
		#don't add empty channels, it might break things
		self.known_channels[channel.name.lower()]=channel
		ffservices.stats["channels"]+=1
	
	@classmethod
	def removeChannel(self, channel):
		if(self.known_channels.has_key(channel.name.lower())):
			del(self.known_channels[channel.name.lower()])
			ffservices.stats["channels"]-=1
