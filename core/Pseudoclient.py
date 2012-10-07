import time, types, logging
import Network, event, config
from Client import Client
from IRCMessage import IRCMessage
from PseudoclientCommand import PseudoclientCommand

log=logging.getLogger(__name__)

def introduce_pseudoclients(eventname):
	Pseudoclient.introduceAll()

def dispatch_pc_privmsgs(eventname, message):
	log.debug("Got privmsg: %s", str(message).strip())
	for pc_name in message.parameters[:-1]:
		pc=Pseudoclient.findByNick(pc_name)
		if(pc is None):
			log.debug("Can't find pseudoclient for nick %s!", message.parameters[0])
			return
		pc.privmsg(message)
	
event.addHandler("Network/LinkEstablished", introduce_pseudoclients)
event.addHandler("Message/Incoming/PRIVMSG", dispatch_pc_privmsgs)

class Pseudoclient(Client):
	pseudoclients={}
	pseudoclients_bynick={}
	
	def __init__(self, svc_name, nick, user, host, realname):
		#def __init__(self, nick, hopcount, timestamp, username, hostname, server, servicestamp, usermodes, virtualhost, cloakedhost, nickipaddr, realname):
		super(Pseudoclient, self).__init__(nick, 1, long(time.time()), user, host, config.get("Server/Name"), long(time.time()), "+", "*", "*", "*", realname)
		self.name=svc_name
		self.description=svc_name
		self.commands={}
		self.help="No help for "+svc_name+"."
		Pseudoclient.add(self)
		if(Network.isAuthed): self.introduce()
	
	def changeNick(self, newnick, timestamp=None):
		if(timestamp is None): timestamp=time.time()
		parent=super(Pseudoclient, self)
		oldnick=parent.nick
		if(parent.changeNick(newnick, timestamp)):
			del self.pseudoclients_bynick[oldnick.lower()]
			self.pseudoclients_bynick[parent.nick.lower()]=self
			return True
		else: return False
	
	def addCommand(self, command, head=False):
		if(not self.commands.has_key(command.command)): self.commands[command.command]=[]
		if(head):
			self.commands[command.command].insert(0, command)
		else:
			self.commands[command.command].append(command)
	
	def removeCommand(self, command):
		if(not self.commands.has_key(command.command)): return
		if(command in self.commands[command.command]): self.commands[command.command].remove(command)
	
	def getCommand(self, commandname):
		return self.commands[commandname.upper()] if self.commands.has_key(commandname.upper()) else None
	
	def getHelp(self, item=None):
		if(item is None):
			help=[self.help]
			#commandlist=[(c[0].command, c[0].description) for c in self.commands.values()]
			commandlist_temp=[]
			max_cmd_length=0
			for c in self.commands.values():
				commandlist_temp.append((c[0].command, c[0].description))
				if(len(c[0].command)>max_cmd_length): max_cmd_length=len(c[0].command)
			
			if(len(commandlist_temp)>0):
				help.append(" ")
				help.extend(["\x02%s\x02%s%s"%(c[0], " "*((max_cmd_length+4)-len(c[0])), c[1]) for c in commandlist_temp])
			
			return help
		
		item=item.upper()
		commandname=item.split()[0]
		command=self.getCommand(commandname)
		if(command is None): return None
		#command=command[0]
		#if(command.help.has_key(item)):
		#	return command.help[item]
		#return None
		return command[0].getHelp(item)
	
	def privmsg(self, message):
		log.debug("Got privmsg for %s from %s: %s", message.parameters[0], message.source, message.parameters[-1])
		command_parts=message.parameters[-1].split(None, 1)
		command=command_parts[0]
		command_text=command_parts[1] if len(command_parts)>1 else ""
		command=command.upper()
		if(command=="HELP"):
			if(command_text=="" or command_text.lower() in (self.nick.lower(), self.name.lower())):
				#requesting help for this service
				#for line in IRCMessage.wrapText(self.help):
				#print self.getHelp()
				#for line in IRCMessage.wrapText("\n".join(self.getHelp())):
				
				#for line in IRCMessage.wrapText(self.getHelp()):
					#self.sendMsg(message.source, line)
				self.sendMsg(message.source, self.getHelp())
			else:
				#print help
				help_temp=self.getHelp(command_text)
				if(help_temp is None):
					help="No help exists for \x02"+command_text+"\x02."
				else:
					help=["\x02%s\x02 - %s"%(command_text.upper(), help_temp[0]), " "]
					help.extend(help_temp[1:])
				
				#for line in IRCMessage.wrapText(help):
					#self.sendMsg(message.source, line)
				self.sendMsg(message.source, help)
		else:
			command_o=self.getCommand(command)
			if(command_o is None):
				#for line in IRCMessage.wrapText("Unrecognized command: \x02%s\x02."%(command)): self.sendMsg(message.source, line)
				self.sendMsg(message.source, "Unrecognized command: \x02%s\x02."%(command))
			else:
				for command_o_real in command_o:
					if(command_o_real.handler is None):
						log.error("One of the handlers for %s %s command is None!", self.name, command_o_real.command)
						continue
					
					if(not command_o_real.handler(message.source, command, command_text)):
						break
	
	def sendMsg(self, to_nick, format, *args):
		#sends a message to a nick as this client
		#eventually, will use the client's preferred notification method, for now it's PRIVMSGs
		#Network.sendMsg(IRCMessage(":", self.nick, "PRIVMSG", to_nick, format % args))
		if(isinstance(format, types.StringTypes)):
			text=format % args
		else:
			text=format
		
		for line in IRCMessage.wrapText(text):
			Network.sendMsg(IRCMessage(":", self.nick, "PRIVMSG", to_nick, line))
	
	@classmethod
	def introduceAll(self):
		#print self.pseudoclients
		for pc in self.pseudoclients.values():
			#log.debug("Introducing pseudoclient %s: %s!%s@%s (%s) [%s]", pc.name, pc.nick, pc.username, pc.hostname, pc.realname, str(pc))
			pc.introduce()
	
	@classmethod
	def add(self, pc):
		#log.debug("Adding Pseudoclient %s (%s -> %s)", pc.name, pc.nick, pc.nick.lower())
		self.pseudoclients[pc.name]=pc
		self.pseudoclients_bynick[pc.nick.lower()]=pc
		Client.addClient(pc)
	
	@classmethod
	def create(self, svc_name, nick, user, host, realname):
		if(self.pseudoclients.has_key(svc_name)): return None
		if(self.pseudoclients_bynick.has_key(nick.lower())): return False
		return Pseudoclient(svc_name, nick, user, host, realname) #__init__ automatically adds it for us
	
	@classmethod
	def removePC(self, pc_name, reason="Removed"):
		if(not self.pseudoclients.has_key(pc_name)): return
		self.pseudoclients[pc_name].remove(reason)
	
	def remove(self, reason="Removed"):
		del self.pseudoclients[self.name]
		del self.pseudoclients_bynick[self.nick.lower()]
		Client.removeClient(self)
		Network.sendMsg(":", super(Pseudoclient, self).nick, "QUIT", reason)
	
	@classmethod
	def findByNick(self, nick):
		return self.pseudoclients_bynick[nick.lower()] if self.pseudoclients_bynick.has_key(nick.lower()) else None
