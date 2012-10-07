import log
config={"":{}}

def getDict(key=None, createMissingDicts=0):
	if(key==None or key==""): return config
	current_dict=config[""]
	last_dict=None
	for temp_key in key.split("/"):
		if(not current_dict.has_key(temp_key)):
			if(createMissingDicts):
				current_dict[temp_key]={}
			else:
				return None
		last_dict=current_dict
		current_dict=current_dict[temp_key]
	#return current_dict
	return last_dict

def set(key, value):
	key=key.strip(" /")
	temp_dict=getDict(key, 1)
	temp_dict[key.split("/").pop()]=value

def get(key):
	clean_key=key.strip(" /")
	final_key=key.split("/").pop()
	temp_dict=getDict(clean_key)
	if(temp_dict==None or not temp_dict.has_key(final_key)): return None
	return temp_dict[final_key]

def load(configfile):	#can raise IOError, SyntaxError
	global CONFIG
	CONFIG={}
	execfile(configfile, globals(), locals())
	set("/", CONFIG)
