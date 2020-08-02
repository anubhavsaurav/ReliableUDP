import socket
import struct
import select
import argparse

import random
import hashlib

class Packet(object):
    
    
    CONTROL_PKT=1
    SYN_PKT=1
    SYNACK_PKT=2
    ACK=3
    FIN=4
    SHUD=9
    DATA_PKT=2
    STATE=0
    def __init__(self,data=None,seq=0,datatype="data",con_pkt_code=1):
        if(datatype=="control"):
            self.pktType=self.CONTROL_PKT
        else:
            self.pktType=self.DATA_PKT

        self.conPktCode=con_pkt_code
        self.data=data
        if(data is None):
            self.checksum=hashlib.md5(b"").digest()
        else:
            self.checksum=hashlib.md5(self.data).digest()
        self.seq=seq
        self.delim=b'(:|BYE|:)'
    

    def pack(self):
        
        data=self.data
        
        if(data is None):
            self.length=0
            data=b''
        else:
            self.length=len(data)
        data+=self.delim
        return struct.pack("II16sII%ds"%(self.length+len(self.delim)),self.length,self.seq,self.checksum,self.pktType,self.conPktCode,data)

    def unpack(self,data):
        ''' Unpacks packed binary data and overwrites the contents of the packet Object with new data'''

        self.length,self.seq,self.checksum,self.pktType,self.conPktCode=struct.unpack("II16sII",data[:32])
        
        if(self.length != 0):
            (self.data,)=struct.unpack("%ds"%(self.length+len(self.delim)),data[32:])
            sliceInd=-1*len(self.delim)
            self.data=self.data[:sliceInd]
            # print(self.data)
        return self







ACK_TIMEOUT=0.1
MAX_RESEND_TRY=6969
DELIM_LEN=6
class SendUtil():




    @staticmethod
    def recvall(s,retaddr=True,delim=b"(:|BYE|:)"):

        '''TO DO: ADDRESS CHECKS'''

        message=b''
        while True:
            # print("Here2323")
            more,address = s.sock.recvfrom(1024*1024*1024)  
            if not more:  # socket has closed when recv() returns ''
                # print('Received zero bytes - end of file')
                break
            # print('Received {} bytes'.format(len(more)))
            message += more
            # print(message)
            # temp=message
            # temp.decode('utf-8')

            if(message.endswith(delim)):
                break

        if(retaddr):
            return message,address
        else:
    
            return message
    
    
    @staticmethod
    def checkIntegrity(pkt):
        # print()
        # return True
        if(pkt.data is None):
            # print("None ",pkt.checksum == hashlib.md5(b"").digest())
            # return True
            return pkt.checksum == hashlib.md5(b"").digest()
        else:
            # print(pkt.checksum == hashlib.md5(pkt.data).digest())
            # return True
            return pkt.checksum == hashlib.md5(pkt.data).digest()
    
    
    
    @staticmethod
    def sendUtil(s,data):
        pkt=Packet(data,seq=s.dataSeq)
        s.dataSeq+=1

        payload=pkt.pack()

        s.sock.sendto(payload,(s.peerHost,s.peerPort))
        sendTries=0
        # print("Needed Seq  ",pkt.seq)
        while True:
            readable,_,_=select.select([s.sock],[],[],ACK_TIMEOUT) #Wait for ACK
            if(readable):
                # print("Maybe")

                msg,addr=SendUtil.recvall(s)
                p=Packet()
                p.unpack(msg)
                # print(p.seq)
                if(SendUtil.checkIntegrity(p)):
                    if(p.pktType==p.CONTROL_PKT and p.seq== pkt.seq):
                        # print("----ACK Recieved at ",sendTries," for msg :",pkt.data)
                        break
            else:
                print("Packet Loss ...Retrying ==>",pkt.data)
                if(sendTries<=MAX_RESEND_TRY):
                    sendTries+=1 
                    # print("Retry   Sending seq",pkt.seq)
                    s.sock.sendto(payload,(s.peerHost,s.peerPort))
                else:
                    print("Retry Timeout , network Error")
                    break





class Sender():

    MAX_DATA_SIZE=20000
    MAX_SHUT_TRY=2000
    def __init__(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.databuf=bytes()
        self.dataSeq=0
        self.seqSet=set()



    def splitData(self,data):
        lst=[]
        dataCpy=data
        if(len(data)>self.MAX_DATA_SIZE):
            while(len(dataCpy)>0):
                ret=dataCpy[:self.MAX_DATA_SIZE]
                dataCpy=dataCpy[self.MAX_DATA_SIZE:]

                lst.append(ret)
        else:
            lst.append(data)
        return lst
    def send(self,data):


        lst=self.splitData(data)
        for i in lst:
            SendUtil.sendUtil(self,i)
        

    def setPeer(self,peer):
        self.peerHost,self.peerPort=peer


    def bind(self,own):
        self.selfHost,self.selfPort=own
        self.sock.bind(own)


    def close(self):
        p=Packet(datatype='control',con_pkt_code=9)
        p.data=p.delim
        payload=p.pack()
        for i in range(self.MAX_SHUT_TRY):
            self.sock.sendto(payload,(self.peerHost,self.peerPort))

        print("Shutting down")

import time

class RecieveUtil():

    @staticmethod
    def recvall(s,retaddr=True,delim=b"(:|BYE|:)"):

        '''TO DO: ADDRESS CHECKS'''

        message=b''
        while True:
            # print("Here2323")
            more,address = s.sock.recvfrom(1024*1024*1024)  
            if not more:  # socket has closed when recv() returns ''
                # print('Received zero bytes - end of file')
                break
            # print('Received {} bytes'.format(len(more)))
            message += more
            # temp=message
            # temp.decode('utf-8')

            if(message.endswith(delim)):
                break

        if(retaddr):
            return message,address
        else:
            return message

    @staticmethod
    def makeACK(pkt):
        p=Packet(datatype="control",con_pkt_code=3)
        p.seq=pkt.seq
        # p.data=b'(:||:)'
        return p

    @staticmethod
    def checkIntegrity(pkt):
        # return True
        if(pkt.data is None):
            # print("LOL ",pkt.checksum == hashlib.md5(b"").digest() )
            return pkt.checksum == hashlib.md5(b"").digest()
        else:
            # print("LOL   ",pkt.checksum == hashlib.md5(pkt.data).digest())
            return pkt.checksum == hashlib.md5(pkt.data).digest()


    @staticmethod
    def recvutil(s,last=False):

        readable,_,_=select.select([s.sock],[],[])

        msg,addr=RecieveUtil.recvall(s)
        p=Packet()
        p.unpack(msg)

        if(RecieveUtil.checkIntegrity(p) and p.pktType==p.DATA_PKT ):
            pkt=RecieveUtil.makeACK(p)
            payload=pkt.pack()

            
            s.sock.sendto(payload,(s.peerHost,s.peerPort))
            
            if(p.seq not in s.seqSet):
                s.seqSet.add(pkt.seq)
                s.recievedPackets.put(p)
                # print("BOI",p.data)

        



import queue

CLOSE_TIMEOUT=2
class Reciever():
    

    def __init__(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.databuf=bytes()
        self.recievedPackets=queue.Queue()
        self.seqSet=set()

    def setPeer(self,peer):
        self.peerHost,self.peerPort=peer


    def bind(self,own):
        self.selfHost,self.selfPort=own
        self.sock.bind(own)


    def recv(self,length):
        retdata=b''
        c=0
        while(len(retdata)!=length):
            RecieveUtil.recvutil(self)
            try:
                pp=self.recievedPackets.get(timeout=0.1)
                retdata+=pp.data
            except queue.Empty:
                pass
            # print(c)
            c+=1    
    
        return retdata

    def close(self):

        while True:
            readable,_,_=select.select([self.sock],[],[],CLOSE_TIMEOUT)
            if(readable):
                msg,addr=RecieveUtil.recvall(self)
                p=Packet()
                p.unpack(msg)
                # print("CLOSE PKT ",p.conPktCode)
                if(p.pktType==p.DATA_PKT and RecieveUtil.checkIntegrity(p)):
                    pkt=RecieveUtil.makeACK(p)
                    payload=pkt.pack()
                    # print("Recieved packet ",p.data)
                    # time.sleep(0.1)
                    # print("Sending ack for msg ",p.data," ",pkt.seq)
                    
                    self.sock.sendto(payload,(self.peerHost,self.peerPort))
                    
                    if(p.seq not in self.seqSet):
                        self.seqSet.add(pkt.seq)
                        self.recievedPackets.put(p)
                        # print("BOI",p.data)
                elif(p.pktType==p.CONTROL_PKT and p.conPktCode==p.SHUD):
                    print("SHUTDOWN")
                    break
