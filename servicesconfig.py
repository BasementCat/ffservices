global CONFIG
CONFIG={
	"Network":{
		"Server":	"localhost",
		"Port":		7000,
		"Password":	"password"
	},
	"Server":{
		"Name":			"services.server",
		"Description":	"Services server",
		"Numeric":		64
	},
	"MySQL":{
		"Host":		"localhost",
		"Username":	"ffservices",
		"Password":	"fjQELsLGCtc5KKxw",
		"Database":	"ffservices"
	},
	"Modules":[
		"print_messages",
		"DevNullServ",
		"ff_NickServ",
		"ff_StatServ",
		
		"ffs_core",
		"ffs_core_log",
		"ffs_core_network_auth",
		"ffs_core_server",
		"ffs_core_client",
		"ffs_core_channel"
	],
	"Services":{
		"Default Pseudoclient Hostname":"network.service",
		"ff_NickServ":{
			"Passwords":{
				"Hash":		None,	#use None to store plaintext passwords, otherwise whatever is supported by the hashlib module
				"Salt":		True	#Set to True to use the user's nickname as the salt, or to a string value to use that as the salt
			},
			"Registration":{
				"Require Email":				True,
				"Require Email Confirmation":	False,
				"Require Oper Activation":		False
			}
		}
	}
}
