import time, logging

log=logging.getLogger(__name__)
timers_period=[]
next_period_event=None
next_period_event_time=0

def add(func, period):
	global timers_period
	timers_period.append({"function":func, "period":period, "lastrun":0, "nextrun":(time.time()+period)})
	log.debug("Going to run %s every %fs", func, period)
	schedule_period_events()

def remove(func, period=None):
	global timers_period, next_period_event, next_period_event_time
	need_reset=False
	for e in timers_period:
		if(e["function"]==func):
			if(period is None or e["period"]==period):
				timers_period.remove(e)
				need_reset=True
	if(need_reset):
		next_period_event=None
		next_period_event_time=0
		schedule_period_events()

def schedule_period_events():
	global timers_period, next_period_event, next_period_event_time
	
	for idx in range(0, len(timers_period)):
		if(next_period_event_time==0 or timers_period[idx]["nextrun"]<next_period_event_time):
			next_period_event_time=timers_period[idx]["nextrun"]
			next_period_event=idx
			#log.debug("Scheduling #%d (%s) for %f (now is %f)", idx, str(timers_period[next_period_event]["function"]), timers_period[next_period_event]["nextrun"], time.time())

def run():
	global timers_period, next_period_event, next_period_event_time
	if(next_period_event is None): return
	if(next_period_event_time<=time.time()):
		timers_period[next_period_event]["function"]()
		timers_period[next_period_event]["nextrun"]=time.time()+timers_period[next_period_event]["period"]
		next_period_event=None
		next_period_event_time=0
		schedule_period_events()
