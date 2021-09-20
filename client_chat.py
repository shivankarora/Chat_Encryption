
# Python program to implement client side of chat room. 
import socket 
import select 
import sys 
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5
from base64 import b64encode, b64decode
import ast  


def sign(message, priv_key):
	# print("priv key",priv_key)
	signer = PKCS1_v1_5.new(priv_key)
	digest = MD5.new()
	digest.update(message)
	# print(signer.sign(digest))
	# print("Sign type: ",type(signer.sign(digest)))
	return signer.sign(digest)

def verify(message, signature, pub_key):
	# print("pub key: ",pub_key)
	signer = PKCS1_v1_5.new(pub_key)
	digest = MD5.new()
	digest.update(message)
	# print(type(digest))
	# print(type(signature))
	return signer.verify(digest, signature)

random_generator = Random.new().read
key = RSA.generate(1024, random_generator) #generate public and private keys

publickey = key.publickey() # pub key export for exchange
# print(str(publickey.exportKey()))

'''
Socket has a particular type AF_INET which 
identifies a socket by its IP and Port
SOCK_STREAM specifies that data is to be read
in continuous flow
'''
hang=10
server_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server_rec = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Define correct usage
if len(sys.argv) != 4: 
    print("Correct usage: script, IP address, port number username")
    exit() 

IP_address = str(sys.argv[1]) 
Port = int(sys.argv[2]) 
uname = str(sys.argv[3])

# print("-------------------" + uname + "----------------------")
#print(publickey.exportKey())
#print(key.exportKey())

'''
Creating two sockets, one for sending, and the other for receiving
'''
server_send.connect((IP_address, Port)) 
server_rec.connect((IP_address,Port))

'''
Sends message to the server for registering the user. Expects an ACK and only then proceeds for 
data forwarding among users
'''
register_msg_send = "REGISTER TOSEND ["+uname+"]\n\n"
register_msg_rec = "REGISTER TORECV ["+uname+"]\n\n"

server_send.send(bytes(register_msg_send,'utf-8'))
# print("waiting")
ack_send = server_send.recv(2048)
ack_send = ack_send.decode('utf-8')
# print(ack_send)
if(ack_send != "REGISTERED TOSEND ["+uname+"]\n\n"):
    print(ack_send)
    print("closed")
    server_send.close()
    exit()

server_rec.send(bytes(register_msg_rec,'utf-8'))

ack_rec = server_rec.recv(2048)
# print(ack_rec)
ack_rec = ack_rec.decode('utf-8')
# print(ack_rec)
if(ack_rec !="REGISTERED TORECV ["+uname+"]\n\n"):
    print(ack_rec)
    #print("Here2")
    server_rec.close()
    exit()
# print("SENT PUBLIC KEY: ",publickey)
temp = key.publickey().exportKey(format='PEM', passphrase=None, pkcs=1)
# print(temp)
# print(type(key.publickey().exportKey(format='PEM', passphrase=None, pkcs=1)))
# print("SERVER: ",bytes("REGISTERKEY" + uname + "-KEY" ,'utf-8')+temp)
server_send.send(bytes("REGISTERKEY" + uname + "-KEY" ,'utf-8')+temp)

  
while True: 
	# print("Here")

	# read_sockets,write_socket, error_socket = select.select(sockets_list,[],[])
	inputs_list = [sys.stdin, server_rec, server_send]
	read_sockets, write_sockets, error_sockets = select.select(inputs_list,[],[])

	for inp_socket in read_sockets:
		# print(inp_socket)
		if inp_socket == server_rec:

			try:
				# print("caught a message")
				message20 = server_rec.recv(2048)
				# print("message20: ",message20)
				message2 = str(message20.decode('utf-8'))
				# print(type(message2))
				message2 = message2.replace("\r\n","")
				pos1 = message2.index('\n')
				pos2 = message2[(pos1+1):].index('\n')

				sign_recv = message20[pos1+pos2+3:]
				# print("sign_recv: ",sign_recv)
				# print("Message2: ",message2)
				
				# print("recieved")
				#message2 = str(message20.decode('utf-8'))
				# print("message2",message2)
				#print("message2",message2)

				uname = message2[:message2.index('\n')]
				# print("Uname: ",uname)
				rest1 = message2[message2.index('\n')+2 : pos1+pos2+1]
				# print("rest1: ",rest1)
				# print("key: ",key.exportKey())
				#print(type(rest))
				#print(type(ast.literal_eval(str(rest))))
				# print("REST1: ",rest1)
				rest = key.decrypt(eval((rest1)))
				# print("REST: ",rest)
				# print("rest: ",rest)
				#print(ast.literal_eval(str(rest))	)
				#pos = message2.index('\n')
				#uname = message2[7:pos]
				#if (message2[pos+1:pos+15]!="Content-Length"):
				#	server_send.send("ERROR 103 Header Incomplete")
				#else:
				#print(uname)
				server_send.send(bytes("FETCHKEY" + uname,'utf-8'))
				pub_key_rec = server_send.recv(2048)
				pub_key_rec = RSA.importKey(pub_key_rec, passphrase=None) 

				# print(type(sign_recv))
				# print(b64decode(sign_recv+b'===='))
				verified = verify(rest,(b64decode(sign_recv+b'====')),pub_key_rec)
				# print("Verified: ",verified)
				server_rec.send(bytes("RECEIVED "+ uname +"\n\n",'utf-8'))
				# print("sent RECEIVED")
				#sub_msg = message2[pos+15:]
				#pos2 = sub_msg.index('\n');
				#length = int(sub_msg[:pos2])		
				#output = sub_msg[pos2+2:pos2+2+length]		
				# print("rest: ",rest)
				#sys.stdout.write("#" + uname + ": " + output)
				# print("Error in the below line")
				sys.stdout.write("#" + uname + ": " + str(rest.decode('utf-8')))
				# print("Error in the above line")


			except:
				hang-=1
				if(hang==0):
					print("Socket crashed")
					exit()
				print("Nothing")
				continue

		elif inp_socket==sys.stdin:

			# try:
			message1 = sys.stdin.readline() 
			if(message1[:10]=="UNREGISTER"):
				server_send.send(bytes("UNREGISTER " + uname,'utf-8'))
				msg = server_send.recv(2048)
				msg = str(msg.decode('utf-8'))
				print(msg)
				server_send.close()
				server_rec.close()
				exit()

			else:
				assert(message1[0]=='@')
				pos = message1.index(':')
				uname_rec = message1[1:pos]
				message = message1[pos+1:]
				server_send.send(bytes("FETCHKEY" + uname_rec,'utf-8'))
				pub_key_rec = server_send.recv(2048)
				# print("reeived public key: ",pub_key_rec)
				#pub_key_rec = pub_key_rec.decode('utf-8')
				#print(pub_key_rec)
				# pub_key_rec = RSA.importKey(pub_key_rec)
				# print(pub_key_rec.can_encrypt())
				pub_key_rec = RSA.importKey(pub_key_rec, passphrase=None) 
				# print("vds:",pub_key_rec)
				# print("message: ",message.encode('UTF-8'))
				# print("message: ",type(message.encode('UTF-8')))
				encrypted = pub_key_rec.encrypt(message.encode('UTF-8'),32)
				# print(encrypted)
				# print(type(encrypted))
				# print("MESSAGE: ",message)
				#salt
				# print(sign(message.encode('utf-8'),key))
				sign_send = b64encode(sign(message.encode('utf-8'),key))

				server_send.send(bytes("SEND" + uname_rec + "\nSIGN",'utf-8') + sign_send + bytes( "\n"+
						"Content-Length" + str(len(message)) + "\n\n"+ str(encrypted),'utf-8')) 
				
				sys.stdout.write("<You>: "+message)
				# except:
				# 	print("input error")
				# 	continue

		else:
			try:
				ack_rec = server_send.recv(2048)
				ack_rec1 = ack_rec.decode('utf-8')
				#print(ack_rec1)
				if(ack_rec1[:4]!="SENT"):
					print(ack_rec1)	
				elif(ack_rec1[:9]=="ERROR 102"):
					print(ack_rec1)

				# else:
				# 	sys.stdout.write("<You>: " + message) 
			except:
				print("1st continue error")
				continue

	# try:
	# 	message2 = server_rec.recv(2048)
	# 	message2 = message2.decode('utf-8')
	# 	uname = message2[message2.index('<')+1 : message2.index('<')]
	# 	#pos = message2.index('\n')
	# 	#uname = message2[7:pos]
	# 	#if (message2[pos+1:pos+15]!="Content-Length"):
	# 	#	server_send.send("ERROR 103 Header Incomplete")
	# 	#else:
	# 	server_send.send("RECEIVED "+ uname +"\n\n")

	# 	#sub_msg = message2[pos+15:]
	# 	#pos2 = sub_msg.index('\n');
	# 	#length = int(sub_msg[:pos2])		
	# 	#output = sub_msg[pos2+2:pos2+2+length]		

	# 	#sys.stdout.write("#" + uname + ": " + output)
	# 	sys.stdout.write("#" + uname + ": " + message2)
	# except:
	# 	print("Nothing")
	# 	continue
 

	#sys.stdout.write(message) 
	#ack_rec = server_rec.recv(2048)
	#ack_rec = ack_rec.decode('utf-8')

	#if(ack_rec[:4]!=SENT):
	#	print(ack_rec)
	#	server_send.close()
	#	exit()

	#sys.stdout.flush() 
server.close() 
