import sys
import socket, socketserver
import json
import random


# You to exchange:
# Hello: the first message you must send, identifying yourself to the exchange
# Add: a request to buy or sell a security; 'add order'
# Cancel: a request to remove from the book some previously-placed order that hasn't traded yet
# Convert: a request to convert an ETF or ADR (from or to its underlying basket)
#
# Exchange to you (private):
#
# Hello: the first message the exchange will send you when you connect, containing your positions
# Ack: 'your order was successfully placed on the book' (this does not mean it traded!)
# Reject: 'your order wasn't valid for this reason: '' (e.g. negative price, malformed syntax etc.)
# Error: an error related to your bot that's not associated with a specific order
# Out: following a cancel or once your order is completely filled, 'your order is no longer on the book'
# Fill: 'your order traded'
#
# Exchange to you (public):
#
# Book: 'the current state of the book is''
# Trade: 'two (anonymous) people traded at price X'
# Open: 'the market for a specific security has opened'
# Close: 'the market for a specific security has closed'



class MyTCPHandler(socketserver.StreamRequestHandler):

    def read_from_client(self):
        data = self.rfile.readline()
        return json.loads(data)

    def write_to_client(self, msg):
        json_msg = json.dumps(msg).encode("utf-8") # <- TypeError: a bytes-like object is required, not 'str'
        self.wfile.write(json_msg)
        self.wfile.write(b"\n")

    # types = ["hello", "open", "close", "error", "book", "trade", "ack", "reject", "fill", "out"]

    def server_feed_gen(self):
        # types = ["close", "open", "book", "trade"]
        input_cmd = ""
        while input_cmd == "":
            input_cmd = input("Input server feed:").split()

        type = input_cmd[0].lower()
        # print(input_cmd)

        if type == "hello":
            # HELLO SYM:POSN SYM:POSN ...
            return {"type":"hello","symbols":[{"symbol":"BOND","position":2}, {"symbol":"GS","position":1}]}

        elif type == "open" or type == "close":
            # OPEN|CLOSE SYM SYM SYM ...
            # {"type":"open|close","symbols":["SYM1", "SYM2", ...]}
            # Example
            # CLOSE BOND GS MS
            return {"type":type,"symbols":input_cmd[1:]}

        elif type == "book":
            symbol = input_cmd[1]
            buy_index = input_cmd.index("BUY")
            sell_index = input_cmd.index("SELL")
            buys = input_cmd[buy_index + 1: sell_index]
            sells = input_cmd[sell_index + 1:]
            for i, pair in enumerate(buys):
                buys[i] = [int(x) for x in pair.split(":")]
            for i, pair in enumerate(sells):
                sells[i] = [int(x) for x in pair.split(":")]
            # BOOK SYMBOL BUY PRICE:SIZE PRICE:SIZE ... SELL PRICE:SIZE PRICE:SIZE ...
            # {"type":"book","symbol":"SYM","buy":[[PRICE,SIZE], ...],"sell":[...]}
            # Example
            # BOOK SYMBOL BUY 10:1 20:2 SELL 30:1 40:2
            return {"type":type,"symbol":symbol,"buy":buys,"sell":sells}
            
        elif type == "trade":
            # TRADE SYMBOL PRICE SIZE
            # {"type":"trade","symbol":"SYM","price":N,"size":N}
            # Example:
            # TRADE BOND 1000 50

            symbol, price, size = input_cmd[1:]
            return {"type":type,"symbol":symbol,"price":int(price),"size":int(size)}

        elif type == "ack":
            # ACK ID
            # {"type":"ack","order_id":N}
            return {"type":type,"order_id":int(input_cmd[1])}
        
        elif type == "reject":
            # REJECT ID MSG
            # {"type":"reject","order_id":N,"error":"MSG"}
            return {"type":type,"order_id":int(input_cmd[1]),"error":input_cmd[2]}

        elif type == "fill":
            # FILL ID SYMBOL DIR PRICE SIZE
            # {"type":"fill","order_id":N,"symbol":"SYM","dir":"BUY","price":N,"size":N}
            return {"type":type,"order_id":int(input_cmd[1]),"symbol":input_cmd[2],
                    "dir":input_cmd[3],"price":int(input_cmd[4]),"size":int(input_cmd[5])}

        elif type == "out":
            # OUT ID
            return {"type":type,"order_id":int(input_cmd[1])}
        
        elif type == "error":
            # 'Error' and 'reject' messages are the server complaining about your bot. 
            # If the server is able to associate the error with an 'add' message, 
            # then it will send a 'reject' with the order id that failed and the error message. 
            # Otherwise, you will simply receive an 'error'.
            # If the server detects that you have disconnected then all of your open orders will be canceled.

            return {"type":type,"error":input_cmd[1]}

        else:
            print("invalid cmd")

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.read_from_client()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        # self.write_to_client({"type": "close", "symbols":["SYM1", "SYM2"]})
        for i in range(1000):
            msg = self.server_feed_gen()
            print(msg)
            self.write_to_client(msg)
            # print(self.read_from_client())



    def close(self):
        print("closed")
        server.shutdown()
        server.close()
        

if __name__ == "__main__":
    HOST, PORT = "localhost", 9997

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        print('The text exchange server is running...')
        server.serve_forever()
