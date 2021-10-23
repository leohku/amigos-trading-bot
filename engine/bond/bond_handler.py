from bond.bond_strategy import BondStrategy


class BondHandler():
    def __init__(self):
        # --- Bond ---
        self.BOND_FAIR_VALUE = 1000
        self.BOND_RISK_LIMIT = 100
        self.bond_market_open = False
        self.bond_bids = []
        self.bond_asks = []
        self.bond_active_orders = [] # array indexes of trade_pipelines
        self.bond_total_position = 0
        self.bond_pnl = 0

        self.bondStrategy = BondStrategy()

    def handleBook(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        self.bond_bids = message['buy']  # high-to-low
        self.bond_asks = message['sell']  # low-to-high

        # Deduping the strategy is not required, since if people
        # are selling for <1000 (LOW) then I buy, if people are buying for
        # >1000 (HIGH) then I sell. i.e.,
        # others LOW ASK -> me LOW BID
        # others HIGH BID -> me HIGH ASK
        # so LOW BIDS and HIGH ASKS do not trigger anything in the algorithm

        strategies = self.bondStrategy.getStrategies(self.BOND_FAIR_VALUE, self.BOND_RISK_LIMIT, self.bond_asks, self.bond_bids, self.bond_total_position, self.bond_pnl, self.bond_active_orders, trade_pipelines)
        for strategy in strategies:
            # possible action - BUY | SELL | NOOP
            action = strategy['action'].upper()
            if action == 'BUY' or action == 'SELL':
                execution_msg = {
                    "type": "add",
                    "order_id": len(message_history),
                    "symbol": "GS",
                    "dir": action,
                    "price": strategy['price'],
                    "size": strategy['size']
                }
                write_to_exchange(exchange, execution_msg)  # send to exchange
                pipeline = {
                    'type': 'BOND',
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
                self.bond_active_orders.append(len(trade_pipelines))
                trade_pipelines.append(pipeline)
            elif action == 'NOOP':
                pass

    def handleTrade(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # Check if it is our order
        # NOTE from Tony: only ETF will use TRADE signal
        pass

    def handleOpen(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        self.bond_market_open = True

    def handleClose(self, message, exchange, write_to_exchange, message_history, trade_pipelines, logger):
        self.bond_market_open = False
        logger.logBond(self.bond_pnl)

    def handleAck(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # Resolve Ack order_id to relevant pipeline
        pipeline_id = message_history[message['order_id']]['pipeline']
        pipeline = trade_pipelines[pipeline_id]
        if pipeline['status'] != 'CANCELLED_BY_EXCHANGE':
            # There's only one ACK in the BOND pipeline,
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
                self.bond_active_orders.remove(pipeline_id)
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
        fill_pnl = abs(self.BOND_FAIR_VALUE - message['price']) * message['size']
        pipeline['pnl'] += fill_pnl
        self.bond_pnl += fill_pnl
        # Update the position
        if pipeline['dir'] == 'BUY':
            self.bond_total_position += message['size']
        elif pipeline['dir'] == 'SELL':
            self.bond_total_position -= message['size']

        if pipeline['status'] != 'CANCELLED_BY_EXCHANGE':
            # Should always be ==, but just to play safe
            if pipeline['confirmed_and_filling_total_fill'] >= pipeline['size']:
                pipeline['status'] = 'COMPLETED'
                try:
                    self.bond_active_orders.remove(pipeline_id)
                except ValueError:
                    pass
        else:
            # A FILL is received after an OUT is received
            # I think this will not happen, but just in case:
            print("WARN: FILL received after OUT")
            # There isn't anything to handle though, just a fyi message.
