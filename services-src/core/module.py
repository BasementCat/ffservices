import logging
import config, ffservices, sys, event

log=logging.getLogger(__name__)

modules={}

def load(module_name):
	try:
		real_module_name="modules."+module_name
		__import__(real_module_name)
		module=sys.modules[real_module_name]
	except Exception as e:
		log.error("Module failed to load: %s: %s", module_name, str(e))
		return False
	
	try:
		module.module_start
		module.module_stop
	except AttributeError:
		log.error("Module %s does not define both module_start and module_stop", module_name)
		return False
	
	if(not module.module_start()):
		log.error("Module %s failed to start", module_name)
		return False
	
	log.info("Module %s loaded", module_name)
	modules[module_name]=module
	return True

def unload(module_name):
	if(not modules.has_key(module_name)):
		log.info("Module %s is not loaded", module_name)
		return True
	
	module=modules[module_name]
	del(modules[module_name])
	
	event.removeModuleHandlers("modules."+module_name)
	if(not module.module_stop()):
		log.warning("Module %s failed to stop - this could lead to errors", module_name)
		return False
	
	log.info("Module %s unloaded", module_name)
	return True

def unloadAll():
	#[module.module_stop() for modname, module in modules]
	for modname in modules:
		modules[modname].module_stop()

def loadConfigured():
	[load(modname) for modname in config.get("Modules")]
