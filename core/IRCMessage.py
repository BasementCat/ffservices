import event
import re, types

class IRCMessage:
	leftover_queue_text=None
	
	def __init__(self, src_type, source, command, *args):
		self.source_type=src_type
		self.source=source
		self.command=command
		self.parameters=args
	
	@classmethod
	def parse(self, text):
		text=text.strip()
		if(text==""): return None
		#print "Processing: %s" % text
		src_type=source=command=parameters=temp_param_s=last_parameter=None
		
		match=re.match("^(?:([:@])(\S+)\s+)?(\S+)((?:\s+).+?)?$", text)
		if(match is None): return None
		src_type, source, command, text=match.groups()
		if(not text is None):
			if(re.match("^(?:\s+)?:", text)):
				parameters=[text[1:]]
			else:
				temp_param_s, last_parameter=re.match("^(?:\s+)?(.+?)(?:\s+:(.*))?$", text).groups()
				parameters=temp_param_s.split()
				if(not last_parameter is None):
					parameters.append(last_parameter)
		else:
			parameters=[]
		
		if(len(parameters)==1 and parameters[-1][0]==":"): parameters[-1]=parameters[-1][1:]
		return IRCMessage(src_type, source, command, *parameters)
	
	def __str__(self):
		params=[str(x) for x in self.parameters]
		return "%s%s%s%s%s\r\n" % (
			self.source_type if (self.source and self.source_type) else (":" if self.source else ""),
			str(self.source) if self.source else "",
			" " if self.source else "",
			str(self.command),
			"%s%s %s%s" % (
					" " if len(params)>1 else "",
					" ".join(params[:-1]) if len(params)>1 else "",
					":" if re.search("\s", params[-1]) else "",
					params[-1]
				) if len(params) else ""
			)
	
	@classmethod
	def processMessageQueue(self, data):
		if(not self.leftover_queue_text is None):
			data=self.leftover_queue_text+data
			self.leftover_queue_text=None
		
		incomplete_last_message=False
		if(not data.endswith("\r\n")):
			incomplete_last_message=True
		
		messages=data.split("\r\n")
		if(incomplete_last_message):
			self.leftover_queue_text=messages.pop()
		
		for message_text in messages:
			msg=IRCMessage.parse(message_text)
			if(msg is None): continue #invalid message or something
			event.trigger("Message/Incoming/"+msg.command, message=msg)
	
	@classmethod
	def wrapText(self, full_text_arg, characters=80):
		r=[]
		for full_text in ([full_text_arg] if isinstance(full_text_arg, types.StringTypes) else full_text_arg):
			for text in full_text.split("\n"):
				while(len(text)>characters):
					c_idx=characters
					while(c_idx>=0 and text[c_idx] not in (" ", "\n", "\t", "\r")): c_idx-=1
					if(c_idx<=0): c_idx=characters
					r.append(text[:c_idx].strip())
					text=text[c_idx:].strip()
				r.append(text)
		
		return [(" " if l=="" else l) for l in r]
