from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2


# The packet that we shall send to each router along the path is the ICMP echo
# request packet, which is exactly what we had used in the ICMP ping exercise.
# We shall use the same packet that we built in the Ping exercise
def checksum(string):
    # print(f"String: {string}")
    # print(f"String: {list(string)}")
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def build_packet():  # TODO
    myChecksum = 0
    myID = os.getpid() & 0xFFFF
    # In the sendOnePing() method of the ICMP Ping exercise ,firstly the header of our
    # packet to be sent was made, secondly the checksum was appended to the header and
    # then finally the complete packet was sent to the destination.
    header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)
    data = struct.pack("d", time.time())

    myChecksum = checksum(header + data)

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    # Make the header in a similar way to the ping exercise.
    # Append checksum to the header.
    # Don’t send the packet yet , just return the final packet in this function.
    # So the function ending should look like this
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)
    packet = header + data
    #print(packet)
    return packet


def get_name(addr):
    """Gets the name of the host if it can find one."""
    try:
        host = gethostbyaddr(addr[0])
        #print(f"Host {host}")
        return host
    except IOError:
        #print(addr)
        #print(f"Address {addr}")
        return addr


def get_route(hostname):
    timeLeft = TIMEOUT
    print(f"\t\tTracing route to {hostname}")
    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            destAddr = gethostbyname(hostname)
            #print(destAddr)

            # Fill in start
            # Make a raw socket named mySocket TODO
            icmp = getprotobyname("icmp")
            mySocket = socket(AF_INET, SOCK_RAW, icmp)
            # mySocket.bind(("", 0))
            # Fill in end

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)

            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)
                #print(whatReady)
                if whatReady[0] == []:  # Timeout
                    #print("WhatReady")
                    print(" * * * Request timed out.")
                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect
                if timeLeft <= 0:
                    #print("TimeLeft")
                    print(" * * * Request timed out.")
            except timeout:
                continue

            else:
                # Fill in start TODO
                # Fetch the icmp type from the IP packet
                types, code = recvPacket[20:22]
                addr = get_name(addr)   # Outputs the name instead of the address (if it can find one)
                #print(f"Types: {types}\t\tCode: {code}")
                # Fill in end

                if types == 11:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" % (ttl, (timeReceived - t) * 1000, addr[0]))

                elif types == 3:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" % (ttl, (timeReceived - t) * 1000, addr[0]))

                elif types == 0:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" % (ttl, (timeReceived - timeSent) * 1000, addr[0]))
                    return

                else:
                    print("error")
                break
            finally:
                #print("\n")
                mySocket.close()


if __name__ == '__main__':
    get_route("google.com")
    #get_route("oregonstate.edu")
    get_route("amazon.com")
    get_route("twitter.com")
    get_route("reddit.com")
