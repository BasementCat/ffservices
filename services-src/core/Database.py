import MySQLdb, logging
import config

log=logging.getLogger(__name__)
conn=None

def init():
	global conn
	try:
		conn=MySQLdb.connect(
			host=config.get("MySQL/Host"),
			user=config.get("MySQL/Username"),
			passwd=config.get("MySQL/Password"),
			db=config.get("MySQL/Database")
			)
	except MySQLdb.Error as e:
		log.critical("Mysql error %d: %s", e.args[0], e.args[1])
		return False
	return True

def commit():
	global conn
	return conn.commit()
