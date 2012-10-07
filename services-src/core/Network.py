import config, log
from core.event import Event
import socket, select
from Server import Server
from IRCMessage import IRCMessage

svr_sock=None
isConnected=False
isAuthed=False

def connect():
	global svr_sock, isConnected
	try:
		svr_sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		svr_sock.connect((config.get("Network/Server"), config.get("Network/Port")))
		isConnected=True
	except Exception as e:
		log.error("Failure to connect to server: %s:%d : %s", config.get("Network/Server"), config.get("Network/Port"), str(e))
		return False
	
	Event.trigger("Network/Connect")
	return True

def disconnect():
	global svr_sock, isConnected, isAuthed
	isConnected=False
	isAuthed=False
	Event.trigger("Network/Disconnect")
	if(svr_sock is None): return True
	svr_sock.close()
	return True

def sendToUmode(source, umode, *args):
	if(source is not None):
		if(source[0] in (":", "@")):
			source_type=source[0]
		else:
			source_type=":"
		source=source[1:]
	elif(source is None):
		source_type=":"
		source=config.get("Server/Name")
	return sendf(source_type+source, "SMO", umode, *args)

def send(*args):
	global svr_sock
	return svr_sock.send(args[0] % args[1:])

def sendf(*args):
	args=list(args)
	if(args[0][0] in (":", "@")):
		src_type=args[0][0]
		source=args.pop(0)[1:]
	else:
		#if(Server.getLinkedServer().protoctl["NS"]):
		#	src_type="@"
		#	source=config.get("Server/Numeric")
		#else:
		src_type=":"
		source=config.get("Server/Name");
	return sendMsg(IRCMessage(src_type, source, *args))

def sendMsg(msg):
	global svr_sock
	Event.trigger("Message/Outgoing/"+msg.command, message=msg)
	return svr_sock.send(str(msg))

def recv(max_buf):
	global svr_sock
	return svr_sock.recv(max_buf)

def isReady(timeout):
	global svr_sock
	in_ready,out_ready,except_ready=select.select([svr_sock], [], [], timeout)
	if(len(in_ready)>0):
		return True
	
	return False
