class PseudoclientCommand():
	def __init__(self, command, handler, description=None, help=None):
		self.command=command.upper()
		self.handler=handler
		self.description=description
		#self.help={self.command:help}
		self.help={}
		self.addHelp(command, description, help)
	
	def addHelp(self, item, description, help):
		#item must include the command name! (for example, for chanserv: SET SUBOPTION)
		self.help[item.upper()]=(description, help)
		return self #for method chaining -- so you can do PseudoclientCommand(args).addHelp(stuff).addHelp(morehelp), etc
	
	def getHelp(self, item):
		item=item.upper()
		return self.help[item] if self.help.has_key(item) else None
	
	def getSubCommandHelp(self):
		r={}
		for sc_name in self.help.keys():
			if(sc_name==self.command): continue
			r[sc_name]=self.help[sc_name]
		
		return r
