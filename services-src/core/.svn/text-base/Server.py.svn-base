from utils import lookup
import Network, config, log, ffservices
from IRCMessage import IRCMessage

class Server:
	known_servers={}
	known_server_numerics={}
	linked_server=None
	
	def __init__(self, name, hopcount, description, numeric=0, flags='', protocol_version=0):
		self.name=name
		self.hopcount=int(hopcount)
		self.description=description
		self.numeric=int(numeric)
		self.flags=flags
		self.protocol_version=int(protocol_version)
		self.protoctl=lookup()
		self.nickchars=[]
		self.chanmodes={}
	
	def __repr__(self):
		return "Server %s[%s] @%s (%s:%s): %s" % (self.name, self.numeric,
			self.hopcount, self.protocol_version, self.flags, self.description)
	
	def introduce(self):
		Network.sendMsg(IRCMessage(":", config.get("Server/Name"), "server", self.name, self.hopcount+1, self.description))
		Network.sendMsg(IRCMessage(":", self.name, "EOS"))
	
	@classmethod
	def createServerFromMessage(self, sv_msg, pctl_msg=None):
		#IMPORTANT: note that this method will ONLY work on the SERVER message received
		#during the connection negotiation process, NOT on SERVER messages intended
		#to introduce new servers!
		name, hopcount, info=sv_msg.parameters
		if(info[0]=="U"):
			info, description=info.split(None, 1)
			protocol_version, flags, numeric=info[1:].split("-")
		else:
			description=info
			protocol_version=0
			flags=''
			numeric=0
		
		svr=Server(name, hopcount, description, numeric, flags, protocol_version)
		if(pctl_msg!=None):
			for pctl in pctl_msg.parameters:
				if(pctl in ("NOQUIT", "TOKEN", "NICKv2", "VHP", "SJOIN", "SJOIN2", "UMODE2", "VL", "SJ3", "NS", "SJB64", "TKLEXT", "NICKIP", "CLK")):
					svr.protoctl.add(pctl)
				else:
					opt, value=pctl.split("=", 1)
					if(opt=="NICKCHARS"):
						svr.nickchars=value.split(",")
					elif(opt=="CHANMODES"):
						cm_types=("list", "paramrequired", "param", "boolean")
						cur_cm_type=0
						for modes_type in value.split(","):
							#for mode in modes_type.split(""):
							for mode in modes_type:
								svr.chanmodes[mode]=cm_types[cur_cm_type]
							cur_cm_type+=1
						#print svr.chanmodes
						#log.edebug("Supported channel modes: %s", " ".join([mc+"="+t for mc,t in svr.chanmodes]))
					else:
						svr.protoctl.add(pctl)
		return svr
	
	@classmethod
	def findByName(self, name):
		return self.known_servers[name] if self.known_servers.has_key(name) else None
	
	@classmethod
	def findByNumeric(self, numeric):
		return self.known_server_numerics[numeric] if self.known_server_numerics.has_key(numeric) else None
	
	@classmethod
	def addServer(self, server):
		ffservices.stats["servers"]+=1
		self.known_servers[server.name]=server
		if(server.numeric>0): self.known_server_numerics[server.numeric]=server
		if(server.hopcount==1):
			self.linked_server=server
			#log.edebug("Linked to %s", server.name)
	
	@classmethod
	def removeServer(self, server):
		ffservices.stats["servers"]-=1
		del(self.known_servers[server.name])
		if(server.numeric>0): del(self.known_server_numerics[server.numeric])
		if(self.linked_server is server): self.linked_server=None
	
	@classmethod
	def removeAllServers(self):
		self.known_servers={}
		self.known_server_numerics={}
	
	@classmethod
	def getLinkedServer(self):
		return self.linked_server
