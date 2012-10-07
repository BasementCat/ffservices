import base64, socket, struct, re, logging
import config, Network, ffservices
from Server import Server
from IRCMessage import IRCMessage

log=logging.getLogger(__name__)

class Client(object):
	known_clients_nick={}
	known_clients_server={}
	
	def __init__(self, nick, hopcount, timestamp, username, hostname, server, servicestamp, usermodes, virtualhost, cloakedhost, nickipaddr, realname):
		self.nick=nick
		self.hopcount=hopcount
		self.timestamp=timestamp
		self.username=username
		self.hostname=hostname
		self.server=server
		self.servicestamp=servicestamp
		self.usermodes=usermodes
		self.virtualhost="" if virtualhost is None or virtualhost=="*" else virtualhost
		self.cloakedhost=cloakedhost
		self.nickipaddr=nickipaddr
		self.ip=Client.int_to_ip(Client.decodeUnrealB64(nickipaddr, Client.decodeUnrealB64Char_NICKIP), True if len(nickipaddr)>9 else False) if nickipaddr else None
		if(self.ip is not None): self.ip=Client.formatIPv6(self.ip) if len(nickipaddr)>9 else self.ip
		self.realname=realname
		#log.debug("New client: %s!%s [%s -> %s -> %s -> %s] on %s, %s, %s", self.nick, self.username, self.ip, self.hostname, self.cloakedhost, self.virtualhost, self.server, self.usermodes, self.realname)
	
	def introduce(self):
		svr=Server.getLinkedServer()
		msg=None
		if(svr.protoctl["NICKv2"]):
			if(svr.protoctl["CLK"]): #NICKv2 and CLK
				if(svr.protoctl["NICKIP"]): #NICKv2 and CLK and NICKIP
					msg=IRCMessage(None, None, "nick", self.nick, self.hopcount, self.timestamp, self.username, self.hostname, self.server, self.servicestamp, self.usermodes, self.virtualhost, self.cloakedhost, self.nickipaddr, self.realname)
				else: #NICKv2 and CLK
					msg=IRCMessage(None, None, "nick", self.nick, self.hopcount, self.timestamp, self.username, self.hostname, self.server, self.servicestamp, self.usermodes, self.virtualhost, self.cloakedhost, self.realname)
			else: #NICKv2 but not CLK
				if(svr.protoctl["NICKIP"]): #NICKv2 and NICKIP
					msg=IRCMessage(None, None, "nick", self.nick, self.hopcount, self.timestamp, self.username, self.hostname, self.server, self.servicestamp, self.usermodes, self.virtualhost, self.nickipaddr, self.realname)
				else: #nickv2, no clk, no nickip
					msg=IRCMessage(None, None, "nick", self.nick, self.hopcount, self.timestamp, self.username, self.hostname, self.server, self.servicestamp, self.usermodes, self.virtualhost, self.realname)
		else: #normal
			msg=IRCMessage(None, None, "nick", self.nick, self.hopcount, self.timestamp, self.username, self.hostname, self.server, self.servicestamp, self.realname)
		
		Network.sendMsg(msg)
	
	def changeNick(self, newnick, timestamp):
		if(timestamp>self.timestamp):
			del self.known_clients_nick[self.nick.lower()]
			self.known_clients_nick[newnick.lower()]=self
			self.nick=newnick
			self.timestamp=timestamp
			return True
		else:
			return False
	
	def kill(self, reason):
		#this sends a kill from this server
		me=config.get("Server/Name")
		Network.sendf(":"+me, "kill", self.nick, "%s (%s)"%(me, reason))
		self.remove()
	
	def changeModes(self, modechange):
		mode_dir="+"
		mode_list=[c if c not in ("+", "-") else "" for c in self.usermodes]
		for c in modechange:
			if(c in ("+", "-")):
				mode_dir=c
				continue
			
			if(mode_dir=="+"):
				if(not c in mode_list):
					mode_list.append(c)
					if(c=="i"):
						ffservices.stats["invisible"]+=1
						ffservices.stats["normal"]-=1
					elif(c=="o"):
						ffservices.stats["opers"]+=1
			else:
				if(c in mode_list):
					mode_list.remove(c)
					if(c=="i"):
						ffservices.stats["invisible"]-=1
						ffservices.stats["normal"]+=1
					elif(c=="o"):
						ffservices.stats["opers"]-=1
		mode_list.sort()
		self.usermodes="+"+"".join(mode_list)
	
	def hasMode(self, mode, has_one_mode=False):
		#multiple modes may be passed in the mode parameter, either as a list or as a string with len>1
		#by default the behavior is to return true only if all of the supplied modes are set
		#setting the second parameter to True causes it to return true if at least one of the supplied modes is set
		for modechar in mode:
			if(modechar in self.usermodes):
				if(has_one_mode): return True
			else:
				if(not has_one_mode): return False
		return True
	
	def quit(self, reason):
		Network.sendf(":"+self.nick, "quit", reason)
		log.info("Locally QUITting client: %s", reason)
		self.remove()
	
	def remove(self):
		Client.removeClient(self)
	
	@classmethod
	def addClient(self, client):
		existing_client=Client.findByNick(client.nick)
		if(not existing_client is None):
			return False
		
		if("i" in client.usermodes):
			ffservices.stats["invisible"]+=1
		else:
			ffservices.stats["normal"]+=1
		if("o" in client.usermodes): ffservices.stats["opers"]+=1
		
		self.known_clients_nick[client.nick.lower()]=client
		#self.known_clients_server[client.server]=client
		if(self.known_clients_server.has_key(client.server)):
			self.known_clients_server[client.server].append(client)
		else:
			self.known_clients_server[client.server]=[client]
		return True
	
	@classmethod
	def removeClient(self, client):
		if("i" in client.usermodes):
			ffservices.stats["invisible"]-=1
		else:
			ffservices.stats["normal"]-=1
		if("o" in client.usermodes): ffservices.stats["opers"]-=1
		
		if(self.known_clients_nick.has_key(client.nick.lower())): del self.known_clients_nick[client.nick.lower()]
		#if(self.known_clients_server.has_key(client.server)): del self.known_clients_server[client.server]
		if(self.known_clients_server.has_key(client.server) and client in self.known_clients_server[client.server]):
			self.known_clients_server[client.server].remove(client)
	
	@classmethod
	def findByNick(self, nick):
		return self.known_clients_nick[nick.lower()] if self.known_clients_nick.has_key(nick.lower()) else None
	
	@classmethod
	def findByServer(self, servername):
		return self.known_clients_server[servername] if self.known_clients_server.has_key(servername) else []
	
	@classmethod
	def decodeUnrealB64Char_NICKIP(self, char):
		if(char=="="): return None
		num=ord(char)
		if(num>96): return num-(97-26)
		if(num>64): return num-65
		if(num>47): return num-(48-52)
		if(num==47): return 63
		if(num==43): return 62
		return None
	
	@classmethod
	#def decodeUnrealB64(self, string, table):
	def decodeUnrealB64(self, string, decode_func):
		r=0
		i=0
		for char in string:
			num=decode_func(char)
			#log.debug("%s=%s", char, str(num))
			if(num is None): continue
			r=(r<<6)|num
			#r=r|(num<<(6*i))
			i+=1
		return r/16
	
	@classmethod
	def int_to_ip(self, ip, ipv6=False):
		ip_list=[]
		#ip_bits=(len(hex(ip))-2)*4
		#ipv6=True if ip_bits>32 else False
		for i in range(0, 4 if not ipv6 else 8):
			if(ipv6):
				ip_list.append(hex(ip&0xffff)[2:])
				ip=ip>>16
			else:
				ip_list.append(str(ip&0xff))
				ip=ip>>8
		ip_list.reverse()
		return (":" if ipv6 else ".").join(ip_list)
	
	@classmethod
	def formatIPv6(self, ip, long_fmt=False):
		ip_parts=ip.split(":")
		new_ip=[]
		for part in ip_parts:
			if(part is None or part==""):
				new_ip.extend(["0" for i in range(0, 8-len(ip_parts))])
			else:
				new_ip.append(part)
		new_ip_s=":".join(new_ip)
		if(not long_fmt): new_ip_s=re.sub("((:0)|(0:)){2,}", "::", new_ip_s)
		return new_ip_s
