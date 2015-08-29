
import SocketServer
from struct import *

PORTNO = 10552

class handler(SocketServer.DatagramRequestHandler):
    def handle(self):
        newmsg = self.rfile.readline().rstrip()
        nm = _unpack(newmsg)
        print "Client %s said ``%s''" % (self.client_address[0], (nm,))
        self.wfile.write(self.server.oldmsg)
        self.server.oldmsg = newmsg

def _unpack(dat):
    __format = '>ccccffffffdddddddd??ii?ii'
    return unpack(__format, dat)


s = SocketServer.UDPServer(('',PORTNO), handler)
print "Awaiting UDP messages on port %d" % PORTNO
s.oldmsg = "This is the starting message."
s.serve_forever()
