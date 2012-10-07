import logging

log=logging.getLogger(__name__)

events={}
event_ownership={}
eventStopped=0
eventHadNoHandlers=0
stop_event=0

#def addHandler(event, handler_function):
def addHandler(*args):
	args=list(args)
	handler_function=args.pop()
	for event in args:
		log.debug("Adding [%s] as handler for '%s'", handler_function, event)
		if(events.has_key(event)):
			events[event].append(handler_function)
		else:
			events[event]=[handler_function]
	
		if(event_ownership.has_key(handler_function.__module__)):
			event_ownership[handler_function.__module__].append((event, handler_function))
		else:
			event_ownership[handler_function.__module__]=[(event, handler_function)]

def removeHandler(event, handler_function):
	log.debug("Removing [%s] as handler for '%s'", handler_function, event)
	if(not events.has_key(event)): return
	try:
		events[event].remove(handler_function)
	except ValueError:
		pass

def removeModuleHandlers(module):
	if(not event_ownership.has_key(module)): return
	[removeHandler(event, func) for event, func in event_ownership[module]]
	del(event_ownership[module])

def stop():
	global stop_event
	stop_event=1

def trigger(event, **kwargs):
	global events, eventStopped, eventHadNoHandlers, stop_event
	real_event=""
	real_event_parts=[]
	handlers_called=0
	eventStopped=0
	eventHadNoHandlers=0
	stop_event=0
	return_values=[]
	for event_part in event.split("/"):
		real_event_parts.append(event_part)
		real_event="/".join(real_event_parts)
		if(events.has_key(real_event)):
			for func in events[real_event]:
				returnval=func(eventname=event, **kwargs)
				if(stop_event):
					log.debug("Event '%s' (%s) stopped by [%s]", real_event, event, func)
					stop_event=0
					eventStopped=1
					return None
				if(event==real_event):
					handlers_called+=1
					return_values.append(returnval)
	if(handlers_called==0): eventHadNoHandlers=1
	return return_values
