
import socket
from rudp import Sender,Reciever
import time
import argparse
import struct

header_struct = struct.Struct('!I')

def server(selfHost,selfPort,peerHost,peerPort):
    sock=Reciever()
    sock.bind((selfHost,selfPort))
    sock.setPeer((peerHost,peerPort))




    
    data=sock.recv(header_struct.size)

    (fileSize,)=header_struct.unpack(data)

    fileData=sock.recv(fileSize)


    with open("DownloadedFile","wb") as f:
        f.write(fileData)

    sock.close()
    print("File Saved by the name : Downloaded File , Size {} Bytes".format(fileSize))
    print("Server exit")

def client(selfHost,selfPort,peerHost,peerPort,src):

    with open("./"+src,"rb") as f:
        data=f.read()
    
    size=header_struct.pack(len(data))
    # print(len(data))
    sock=Sender()
    sock.bind((selfHost,selfPort))
    sock.setPeer((peerHost,peerPort))

    sock.send(size)
    sock.send(data)


    sock.close()
    print("File Successfully Sent !!!")
    print("Client Exit")

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Send UDP packet to get MTU')
    parser.add_argument("role",help="Role of client or server")
    parser.add_argument('selfHost', help='the host to which to target the packet')
    
    parser.add_argument('selfPort', metavar='PORT', type=int, default=1060,
                        help='UDP port (default 1060)')

    parser.add_argument('peerHost', help='the host to which to target the packet')
    parser.add_argument('peerPort', metavar='PORT', type=int, default=1060,
                        help='UDP port (default 1060)')
    parser.add_argument("-i",dest="src",help="Input video file")

    args=parser.parse_args()

    if(args.role=='server'):
        server(args.selfHost,args.selfPort,args.peerHost,args.peerPort)
    else:
        client(args.selfHost,args.selfPort,args.peerHost,args.peerPort,args.src)