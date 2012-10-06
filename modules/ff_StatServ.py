from core import config, log, event, Database, Network, ffservices, Timer
from core.Pseudoclient import Pseudoclient
from core.PseudoclientCommand import PseudoclientCommand
from core.IRCMessage import IRCMessage
from core.Client import Client
import time

db_cursor=None
statserv=None
my_channels={}

def module_start():
	global db_cursor, statserv
	try:
		db_cursor=Database.conn.cursor()
		statserv=Pseudoclient.create("StatServ", "StatServ", "statserv", config.get("Services/DefaultHostname"), "Network statistics tracker")
		if(statserv is None): raise Exception("A pseudoclient with this service name already exists (StatServ)")
		if(statserv is False): raise Exception("A pseudoclient with this nick already exists (StatServ)")
		
		try:
			db_cursor.execute("describe `ff_statserv_lusers`")
		except Exception:
			db_cursor.execute("""CREATE TABLE  `ff_statserv_lusers` (
				`time` BIGINT( 1 ) NOT NULL ,
				`normal_users` BIGINT( 1 ) NOT NULL ,
				`invisible_users` BIGINT( 1 ) NOT NULL ,
				`servers` BIGINT( 1 ) NOT NULL ,
				PRIMARY KEY (  `time` ) ,
				INDEX (  `normal_users` ,  `invisible_users` ,  `servers` )
				) ENGINE = MYISAM ;""")
			db_cursor.execute("""ALTER TABLE  `ff_statserv_lusers` ADD  `opers` BIGINT( 1 ) NOT NULL ,
				ADD INDEX (  `opers` )""")
			db_cursor.execute("""ALTER TABLE  `ff_statserv_lusers` ADD  `channels` BIGINT( 1 ) NOT NULL ,
				ADD INDEX (  `channels` )""")
			
			db_cursor.execute("""CREATE TABLE  `ff_statserv_channels` (
				`time` BIGINT( 1 ) NOT NULL ,
				`channel` VARCHAR( 128 ) NOT NULL ,
				`nick` VARCHAR( 128 ) NOT NULL ,
				`nickserv_groupid` BIGINT( 1 ) NULL DEFAULT NULL ,
				`message_type` VARCHAR( 16 ) NOT NULL ,
				`message` VARCHAR( 2048 ) NOT NULL ,
				PRIMARY KEY (  `time` ) ,
				INDEX (  `nickserv_groupid` )
				) ENGINE = MYISAM ;""")
			db_cursor.execute("""ALTER TABLE  `ff_statserv_channels` CHANGE  `time`  `time` DOUBLE NOT NULL""")
	except Exception as e:
		log.error("Can't start ff_StatServ: %s", str(e))
		return False
	
	Timer.add(do_lusers_update, 60)
	#every 60 seconds works out to a little over 500,000 rows per year, which is
	#pretty acceptible -- stats probably do not need to be kept longer than a few
	#months, anyway
	event.addHandler("Message/Incoming", do_log_channel_msgs)
	return True

def module_stop():
	global db_cursor, statserv
	db_cursor.close()
	statserv.remove()
	Timer.remove(do_lusers_update)
	return True

def do_lusers_update():
	global db_cursor
	#log.debug(str(ffservices.stats))
	try:
		db_cursor.execute("insert into `ff_statserv_lusers`(`time`,`normal_users`,`invisible_users`,`servers`,`opers`,`channels`) values (UNIX_TIMESTAMP(), %s, %s, %s, %s, %s)", (
			ffservices.stats["normal"],
			ffservices.stats["invisible"],
			ffservices.stats["servers"],
			ffservices.stats["opers"],
			ffservices.stats["channels"]
			))
	except Exception as e:
		log.warning("Can't update LUSERS stats for statserv: %s", str(e))

def do_log_channel_msgs(eventname, message):
	global db_cursor, statserv, my_channels
	#this will end up being called on every incoming message (or at least quite a few of them) so we kind of have to do some extra sanity checks
	if(len(message.parameters)<1): return #definitely not something we're interested in
	#we have to know what channels to log - we'll join anything that we're invited to
	if(message.command=="INVITE"):
		if(message.parameters[0].lower()==statserv.nick.lower()):
			Network.sendMsg(IRCMessage(":", statserv.nick, "JOIN", message.parameters[1]))
			my_channels[message.parameters[1].lower()]=True #using a dict here because key lookup in a dict is probably faster than using in
		return #ignore invite messages, even if they're not for us
	#messages targeted at a channel should always have a "#" character as the first character of their first parameter (the message's target)
	if(not message.parameters[0][0]=="#"): return
	#finally, if we're not supposed to be in a particular channel, we don't log messages for it
	if(not my_channels.has_key(message.parameters[0].lower())): return
	
	client=Client.findByNick(message.source)
	#this will not work if the service stamp contains something other than nickserv's group id for that nick
	cl_groupid=client.servicestamp if (client is not None and client.hasMode("r")) else None
	
	try:
		db_cursor.execute("insert into `ff_statserv_channels`(`time`, `channel`, `nick`, `nickserv_groupid`, `message_type`, `message`) values (%s, %s, %s, %s, %s, %s)", (
			time.time(),
			message.parameters[0],
			message.source,
			cl_groupid,
			message.command,
			" ".join(message.parameters[1:]) #hopefully this won't fuck up
			))
	except Exception as e:
		log.warning("Can't update channel stats: %s", str(e))
