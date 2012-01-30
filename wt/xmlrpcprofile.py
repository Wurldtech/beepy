import xmlrpclib
from beepy.profiles import profile
from twisted.internet import threads

uri = "http://www.wurldtech.com/profiles/XML-RPC"

#### XML-RPC marshal functions

def xmlrpc_decode(data):
    return xmlrpclib.loads(data)

def xmlrpc_encode_results(data):
    if type(data) != tuple or type(data) != list:
        data = (data,)
    return '<?xml version="1.0"?><methodResponse>' + xmlrpclib.dumps(tuple(data), None) + '</methodResponse>'

def xmlrpc_encode_error(code, descr):
    return xmlrpclib.dumps(xmlrpclib.Fault(code, descr))

def xmlrpc_encode_call(name, params):
    return xmlrpclib.dumps(tuple(params), name)

#### End of XML-RPC marshal functions

class XmlRpcError(Exception):
    def __init__(self, code, message):
        self.code = code
        Exception.__init__(self, message)


class XmlRpcServer(profile.Profile):
    
    def __init__(self, commands):
        profile.Profile.__init__(self)
        self.commands = commands
    
    def processMSG(self, msg):
        
        try:
            # Decode message and ensure it's a call
            params, funcname = xmlrpc_decode(msg.payload)
            
            # Carry out the call
            if funcname not in self.commands:
                raise XmlRpcError(2, 'Method does not exist')
            
            cmd, defer = self.commands[funcname]
            def runit():
                try:
                    result = cmd(*params)
                    self.channel.sendReply(msg.msgno, xmlrpc_encode_results(result))
                except Exception, e:
                    err = xmlrpc_encode_error(3, 'Command exception: ' + e.message)
                    self.channel.sendError(msg.msgno, err)
            
            if not defer:
                runit()
            else:
                threads.deferToThread(runit)
        
        except XmlRpcError, e:
            err = xmlrpc_encode_error(e.code, e.message)
            self.channel.sendError(msg.msgno, err)
        
        except Exception, e:
            err = xmlrpc_encode_error(3, 'Unhandled exception: ' + e.message)
            self.channel.sendError(msg.msgno, err)


class XmlRpcClient(profile.Profile):
    
    def processRPY(self, msg):
        results = xmlrpc_decode(msg.payload)
        self.handleCompleted(results[0])
    
    def processERR(self, msg):
        try:
            xmlrpc_decode(msg.payload)
        except xmlrpclib.Fault, e:
            self.handleError(e.faultCode, e.faultString)
    
    def execRpcCall(self, name, args):
        # Actually run the call
        self.channel.sendMessage(xmlrpc_encode_call(name, args))
    
    def handleCompleted(self, results):
        # User should overwrite this. By default we ignore any results
        pass
    
    def handleError(self, code, message):
        # User should overwrite this. By default we ignore any errors
        pass

