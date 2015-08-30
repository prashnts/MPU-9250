import socket
import sys

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print ('Failed to create socket')
    sys.exit()

host = 'localhost';
port = 10552;

while(1) :
    
    try :
        msg = input('Enter message to send : ')
        
        #Set the whole string
        s.sendto(msg.encode('utf-8'), (host, port))

        # receive data from client (data, addr)
        d = s.recvfrom(1024)
        reply = d[0]
        addr = d[1]

        print ('Server reply : ' + reply.decode("utf-8"))
    
    # Some problem sending data ??
    except socket.error as e:
        print ('Error Code : ' + str(e[0]) + ' Message ' + e[1])
        sys.exit()
    
    # Ctrl + C
    except KeyboardInterrupt:
        break

print('Program Complete')