#!/usr/bin/env python3
# python3 version of server
import sys
import subprocess
# ECC - now installed in official area
# sys.path.append('/home/root/.local/lib/python3.5/site-packages')
#
from ironman.constructs.ipbus import PacketHeaderStruct, ControlHeaderStruct, IPBusConstruct, IPBusWords, IPBusWord
from ironman.hardware import HardwareManager, HardwareMap
from ironman.communicator import Jarvis
import random
from mmap import mmap
import struct
from construct import Bytes, ByteSwapped

# packet history
history_fifo = [0] * 8

# traffic history
traffic_history = [0] * 4
traffic_fifo = [0] * 16

# Jarvis stuff
j = Jarvis()
manager = HardwareManager()

# read in hardware maep
with open('hardware_map.yml') as f:
  read_data = f.read()
manager.add(HardwareMap(read_data, 'main'))

# Jason stuff
j.set_hardware_manager(manager)
@j.register('main')

# Class to respond to upd packet
class DataInteraction:

  # read request - reads from /dev/mem
  def read(self, addr, size):
    baseaddr = int(addr/4096)
    baseaddr *= 4096
    f = open('/dev/mem','r+b')
    reg = mmap(f.fileno(), 4096, offset=baseaddr)
    print("ipbus_srtm: reading offset: ", hex(addr))
    print("baseaddr: ", hex(baseaddr))

    # return value in memory
    number = struct.unpack('I',reg[addr%4096:addr%4096+4])[0]
    print("number: ", hex(number))

    return IPBusWord.build(number)

  # write request - writes into /dev/mem
  def write(self, addr, data):
    baseaddr = int(addr/4096)
    baseaddr *= 4096
    print("ipbus_srtm: writing offset: ", hex(addr))
    num0 = int(data[0])
    num1 = int(data[1])
    num2 = int(data[2])
    num3 = int(data[3])

    # piece number together from the four data words
    number = num0 + (num1 << 8) + (num2 << 16) + (num3 << 24)
    print("Writing value: ", hex(number))

    # replace with call to subprocess
    subprocess.run(["/home/root/ipbus/write_reg.exe",hex(addr), hex(number)])

    # open /dev/mem
    ###f = open('/dev/mem','r+b')
    # write word to memory
    ###reg1 = mmap(f.fileno(), 4096, offset=baseaddr)
    ###reg1[addr%4096:addr%4096+4]=struct.pack('I',number)

    return

  # RMWBITS request - reads register and writes over selected bits
  def rmwbits(self, addr, data):

    baseaddr = int(addr/4096)
    baseaddr *= 4096

    # open /dev/mem and read register value
    f = open('/dev/mem','r+b')
    reg = mmap(f.fileno(), 4096, offset=baseaddr)

    # return value in memory
    reg_val = struct.unpack('I',reg[addr%4096:addr%4096+4])[0]

    num0 = int(data[0])
    num1 = int(data[1])
    num2 = int(data[2])
    num3 = int(data[3])
    num4 = int(data[4])
    num5 = int(data[5])
    num6 = int(data[6])
    num7 = int(data[7])

    # The first four words are the aMask and the second four words are the words to overwrite
    # a) read register
    # b) output = original&mask + new
    mask = num0 + (num1 << 8) + (num2 << 16) + (num3 << 24)
    numb = num4 + (num5 << 8) + (num6 << 16) + (num7 << 24)
    final_word = (mask & reg_val) + numb

    print("Writing value: ", hex(final_word))
    subprocess.run(["/home/root/ipbus/write_reg.exe",hex(addr), hex(final_word)])

    ###reg[addr%4096:addr%4096+4]=struct.pack('I',final_word)

    # ipbus expects to get the original register value returned to it
    return IPBusWord.build(reg_val)

# keeps track of the request and response packets. This data is sent out with the status packet
# stores the request and response packets in a global fifo and returns an array of Bytes 
def build_history(packet) :
  global history_fifo

  # Shift values first three elements
  for i in range(0,3) : 
    history_fifo[i] = history_fifo[i+1]

  # Shift values for elements 4-6
  for i in range(4,7) :
    history_fifo[i]= history_fifo[i+1]

  # build packet request word
  request_value = 0
  if (packet.request.header.type_id == 'STATUS') :
    request_value += 1
  elif (packet.request.header.type_id == 'RESEND') :
    request_value += 2

  # build packet response word
  response_value = 0
  if (packet.request.header.type_id == 'STATUS') :
    response_value += 1
  elif (packet.request.header.type_id == 'RESEND') :
    response_value += 2

  # build packet from request and response packet - This is big endian
  request_word = (packet.request.header.protocol_version << 4) + (packet.request.header.id << 8) + (packet.request.header.byteorder << 28) + (request_value << 24)  
  response_word = (packet.response.header.protocol_version << 4) + (packet.response.header.id << 8) + (packet.response.header.byteorder << 28) + (request_value << 24)

  # store newest request/response value in the fifo
  history_fifo[3] = request_word
  history_fifo[7] = response_word


  #print("request_word: ", hex(request_word))
  #print("request packet: ", packet_history[hist_pointer])
  #print("response_word: ", hex(response_word))
  #print("response packet: ", packet_history[hist_pointer+4])

  return


# keeps track of the traffic that is added to the status packet
def build_traffic(packet) :
  global traffic_history
  global traffic_fifo
  lookup1 = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
  lookup2 = [24, 16, 8, 0, 24, 16, 8, 0, 24, 16, 8, 0, 24, 16, 8, 0]

  #print("building traffic...")

  # shift traffic fifo
  for i in range(0,15) :
    traffic_fifo[i] = traffic_fifo[i+1]

  # Ignoring the top four bits for now. Lower four bits are the event type
  if (packet.request.header.type_id == 'CONTROL') :
    traffic_word = 2
  elif (packet.request.header.type_id == 'STATUS') :
    traffic_word = 3
  elif (packet.request.header.type_id == 'RESEND') :
    traffic_word = 4

  traffic_fifo[15] = traffic_word

  # clear the traffic history
  for iword in range(0,4) :
    traffic_history[iword] = 0

  # each traffic history words contains four traffic entries that are bit shifted by lookup2
  for iword in range(0,16) :
    traffic_history[lookup1[iword]] += (traffic_fifo[iword] << lookup2[iword])

  return

# This function fills the response packet to be sent out.
def buildResponsePacket(packet):
  global packet_history, traffic_history
  #print("buildResponsePacket")
  #print("packet request: ", packet.request)

  # build status history words
  build_history(packet)
  
  # history of traffic
  build_traffic(packet)

  if (packet.response.header.type_id == "STATUS" ) :

    # fill data words for the status packet
    #print("packet response status data: ", packet.response.status.data[0])
      
    packet.response.status.data[0]   = Bytes(4).build(1472)                # MTU
    packet.response.status.data[1]   = Bytes(4).build(int("0x00000004",0)) # nResponseBuffers
    next_packet = int("0x200000f0",0) + ((packet.request.header.id+1) << 8)
    #print("next packet: ", hex(next_packet))
    packet.response.status.data[2]   = Bytes(4).build(next_packet)         # Next expected packet header
    packet.response.status.data[3]   = Bytes(4).build(traffic_history[0])  # Incoming traffic
    packet.response.status.data[4]   = Bytes(4).build(traffic_history[1])
    packet.response.status.data[5]   = Bytes(4).build(traffic_history[2])
    packet.response.status.data[6]   = Bytes(4).build(traffic_history[3])
    packet.response.status.data[7]   = Bytes(4).build(history_fifo[0])     # Control packet history
    packet.response.status.data[8]   = Bytes(4).build(history_fifo[1])
    packet.response.status.data[9]   = Bytes(4).build(history_fifo[2])
    packet.response.status.data[10]  = Bytes(4).build(history_fifo[3])
    packet.response.status.data[11]  = Bytes(4).build(history_fifo[4])
    packet.response.status.data[12]  = Bytes(4).build(history_fifo[5])
    packet.response.status.data[13]  = Bytes(4).build(history_fifo[6])
    packet.response.status.data[14]  = Bytes(4).build(history_fifo[7])

    # Handle byte swapping - don't do this for the last 8 words since they should be big endian
    for i in range(7):
      if (packet.request.endian == 'LITTLE') :
        ByteSwapped(packet.response.status.data[i])

  else :  # non-status packet
    # print("packet response", packet.response)
    # ECC - need to handle the case of RMWBITS
    #     - for now it appears to be sufficient that we just store something in the data word
    if (packet.response.transactions[0].header.type_id == "RMWBITS") :
      print("packet type RMWBITS")
      # store some data
      #packet.response.transactions[0].data = 0x0
   
    # set info code
    packet.response.transactions[0].header.info_code = 'SUCCESS'

  #print("Sending response: ", packet.response)
  return  IPBusConstruct.build(packet.response)


# if you want to add history and log anything, use this
# currently commented out of callback list
#from ironman.history import History
#h = History()

from ironman.server import ServerFactory
from ironman.packet import IPBusPacket
from twisted.internet import reactor
from twisted.internet.defer import Deferred

# Connect the response class to the deffered callback
def deferredGenerator():
    #print("In deferredGenerator")
    return Deferred().addCallback(IPBusPacket).addCallback(j).addCallback(buildResponsePacket)#.addCallback(h)

# Set up IPBus UDP @ Port 50001'''
reactor.listenUDP(50001, ServerFactory('udp', deferredGenerator))

print ("Running the ironman reactor...")
reactor.run()
