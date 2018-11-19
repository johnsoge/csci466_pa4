import queue
import threading
from ast import literal_eval #allows for a string to be converted to a dict


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)

    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)


## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths
    dst_S_length = 5
    prot_S_length = 1

    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]
        return self(dst, prot_S, data_S)




## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination

    ## called when printing the object
    def __str__(self):
        return self.addr

    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('\n%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('\n%s: received packet "%s"' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return



## Implements a multi-interface router
class Router:

    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        #TODO: set up the routing table for connected hosts
        self.rt_tbl_D = {}      # {destination: {router: cost}}
        print('\n%s: Initialized routing table' % self)
        #Copy cost_D into rt_tbl_D, initial routing table
        for key, val in self.cost_D.items():
            for key2, val2 in val.items():
                self.rt_tbl_D[key] = {self.name: val2}

        #Insert self into table
        self.rt_tbl_D[self.name] = {self.name: 0}

        self.print_routes()


    ## Print routing table
    def print_routes(self):
        keys = list(self.rt_tbl_D)
        #print top decoration of table
        print('|', end = '')
        for x in range(0, len(keys) + 1):
            print('====', end = '|')
        print('')

        #print who is printing table
        print('| ' + self.name + ' ', end = '')

        #print each destination in table
        print('|', end = '')
        for x in keys:
            print(' ' + x + ' ', end = '|')

        print('')
        #print decoration of table below header
        print('|', end = '')
        for x in range(0, len(keys) + 1):
            print('====', end = '|')
        print('')

        #get a list of all routers
        router_list = list(self.rt_tbl_D[keys[0]])
        #iterate through each router currently in the routing table and print entries for it
        for router in sorted(router_list):
            print('| ' + router + ' ', end = '|')


            for dest in self.rt_tbl_D:
                print('  ' + str(self.rt_tbl_D[dest][router]) + ' ', end = '|')
            print('\n', end = '|')

            for dest in range(len(keys)+1):
                print('----', end = '|')
            print('')



        #print('\nPrint routing table: ' + str(self.rt_tbl_D))


    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))


    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1
            ch = 1
            dest_found = False
            f = float("inf")
            for router, val in self.cost_D.items():
                for interface, cost in val.items():
                    if (router[0]=='H'):
                        if(router == p.dst):
                            ch = interface
                            dest_found = True
                    elif not dest_found and (cost + self.rt_tbl_D[p.dst][router])< f:
                        f = val[interface] + self.rt_tbl_D[p.dst][router]
                        ch = interface

            self.intf_L[ch].put(p.to_byte_S(), 'out', True)
            print('\n%s: forwarding packet "%s" from interface %d to %d' % \
                (self, p, i, ch))
        except queue.Full:
            print('\n%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        p = NetworkPacket(0, 'control', str(self.rt_tbl_D))
        try:
            print('\n%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('\n%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        print('\n%s: Received routing update %s from interface %d' % (self, p, i))

        new_table = literal_eval(p.data_S)

        update = False

        #iterate through the sent in table
        for dest in list(new_table):
            #iterate through the inner dictionary of the sent in table
            for rtr in list(new_table[dest]):
                #if the destination is already in the table, but the original router is not
                if (dest in self.rt_tbl_D) and (not rtr in self.rt_tbl_D[dest]):
                    update = True
                    self.rt_tbl_D[dest][rtr] = new_table[dest][rtr]
                #if the destination is not in the table
                elif not dest in self.rt_tbl_D:
                    update = True
                    self.rt_tbl_D[dest] = self.rt_tbl_D.get(dest, {})
                    #add path cost from current router to new destination
                    self.rt_tbl_D[dest][self.name] = new_table[dest][rtr] + self.rt_tbl_D[rtr][self.name]
                #possible DV algorithm
                elif (new_table[dest][rtr] < self.rt_tbl_D[dest][rtr]):
                    update = True
                    self.rt_tbl_D[dest][rtr] = new_table[dest][rtr]
                elif (new_table[dest][rtr] + self.rt_tbl_D[rtr][self.name]) < (self.rt_tbl_D[dest][self.name]):
                    update = True
                    self.rt_tbl_D[dest][self.name] = new_table[dest][rtr] + self.rt_tbl_D[rtr][self.name]

        #Sort the dict to allow a better printing
        temp = {}
        for x in sorted(self.rt_tbl_D):
            temp[x] = self.rt_tbl_D[x]

        # for x in sorted(self.rt_tbl_D):
        #     temp[x] = {}
        #     for y in sorted(self.rt_tbl_D[x]):
        #         temp[x][y] = self.rt_tbl_D[x][y]
        #
        self.rt_tbl_D = temp

        if update:
            for i in range(0, len(self.intf_L)):
                print('Sending routing update on intf: ' + str(i) + ' from Router: ' + self.name)
                self.send_routes(i)


    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
