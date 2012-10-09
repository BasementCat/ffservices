from core import log
from core.Pseudoclient import Pseudoclient

dev_null_serv=None

def module_start():
	global dev_null_serv
	dev_null_serv=Pseudoclient.create("DevNullServ", "DevNullServ", "devnull", "services.client", "Message sink")
	if(dev_null_serv in (False, None)):
		log.info("DevNullServ: Can't create pseudoclient!")
		return False
	dev_null_serv.help="""DevNullServ - Message sink.

Any messages sent to DevNullServ (with the exception of HELP) will be ignored."""
	return True

def module_stop():
	global dev_null_serv
	dev_null_serv.remove()
	return True
