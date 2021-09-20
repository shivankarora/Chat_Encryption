import socket
import select
import sys
from _thread import *


def clientthread(conn,addr):
	'''
	Looks at the header of a client message and takes actions for acking and
	forwarding
	Inputs: conn - the socket connection of the client
			addr - IP of the client 
	'''

	#global dictionary of registered clients on the server
	global clients
	#print(clients)

	while True:
		try:
			message = conn.recv(2048)
			message_string = str(message.decode('utf-8'))
			# print(message_string)
			if(message):
				# print("Entered")
				# A registration request for receiving data
				if(message_string[:15]=="REGISTER TORECV" and message_string[-2:]=='\n\n'):

					uname = message_string[17:-3]
					# print(uname)
					# print("receiving socket: ",conn)

					#Username should be alpha numeric
					if(not uname.isalnum()):
						conn.send(bytes("ERROR 100 MALFORMED USERNAME\n\n",'utf-8'))
						return
					try:
						li = clients[uname]
						li += ["recv_socket",conn]
						clients[uname]=li
						#print(clients)
						conn.send(bytes("REGISTERED TORECV ["+uname+"]\n\n",'utf-8')) 
					
						# DO EXCEPTION HANDLING FOR KEY ERROR if different usernames come up for send and receive sockets
					except:
						conn.send(bytes("USERNAME MISMATCH",'utf-8'))
						return
					
					
				# A registration request for receiving data
				elif(message_string[:15]=="REGISTER TOSEND" and message_string[-2:]=="\n\n"):
					
					uname = message_string[17:-3]
					# print("sending socket: ",conn)
					#Username should be alphanumeric
					if(not uname.isalnum()):
						conn.send(bytes("ERROR 100 MALFORMED USERNAME\n\n",'utf-8'))
						return

					#Username should be unique
					if(uname in list(clients.keys())):
						conn.send(bytes("EXISTING USERNAME. TRY ANOTHER ONE. CLOSING SOCKET\n",'utf-8'))
						return
					
					li = ["send_socket",conn,addr]
					clients[uname] = li
					# print(uname)
					conn.send(bytes("REGISTERED TOSEND ["+uname+"]\n\n",'utf-8')) 
					continue

				elif(message_string[:11]=="REGISTERKEY"):

					pos = message_string.index('-')
					uname = message_string[11:pos]

					li = clients[uname]
					public_key = message_string[pos+4:]
					li += [public_key]
					clients[uname] = li

					print("NEW KEY REGISTERED")

				elif(message_string[:10]=="UNREGISTER"):
					print(message_string)
					uname = message_string[11:]
					clients.pop(uname,None)
					conn.send(bytes("UNREGISTERED " + uname,'utf-8'))
					return

				elif (message_string[:8]=="FETCHKEY"):
					uname_rec = message_string[8:]
					public_key = clients[uname_rec][5]

					conn.send(bytes(public_key,'utf-8'))


					'''
					MAKE THE FORWARDING PART
					'''

				elif(message_string[:4]=="SEND"):
					# print("Reached Here")
					pos = message_string.index('\n')
					# print("Pos" + str(pos))
					uname_rec = message_string[4:pos]
					#print("Receiver " + uname_rec)
					if ("Content-Length" not in message_string):
						conn.send(bytes("ERROR 103 Header incomplete\n\n", 'utf-8'))
						clients.pop(uname)
						return

					else:
						# print("Message string: ",message_string)
						# print("Reached Here")
						#print("message_string: ",message_string)
						#print(pos)
						pos2 = message_string[(pos+1):].index('\n')
						#print(message_string[(pos+pos2+1):])
						pos3 = message_string[(pos+pos2+2):].index('\n')
						#print(pos2)
						#print(pos3)
						sub_msg = message_string[pos+pos2+16:]
						sign_send = message[pos+5:pos+pos2]
						#print("sub_msg: ",sub_msg)
						# print(sub_msg)
						#pos2 = sub_msg.index('\n');
						# print("pos2: ",pos2)
						# print("pos2 is " + str(pos2))
						length = int(sub_msg[:sub_msg.index('\n')])
						# print("length: ",length)
						# print("Length is " + str(length))		
						msg = message_string[pos+pos2+pos3+4:]
						# print("msg: ",msg)	
						# print(msg)

						for key in clients:
							if(clients[key][2]==addr):
								uname = key

						if(uname_rec not in list(clients.keys())):
							print("Error")
							conn.send(bytes("ERROR 102 Unable to send\n",'utf-8'))
							continue
						else:
							# print("No error")
							# print("Forwarded message to " + uname_rec + " is <" + msg + ">")
							try:
								conn_forward = clients[uname_rec][4]
								# print(conn_forward)
								# print(conn)
								# print("UNAME: ",uname)
								# print("MSG: ",msg)

								#print(bytes(""+uname+": "+message, 'utf-8'))
								# print(bytes(""+uname+": "+msg, 'utf-8'))
								
								conn_forward.send(bytes(""+uname+"\n "+msg+"\n ", 'utf-8')+sign_send)

								msent = conn_forward.recv(2048)
								msent_str = str(msent.decode('utf-8'))
								# print(msent_str)
								if(msent_str[:8]=="RECEIVED"):
									conn.send(bytes('SENT'+uname_rec,'utf-8'))
								else:
									conn.send(bytes("ERROR 102 Unable to send","utf-8"))
								# print("nani!")
							except:
								print("Failure to Forward -- " , sys.exc_info()[0])
								contnue
							# try:
							# 	# conn.send(bytes("SENT ["+uname_rec+"]\n\n"))
							# 	conn_forward = clients[uname_rec][4] 
							# 	print(conn_forward)
							# 	# conn_forward.send(bytes("FORWARD " + uname + "\n"+
   				# 	# 								"Content-Length" + len(message) +
   				# 	# 								 "\n\n"+ message,'utf-8'))
 
   				# 				conn_forward.send(bytes("<",uname,">: ",message))
							# except:
							# 	print("Failure to forward")
							# 	# print(clients[uname_rec][4])
							# 	continue

		except:
			continue


'''
Socket has a particular type AF_INET which 
identifies a socket by its IP and Port
SOCK_STREAM specifies that data is to be read
in continuous flow
'''
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
#No clue what the above line means

if(len(sys.argv)!=3):
	print("Correct usage: name_of_file IP Port")
	exit()

IP = str(sys.argv[1])
Port = int(sys.argv[2])

'''
Bind the server to the above specified IP and Port.
Will be used by client to connect to server
'''
server.bind((IP,Port))

#Listen for set number of active connections
active_conns = 50
server.listen(active_conns)

# global clients 
clients={}

'''
Continuously keep a socket for connecting to client. For every client, make a 
new thread to process the message according to registration request and general message
'''
while True:
	#print(clients)
	conn, addr = server.accept()
	start_new_thread(clientthread,(conn,addr))
		

conn.close()
server.close()
