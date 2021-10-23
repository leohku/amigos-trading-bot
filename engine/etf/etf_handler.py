from etf.etf_strategy import ETFStrategy


class ETFHandler():
    def __init__(self):
        # --- ETF ---
        self.ETF_RISK_LIMIT = 100
        self.CONSTITUENT_RISK_LIMIT = 100
        self.CONVERSION_FEE = 100
        self.MULTIPLES_PER_CONVERSION = 10
        self.RATIO_ETF = 10
        self.RATIO_BOND = 3
        self.RATIO_GS = 2
        self.RATIO_MS = 3
        self.RATIO_WFC = 2

        self.etf_open = False
        self.etf_bids = []
        self.etf_asks = []
        self.etf_total_position = 0

        self.bond_open = False
        self.bond_bids = []
        self.bond_asks = []

        self.gs_open = False
        self.gs_bids = []
        self.gs_asks = []

        self.ms_open = False
        self.ms_bids = []
        self.ms_asks = []

        self.wfc_open = False
        self.wfc_bids = []
        self.wfc_asks = []

        self.etf_active_orders = []
        self.etf_pnl = 0

        self.etfStrategy = ETFStrategy()

    def handleBook(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        if message['symbol'] == 'XLF':
            self.etf_bids = message['buy']  # high-to-low
            self.etf_asks = message['sell']  # low-to-high
        if message['symbol'] == 'BOND':
            self.bond_bids = message['buy']  # high-to-low
            self.bond_asks = message['sell']  # low-to-high
        if message['symbol'] == 'GS':
            self.gs_bids = message['buy']
            self.gs_asks = message['sell']
        if message['symbol'] == 'MS':
            self.ms_bids = message['buy']
            self.ms_asks = message['sell']
        if message['symbol'] == 'WFC':
            self.wfc_bids = message['buy']
            self.wfc_asks = message['sell']

        if (
            self.etf_open and
            self.bond_open and
            self.gs_open and
            self.ms_open and
            self.wfc_open and
            (len(self.etf_bids) != 0) and
            (len(self.etf_asks) != 0) and
            (len(self.bond_bids) != 0) and
            (len(self.bond_asks) != 0) and
            (len(self.gs_bids) != 0) and
            (len(self.gs_asks) != 0) and
            (len(self.ms_bids) != 0) and
            (len(self.ms_asks) != 0) and
            (len(self.wfc_bids) != 0) and
            (len(self.wfc_asks) != 0)
        ):
            strategies = self.etfStrategy.getStrategies(self.etf_asks, self.etf_bids, self.bond_asks, self.bond_bids, self.gs_asks, self.gs_bids, self.ms_asks, self.ms_bids, self.wfc_asks, self.wfc_bids)
            for strategy in strategies:
                # possible action - BUY | SELL
                action = strategy['action'].upper()
                if action == 'BUY' or action == 'SELL':
                    execution_msg = {
                        "type": "add",
                        "order_id": len(message_history),
                        "symbol": "XLF",
                        "dir": action,
                        "price": strategy['price'],
                        "size": strategy['size']
                    }
                    write_to_exchange(exchange, execution_msg)  # send to exchange
                    pipeline = {
                        'type': 'ETF',
                        'dir': action,
                        'price': strategy['price'],
                        'size': strategy['size'],
                        'message_hist': [len(message_history)],
                        'status': 'EXECUTED',
                        'pnl': 0,
                        'confirmed_and_filling_total_fill': 0
                    }
                    execution_msg['pipeline'] = len(trade_pipelines)
                    message_history.append(execution_msg)
                    self.etf_active_orders.append(len(trade_pipelines))
                    trade_pipelines.append(pipeline)
    
    def handleTrade(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # Check if it is our order
        # NOTE from Tony: only ETF will use TRADE signal
        pass

    def handleOpen(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        if 'XLF' in message['symbols']:
            self.etf_open = True
        if 'BOND' in message['symbols']:
            self.bond_open = True
        if 'GS' in message['symbols']:
            self.gs_open = True
        if 'MS' in message['symbols']:
            self.ms_open = True
        if 'WFC' in message['symbols']:
            self.wfc_open = True

    def handleClose(self, message, exchange, write_to_exchange, message_history, trade_pipelines, logger):
        if 'XLF' in message['symbols']:
            self.etf_open = False
        if 'BOND' in message['symbols']:
            self.bond_open = False
        if 'GS' in message['symbols']:
            self.gs_open = False
        if 'MS' in message['symbols']:
            self.ms_open = False
        if 'WFC' in message['symbols']:
            self.wfc_open = False
        # TODO: Logger after calc PnL

    def handleAck(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # Resolve Ack order_id to relevant pipeline
        pipeline_id = message_history[message['order_id']]['pipeline']
        pipeline = trade_pipelines[pipeline_id]
        if pipeline['status'] != 'CANCELLED_BY_EXCHANGE':
            # There's only one ACK in the ETF pipeline,
            # so what to update is clear
            pipeline['status'] = 'CONFIRMED_AND_FILLING'
    
    def handleOut(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # Resolve Out order_id to relevant pipeline
        pipeline_id = message_history[message['order_id']]['pipeline']
        pipeline = trade_pipelines[pipeline_id]

        # Solicited OUT implies a completely normal out caused by filled orders
        # and intentional cancellations (which will not happen in BOND)
        if (
            pipeline['status'] == 'COMPLETED' or
            pipeline['status'] == 'CANCELLED_BY_EXCHANGE'  # double OUT case, from race condition between cancel and fill
        ):
            pass

        # Unsolicited OUT implies the server ACKs your order, and cancels it
        # And future ACKs & FILLs received will not affect status
        # i.e. CANCELLED_BY_EXCHANGE is the final status
        else:
            pipeline['status'] = 'CANCELLED_BY_EXCHANGE'
            try:
                self.etf_active_orders.remove(pipeline_id)
            except ValueError:
                pass
    
    def handleFill(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # calculate the PnL
        # Resolve Fill order_id to relevant pipeline
        pipeline_id = message_history[message['order_id']]['pipeline']
        pipeline = trade_pipelines[pipeline_id]

        # Update the fill
        pipeline['confirmed_and_filling_total_fill'] += message['size']
        # Update the PnL
        # TODO
        # fill_pnl = abs(self.BOND_FAIR_VALUE - message['price']) * message['size']
        # pipeline['pnl'] += fill_pnl
        # self.etf_pnl += fill_pnl
        # Update the position
        if pipeline['dir'] == 'BUY':
            self.etf_total_position += message['size']
        elif pipeline['dir'] == 'SELL':
            self.etf_total_position -= message['size']

        if pipeline['status'] != 'CANCELLED_BY_EXCHANGE':
            # Should always be ==, but just to play safe
            if pipeline['confirmed_and_filling_total_fill'] >= pipeline['size']:
                pipeline['status'] = 'COMPLETED'
                try:
                    self.etf_active_orders.remove(pipeline_id)
                except ValueError:
                    pass
        else:
            # A FILL is received after an OUT is received
            # I think this will not happen, but just in case:
            print("WARN: FILL received after OUT")
            # There isn't anything to handle though, just a fyi message.