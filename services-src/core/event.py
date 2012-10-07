import logging

log=logging.getLogger(__name__)

class Handler(object):
	def __init__(self, event, callback):
		self.event=event
		self.callback=callback

class Event(object):
	events={}

	@classmethod
	def listen(self, *args):
		def handle_internal(callback):
			for event in args:
				log.debug("Adding %s in %s as handler for '%s'", callback.__name__, callback.__module__, event)
				if not event in self.events:
					self.events[event]=[callback]
				else:
					self.events[event].append(callback)
			return callback
		return handle_internal

	@classmethod
	def removeHandler(self, callback, event=None):
		for eventName, handlerList in self.events.items():
			if event is not None and eventName!=event:
				continue
			try:
				handlerList.remove(callback)
			except ValueError:
				pass

	@classmethod
	def removeModule(self, module):
		for handlerList in self.events.values():
			queue=[]
			for handler in handlerList:
				if handler.__module__==module:
					queue.append(handler)
			for handler in queue:
				handlerList.remove(handler)

	def __init__(self, eventName, *args, **kwargs):
		self.eventName=eventName
		self.handlersCalled=[]
		self.additionalHandlersCalled=[]
		self.stopped=False
		self.returnValues=[]
		self.eventArgs=args
		self.eventKWArgs=kwargs

	def __str__(self):
		return self.eventName

	def stop(self):
		self.stopped=True

	def run(self):
		currentEvent=None
		currentEventParts=[]
		for part in self.eventName.split("/"):
			currentEventParts.append(part)
			currentEvent="/".join(currentEventParts)
			if currentEvent in self.events:
				for callback in self.events[currentEvent]:
					out=callback(self, *self.eventArgs, **self.eventKWArgs)
					if self.stopped:
						log.debug("Event '%s' (%s) stopped by %s in %s", currentEvent, self.eventName, callback.__name__, callback.__module__)
						self.stopped=callback
						return
					if self.eventName==currentEvent:
						self.handlersCalled.append(callback)
						self.returnValues.append(out)
					else:
						self.additionalHandlersCalled.append(callback)

	@classmethod
	def trigger(self, *args, **kwargs):
		e=Event(*args, **kwargs)
		e.run()
		return e