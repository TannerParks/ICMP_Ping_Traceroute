from socket import *
import os
import sys
import struct
import time
import select
import binascii

from statistics import stdev

ICMP_ECHO_REQUEST = 8

timeList = []  # Keep all the round trip times here


def checksum(string):
    print(f"String: {string}")
    #print(f"String: {list(string)}")
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        print("\n", hex(string[count + 1]), hex(string[count]))
        thisVal = (string[count + 1]) * 256 + (string[count])
        print(f"ThisVal: {thisVal}")
        csum = csum + thisVal
        print(f"Checksum: {csum}")
        csum = csum & 0xffffffff
        print(f"Checksum 0xf: {csum}")
        count = count + 2
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)  # Add the extra 1 to the front for the binary number
    print(f"Checksum shift: {csum}")
    answer = ~csum
    answer = answer & 0xffff
    print(f"Answer before shift: {hex(answer)}")
    answer = answer >> 8 | (answer << 8 & 0xff00)
    print(f"Final answer: {hex(answer)}\t\t{answer}")
    #quit(0)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        # print(whatReady)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)  # Returns datagram in bytes
        print(f"Rec: {recPacket}")
        # TODO
        # Fill in start
        # Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]

        unpackedPacket = struct.unpack("bbHHh", icmpHeader)
        PID = unpackedPacket[3]
        if PID == ID:
            packetSize = struct.calcsize("d")
            time_sent = struct.unpack("d", recPacket[28:28 + packetSize])[0]
            roundtrip = timeReceived - time_sent

            print(f"IP: {addr[0]} total time = {roundtrip}ms")
            return roundtrip

        # Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)  # bbHHh
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    print(f"Header: {header}\tData: {data}\n")
    myChecksum = checksum(header + data)
    # Get the right checksum, and put in the header
    print(f"OG Checksum: {hex(myChecksum)}")
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    print(f"Corrected checksum: {hex(myChecksum)}")
    #exit(0)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details: http://sock-raw.org / papers / sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Send ping requests to a server separated by approximately one second
    # while 1:
    for i in range(5):
        delay = doOnePing(dest, timeout)
        # print(delay)   # print this later
        timeList.append(delay)
        time.sleep(1)  # one second
    printTimes()
    return delay


def printTimes():
    """Prints information about the RTT."""
    minimum = str(round(min(timeList), 5))
    maximum = str(round(max(timeList), 5))
    mean = str(round((sum(timeList) / len(timeList)), 5))
    std = str(round(stdev(timeList), 5))

    print(f"""
    \tMinimum:                 {minimum}
    \tMaximum:                 {maximum}
    \tMean:                    {mean}
    \tStandard Deviation:      {std}
    """)

    timeList.clear()    # Clears the list for the next ping
    return


if __name__ == "__main__":
    ping("google.com")  # United States
    ping("103.4.99.131")  # Mexico
    ping("1.208.104.173")  # South Korea
    ping("102.67.96.46")  # United Kingdom
    ping("102.128.175.255")  # South Africa
    # ping("localhost")
