from core import config, log, event, Database, Network, ffservices
from core.Pseudoclient import Pseudoclient
from core.PseudoclientCommand import PseudoclientCommand
from core.IRCMessage import IRCMessage
from core.Client import Client
import time, random, hashlib

db_cursor=nickserv=None

def module_start():
	global db_cursor, nickserv
	try:
		db_cursor=Database.conn.cursor()
		nickserv=Pseudoclient.create("NickServ", "NickServ", "nickserv", config.get("Services/DefaultHostname"), "Nickname registration and protection service")
		if(nickserv is None): raise Exception("A pseudoclient with this service name already exists (NickServ)")
		if(nickserv is False): raise Exception("A pseudoclient with this nick already exists (NickServ)")
		
		try:
			db_cursor.execute("describe `ff_nickserv_core`")
		except Exception:
			#the table isn't there, now try to create it
			db_cursor.execute("""
				CREATE TABLE  `ff_nickserv_core` (
					`id` BIGINT( 1 ) NOT NULL AUTO_INCREMENT PRIMARY KEY ,
					`nick` VARCHAR( 128 ) NOT NULL ,
					`password` VARCHAR( 256 ) NOT NULL ,
					`email` VARCHAR( 256 ) NULL ,
					`time_registered` BIGINT( 1 ) NOT NULL ,
					`time_last_seen` BIGINT( 1 ) NOT NULL ,
					`email_confirmed` BOOLEAN NOT NULL ,
					`activated` BOOLEAN NOT NULL ,
					`disabled` BOOLEAN NOT NULL ,
					`group` BIGINT( 1 ) NULL DEFAULT NULL ,
					`confirmation_code` VARCHAR( 64 ) NULL DEFAULT NULL ,
					INDEX (  `time_registered` ,  `time_last_seen` ,  `email_confirmed` ,  `activated` ,  `disabled` ,  `group` ,  `confirmation_code` )
				) ENGINE = MYISAM CHARACTER SET utf8 COLLATE utf8_unicode_ci;
				""")
	except Exception as e:
		log.error("Can't start ff_NickServ: %s", str(e))
		return False
	
	nickserv.help="""\x02NickServ\x02 - Nickname registration and protection service.

\x02NickServ\x02 allows nicknames to be registered to a particular user to prevent others from using them.  Abuse of the service for stealing others' nicknames is not permitted and may result in a network ban.
The available commands are listed below, if you require help with any of them type \x02/msg NickServ help \x1fcommand\x1f\x02."""
	
	nickserv.addCommand(PseudoclientCommand("register", handle_cmd_register, "Register your current nickname", """Syntax: \x02/msg NickServ register \x1fpassword\x1f [\x1femail\x1f]\x02

The \x02register\x02 command registers your current nickname with \x02NickServ\x02.  To register a nickname, the nickname must not already be registered, and it must be a nickname that is permitted by the IRCD.  A valid email address may be required on some networks in order to activate the nickname registration."""
		))
	nickserv.addCommand(PseudoclientCommand("identify", handle_cmd_identify, "Identify yourself using your password", """Syntax: \x02/msg NickServ identify \x1fpassword\x1f\x02

The \x02identify\x02 command identifies you as owning your nick, and allows you to access additional features of NickServ."""
		))
	nickserv.addCommand(PseudoclientCommand("unidentify", handle_cmd_unidentify, "Remove your status as an identified user", """Syntax: \x02/msg NickServ unidentify\x02

The \x02unidentify\x02 command removes your identified status if you have previously identified."""
		))
	nickserv.addCommand(PseudoclientCommand("group", handle_cmd_group, "Group your current nick with another nick", """Syntax: \x02/msg NickServ group [\x1fprimarynick password\x1f]\x02

The \x02group\x02 command allows you to group your current nick with your primary nick, allowing you to use it for identification and to prevent others from using it.  If you have previously identified you do not have to supply any parameters, however if you are not identified you will have to supply your primary nickname (or any nickname grouped with that nickname) and your password."""
		))
	nickserv.addCommand(PseudoclientCommand("glist", handle_cmd_glist, "List the nicknames that are in your group", """Syntax: \x02/msg NickServ glist\x02

The \x02glist\x02 command lists all of the nicknames currently in your group."""
		))
	
	return True

def module_stop():
	global db_cursor, nickserv
	db_cursor.close()
	nickserv.remove()
	return True

def hash_password(nick, password):
	algo=config.get("Services/ff_NickServ/Passwords/Hash")
	salt=config.get("Services/ff_NickServ/Passwords/Salt")
	if(salt is True): salt=nick.lower()
	if(algo is None): return password
	h=hashlib.new(algo)
	h.update(password)
	h.update(salt)
	return h.hexdigest()

def nick_is_registered(nick):
	global db_cursor
	try:
		db_cursor.execute("select count(`nick`) from `ff_nickserv_core` where `nick` like %s", (nick))
		existing_nick_count=db_cursor.fetchone()[0]
		if(existing_nick_count>0): return True
		return False
	except Exception as e:
		log.error("%s", str(e))
		return True

def authenticate(nick, password, real_password=None):
	global db_cursor
	if(real_password is None):
		try:
			db_cursor.execute("select `password` from `ff_nickserv_core` where `nick` like %s", (nick))
			real_password=db_cursor.fetchone()[0]
		except Exception as e:
			log.error("%s", str(e))
			return None
	if(hash_password(nick, password)==real_password): return True
	return False

def handle_cmd_register(source, command, c_text):
	global db_cursor, nickserv
	c_params=c_text.split()
	if(len(c_params)==0):
		nickserv.sendMsg(source, "The \x02register\x02 command required at least one argument.")
		return
	
	if(len(c_params)==1 and config.get("Services/ff_NickServ/Registration/RequireEmail")):
		nickserv.sendMsg(source, "A valid email address is required to register your nickname.")
		return
	
	try:
		#db_cursor.execute("select count(`nick`) from `ff_nickserv_core` where `nick` like %s", (source))
		#existing_nick_count=db_cursor.fetchone()[0]
		#if(existing_nick_count>0):
		#	nickserv.sendMsg(source, "The nick \x02%s\x02 is already registered.", source)
		#	return
		if(nick_is_registered(source)): #will return true if an error is encountered to prevent registration of the same nick twice
			nickserv.sendMsg(source, "The nick \x02%s\x02 is already registered.", source)
			return
		
		conf_code=hashlib.md5(str(random.random())+str(time.time())).hexdigest()
		
		db_cursor.execute("""insert into `ff_nickserv_core` (`nick`,`password`,`email`,`time_registered`,`time_last_seen`,`email_confirmed`,`activated`,`disabled`,`group`,`confirmation_code`)
			values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (
			source,
			hash_password(source, c_params[0]),
			c_params[1] if len(c_params)>1 else None,
			long(time.time()),
			long(time.time()),
			0 if config.get("Services/ff_NickServ/Registration/RequireEmail Confirmation") else 1,
			0 if config.get("Services/ff_NickServ/Registration/RequireOperActivation") else 1,
			0,
			None,
			conf_code
			))
		
		if(config.get("Services/ff_NickServ/Registration/RequireEmail Confirmation")):
			#todo: send email
			#if email fails, delete the nick and display an error
			nickserv.sendMsg(source, "An activation email has been sent to \x02%s\x02 with a confirmation code.  When you have recieved the email, you will have to enter the command \x02/msg NickServ confirm \x1fconfirmationcode\x1f\x02.  Until you do so, you will not be able to identify with this nickname.", c_params[1])
		
		if(config.get("Services/ff_NickServ/Registration/RequireOperActivation")):
			nickserv.sendMsg(source, "You will not be able to identify using this nickname until an IRC operator has activated your account.")
		
		nickserv.sendMsg(source, "The nickname \x02%s\x02 has been registered using the password \x02%s\x02 - please memorize your password or keep it in a safe place, as it may be impossible to retrieve it.", source, c_params[0])
		log.info("NickServ: Registering new nick and creating group for '%s' (email: %s)", source, c_params[1] if len(c_params)>1 else "none")
	except Exception as e:
		nickserv.sendMsg(source, "There was a problem registering your nickname.")
		log.error("Can't register nick %s: %s", source, str(e))
	
	return False

def handle_cmd_identify(source_s, command, c_text):
	global db_cursor, nickserv
	client=Client.findByNick(source_s)
	if(client is None):
		nickserv.sendMsg(source_s, "You do not seem to exist.  This is a bug, please report it.")
		return
	
	if(client.hasMode("r")):
		nickserv.sendMsg(source_s, "You have already identified.")
		return
	
	try:
		db_cursor.execute("select * from `ff_nickserv_core` where `nick` like %s limit 1", (source_s))
		if(db_cursor.rowcount==0):
			nickserv.sendMsg(source_s, "Nick \x02%s\x02 is not registered.", source_s)
			return
		u_id, nick, password, email, time_registered, time_last_seen, email_confirmed, activated, disabled, group, confirmation_code=db_cursor.fetchone()
		if(len(c_text)==0):
			nickserv.sendMsg(source_s, "You must supply a password.")
			return
		#elif(password==hash_password(source_s, c_text)):
		elif(authenticate(source_s, c_text, password)):
			if(not email_confirmed):
				nickserv.sendMsg(source_s, "You have not confirmed your email address.")
				return
			elif(not activated):
				nickserv.sendMsg(source_s, "Your account has not yet been activated.")
				return
			elif(disabled):
				nickserv.sendMsg(source_s, "Your account has been disabled.")
				return
			
			client.changeModes("+r")
			groupid=group if group is not None else u_id
			Network.sendMsg(IRCMessage(":", nickserv.nick, "SVS2MODE", source_s, "+rd", groupid))
			client.servicestamp=groupid
			#using mode +d with svsmode or svs2mode changes the services stamp
			#in this case we set it to the user's group ID
			db_cursor.execute("update `ff_nickserv_core` set `time_last_seen`=%s where id=%s limit 1", (time.time(), u_id))
			nickserv.sendMsg(source_s, "You are now identified for nick \x02%s\x02.", nick)
		else:
			nickserv.sendMsg(source_s, "Invalid password.")
			return
	except Exception as e:
		log.error("Can't identify user %s: %s", source_s, str(e))
		nickserv.sendMsg(source_s, "A problem was encountered -- this is likely a bug, please report it.")

def handle_cmd_unidentify(source_s, command, c_text):
	global db_cursor, nickserv
	client=Client.findByNick(source_s)
	if(client is None):
		nickserv.sendMsg(source_s, "You do not seem to exist.  This is a bug, please report it.")
		return
	
	if(not client.hasMode("r")):
		nickserv.sendMsg(source_s, "You are not identified.")
	else:
		client.changeModes("-r")
		Network.sendMsg(IRCMessage(":", nickserv.nick, "SVS2MODE", source_s, "-r"))
		nickserv.sendMsg(source_s, "You are no longer identified.")

def handle_cmd_group(source_s, command, c_text):
	global db_cursor, nickserv
	params=c_text.split()
	if(nick_is_registered(source_s)):
		nickserv.sendmsg(source_s, "Nick \x02%s\x02 is already registered.", source_s)
	elif(len(params)==1):
		nickserv.sendMsg(source_s, "You must either supply both a registered nickname and a password, or nothing (if you are already identified).")
	elif(len(params)>1):
		if(not nick_is_registered(params[0])):
			nickserv.sendMsg(source_s, "Nick \x02%s\x02 is not registered.", params[0])
			return
		
		try:
			db_cursor.execute("select `id`,`password`,`group` from `ff_nickserv_core` where `nick` like %s limit 1", (params[0]))
			u_id, password, group=db_cursor.fetchone()
		except Exception as e:
			log.error("%s", str(e))
			nickserv.sendMsg(source_s, "Your nick cannot be grouped at this time.")
			return
		groupid=group if group is not None else u_id
		if(not authenticate(params[0], params[1], password)):
			nickserv.sendMsg(source_s, "Incorrect password.")
			return
	else:
		client=Client.findByNick(source_s)
		#TODO: check if client is none
		if(not client.hasMode("r")):
			nickserv.sendMsg(source_s, "You are not identified.")
			return
		
		groupid=client.servicestamp
	
	try:
		db_cursor.execute("""insert into `ff_nickserv_core` (`nick`,`password`,`email`,`time_registered`,`time_last_seen`,`email_confirmed`,`activated`,`disabled`,`group`,`confirmation_code`)
			select %s as `nick`,`password`,`email`,UNIX_TIMESTAMP() as `time_registered`, UNIX_TIMESTAMP() as `time_last_seen`, `email_confirmed`, `activated`, `disabled`, `id` as `group`, `confirmation_code`
			from `ff_nickserv_core` where `id`=%s limit 1""", (source_s, groupid))
		db_cursor.execute("select `nick` from `ff_nickserv_core` where `id`=%s limit 1", (groupid))
		nickserv.sendMsg(source_s, "You are now in the group of \x02%s\x02.", db_cursor.fetchone()[0])
	except Exception as e:
		nickserv.sendMsg(source_s, "Your nick cannot be grouped at this time.")
		log.error("Can't group %s in group #%d: %s", source_s, groupid, str(e))

def handle_cmd_glist(source_s, command, c_text):
	global db_cursor, nickserv
	client=Client.findByNick(source_s)
	if(not client.hasMode("r")):
		nickserv.sendMsg(source_s, "You are not registered.")
		return
	
	try:
		db_cursor.execute("select `nick`, `time_registered`, `time_last_seen` from `ff_nickserv_core` where `id`=%s or `group`=%s order by `id` asc", (client.servicestamp, client.servicestamp))
		nickserv.sendMsg(source_s, "Nicknames in the group of \x02%s\x02:", source_s)
		for g_data in db_cursor.fetchall():
			nickserv.sendMsg(source_s, "\x02%s\x02 (Registered %s ago, last seen %s ago)", g_data[0], ffservices.formatTimeDiff(g_data[1], time.time(), False), ffservices.formatTimeDiff(g_data[2], time.time(), False))
	except Exception as e:
		log.error("%s", str(e))
