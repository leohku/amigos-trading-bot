import socket
import json
import sys
import time
from handler import Handler
from logger import Logger

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name = "AMIGOS"

# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port = 25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# port = 9997
# exchange_hostname = "localhost"

# ~~~~~============== NETWORKING  ==============~~~~~

def connect():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((exchange_hostname, port))
    except Exception as exp:
        print('Failed to connect to the socket.', exp)
        time.sleep(0.1)
    return s.makefile('rw', 1)


def write_to_exchange(exchange, obj):
    # print(f"RESPONSE: {obj}")
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())

# ~~~~~============== MAIN LOOP ==============~~~~~


def main():
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    
    logger = Logger(test_mode)
    handler = Handler(logger)
    
    # print("SERVER: ", hello_from_exchange, file=sys.stderr)
    while True:
        message = read_from_exchange(exchange)
        # return the strategy in JSON
        handler.handleBroadcast(message, exchange, write_to_exchange)
        if(message["type"] == "close"):
            print("SERVER: The round has ended")
            logger.send()
            break


if __name__ == "__main__":
    main()
