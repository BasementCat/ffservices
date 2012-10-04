class lookup(dict):
	def __init__(self, *args):
		self.add(*args)
	
	def has(self, name):
		return self.has_key(name)
	
	def __getitem__(self, key):
		return self.has(key)
		
	def add(self, *args):
		for name in args:
			self[name]=True
		
	def remove(self, *args):
		for name in args:
			if self.has(name):
				del self[name]
