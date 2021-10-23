from bond.bond_handler import BondHandler
from adr.adr_handler import ADRHandler
from etf.etf_handler import ETFHandler


class Handler():
    def __init__(self, logger):
        # message_history: Global array of ASK and CONVERT messages sent to
        # exchange
        # [{dir: price: size: idea}]

        # trade_pipelines: Global array of trade pipeline dictionaries
        # [{type: pipeline_type, details: exec_details, status: []}]

        self.message_history = []
        self.trade_pipelines = []

        # Create message handlers for different assets
        self.bondHandler = BondHandler()
        self.adrHandler = ADRHandler()
        self.etfHandler = ETFHandler()

        self.logger = logger

    def resolvedPipeline(self, order_id):
        pipeline_id = self.message_history[order_id]['pipeline']
        pipeline = self.trade_pipelines[pipeline_id]
        return pipeline

    def handleBroadcast(self, message, exchange, write_to_exchange):
        # print(f"SERVER: {message}")

        # Execute a strategy and send to the server
        msg_type = message["type"]

        # Public Feeds
        if msg_type == "book":
            if message["symbol"] == 'BOND':
                self.bondHandler.handleBook(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                self.etfHandler.handleBook(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif message["symbol"] == 'VALBZ' or message["symbol"] == 'VALE':
                self.adrHandler.handleBook(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif message["symbol"] == 'GS' or message["symbol"] == 'MS' or message["symbol"] == 'WFC' or message["symbol"] == 'XLF':
                self.etfHandler.handleBook(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            return
        if msg_type == "trade":
            return
        if msg_type == "open":
            if 'BOND' in message['symbols']:
                self.bondHandler.handleOpen(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
            if 'VALBZ' in message['symbols'] or 'VALE' in message['symbols']:
                self.adrHandler.handleOpen(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
            if 'GS' in message['symbols'] or 'MS' in message['symbols'] or 'WFC' in message['symbols'] or 'XLF' in message['symbols']:
                self.etfHandler.handleOpen(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
            return
        if msg_type == "close":
            if 'BOND' in message['symbols']:
                self.bondHandler.handleClose(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines, self.logger)
            if 'VALBZ' in message['symbols'] or 'VALE' in message['symbols']:
                self.adrHandler.handleClose(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines, self.logger)
            if 'GS' in message['symbols'] or 'MS' in message['symbols'] or 'WFC' in message['symbols'] or 'XLF' in message['symbols']:
                self.etfHandler.handleClose(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines, self.logger)
            return
        
        # Private Feeds
        # Messages without order_id
        if msg_type == "error":
            print(f"WARN: Error received {message}")
            return

        # Messages with order_id
        msg_pipeline_type = self.resolvedPipeline(message['order_id'])['type']
        if msg_type == "ack":
            if msg_pipeline_type == 'BOND':
                self.bondHandler.handleAck(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif msg_pipeline_type == 'ADR':
                self.adrHandler.handleAck(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif msg_pipeline_type == 'ETF':
                self.etfHandler.handleAck(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            return
        if msg_type == "out":
            if msg_pipeline_type == 'BOND':
                self.bondHandler.handleOut(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif msg_pipeline_type == 'ADR':
                self.adrHandler.handleOut(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif msg_pipeline_type == 'ETF':
                self.etfHandler.handleOut(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            return
        if msg_type == "fill":
            if msg_pipeline_type == 'BOND':
                self.bondHandler.handleFill(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif msg_pipeline_type == 'ADR':
                self.adrHandler.handleFill(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            elif msg_pipeline_type == 'ETF':
                self.etfHandler.handleFill(message, exchange, write_to_exchange, self.message_history, self.trade_pipelines)
                return
            return
        # NOTE: type == "reject" is not handled
