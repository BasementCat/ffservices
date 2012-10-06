import log, yaml

config=dict()

def load(fromFile):
	global config
	with open(fromFile, 'r') as fp:
		config=yaml.load(fp)

def set(key, value):
	raise DeprecationWarning("Setting configuration values programmatically is no longer supported")

def get(key, default=None):
	global config
	curconfig=config
	for part in key.split("/"):
		if isinstance(curconfig, dict):
			if part not in curconfig:
				return default
			curconfig=curconfig[part]
		elif isinstance(curconfig, list):
			part=int(part)
			if part<0 or part>=len(curconfig):
				return default
			curconfig=curconfig[part]
	return curconfig