from adr.adr_strategy import ADRStrategy


class ADRHandler():
    def __init__(self):
        # --- ADR ---
        self.ADR_RISK_LIMIT = 10
        self.ADR_STOCK_RISK_LIMIT = 10
        self.CONVERSION_FEE = 10

        self.adr_market_open = False
        self.adr_bids = []
        self.adr_asks = []
        self.adr_total_position = 0

        self.adr_stock_market_open = False
        self.adr_stock_bids = []
        self.adr_stock_asks = []
        self.adr_stock_total_position = 0

        self.adr_active_orders = []
        self.adr_pnl = 0

        self.adrStrategy = ADRStrategy()

    def handleBook(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        if message['symbol'] == 'VALBZ':
            self.adr_stock_bids = message['buy']  # high-to-low
            self.adr_stock_asks = message['sell']  # low-to-high
        if message['symbol'] == 'VALE':
            self.adr_bids = message['buy']  # high-to-low
            self.adr_asks = message['sell']  # low-to-high
        
        # Only execute strategies if both markets are open and 4 arrays above are populated
        if self.adr_market_open and self.adr_stock_market_open and (len(self.adr_bids) != 0) and (len(self.adr_asks) != 0) and (len(self.adr_stock_bids) != 0) and (len(self.adr_stock_asks) != 0):
            strategies = self.adrStrategy.getStrategies(self.ADR_RISK_LIMIT, self.ADR_STOCK_RISK_LIMIT, self.CONVERSION_FEE, self.adr_asks, self.adr_bids, self.adr_stock_asks, self.adr_stock_bids, self.adr_total_position, self.adr_stock_total_position, self.adr_pnl, self.adr_active_orders, trade_pipelines)
            for strategy in strategies:
                if strategy['type'] == 'ARB':
                    execution_msg_adr = {
                        "type": "add",
                        "order_id": len(message_history),
                        "symbol": "VALE",
                        "dir": strategy['actionADR'].upper(),
                        "price": strategy['priceADR'],
                        "size": strategy['sizeADR']
                    }
                    execution_msg_adr_stock = {
                        "type": "add",
                        "order_id": len(message_history) + 1,
                        "symbol": "VALBZ",
                        "dir": strategy['actionStock'].upper(),
                        "price": strategy['priceStock'],
                        "size": strategy['sizeStock']
                    }
                    write_to_exchange(exchange, execution_msg_adr)
                    write_to_exchange(exchange, execution_msg_adr_stock)
                    pipeline = {
                        'type': 'ADR',
                        'subtype': 'ARB',
                        'dirADR': strategy['actionADR'].upper(),
                        'priceADR': strategy['priceADR'],
                        'sizeADR': strategy['sizeADR'],
                        'dirStock': strategy['actionStock'].upper(),
                        'priceStock': strategy['priceStock'],
                        'sizeStock': strategy['sizeStock'],
                        'message_hist': [len(message_history), len(message_history) + 1],
                        'status': 'EXECUTED',
                        'pnl': 0,
                        'total_fill_adr': 0,
                        'total_fill_adr_stock': 0
                    }
                    execution_msg_adr['pipeline'] = len(trade_pipelines)
                    execution_msg_adr_stock['pipeline'] = len(trade_pipelines)
                    message_history.append(execution_msg_adr)
                    message_history.append(execution_msg_adr_stock)
                    self.adr_active_orders.append(len(trade_pipelines))
                    trade_pipelines.append(pipeline)

    def handleTrade(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # Check if it is our order
        # NOTE from Tony: only ETF will use TRADE signal
        pass

    def handleOpen(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        if 'VALBZ' in message['symbols']:
            self.adr_stock_market_open = True
        if 'VALE' in message['symbols']:
            self.adr_market_open = True

    def handleClose(self, message, exchange, write_to_exchange, message_history, trade_pipelines, logger):
        if 'VALBZ' in message['symbols']:
            self.adr_stock_market_open = False
        if 'VALE' in message['symbols']:
            self.adr_market_open = False
        if self.adr_stock_market_open == False and self.adr_market_open == False:
            logger.logADR(self.adr_pnl)

    def handleAck(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # No-op if message ACKs a convert
        if message_history[message['order_id']]['type'] == 'convert':
            return

        # Resolve Ack order_id to relevant pipeline
        pipeline_id = message_history[message['order_id']]['pipeline']
        pipeline = trade_pipelines[pipeline_id]
        if pipeline['status'] != 'CANCELLED_BY_EXCHANGE':
            # There's only one ACK in the BOND pipeline,
            # so what to update is clear
            pipeline['status'] = 'CONFIRMED_AND_FILLING'

    def handleOut(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # NOTE: It would be better to have an OUT message auto trigger a trade restart instead of
        # completely cancelling the pipeline altogether if some parts of it have been filled.
        # Maybe next version.

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
                self.adr_active_orders.remove(pipeline_id)
            except ValueError:
                pass

    def handleFill(self, message, exchange, write_to_exchange, message_history, trade_pipelines):
        # calculate the PnL
        # Resolve Fill order_id to relevant pipeline
        pipeline_id = message_history[message['order_id']]['pipeline']
        pipeline = trade_pipelines[pipeline_id]
        # Resolve Fill order_id to relevant execution message
        execution_message = message_history[message['order_id']]

        # Update the fill
        if execution_message['symbol'] == 'VALBZ':
            pipeline['total_fill_adr_stock'] += message['size']
        elif execution_message['symbol'] == 'VALE':
            pipeline['total_fill_adr'] += message['size']
        # Update the PnL
        # TODO
        # Update the position
        if execution_message['symbol'] == 'VALBZ':
            if pipeline['dirStock'] == 'BUY':
                self.adr_stock_total_position += message['size']
            elif pipeline['dirStock'] == 'SELL':
                self.adr_stock_total_position -= message['size']
        elif execution_message['symbol'] == 'VALE':
            if pipeline['dirADR'] == 'BUY':
                self.adr_total_position += message['size']
            elif pipeline['dirADR'] == 'SELL':
                self.adr_total_position -= message['size']
        
        if pipeline['status'] != 'CANCELLED_BY_EXCHANGE':
            if pipeline['total_fill_adr_stock'] >= pipeline['sizeStock'] and pipeline['total_fill_adr'] >= pipeline['sizeADR']:
                # Convert all the ADR into stock
                if pipeline['dirADR'] == 'BUY':
                    convert_dir = 'SELL'
                elif pipeline['dirADR'] == 'SELL':
                    convert_dir = 'BUY'
                convert_msg = {
                    "type": "convert",
                    "order_id": len(message_history),
                    "symbol": "VALE",
                    "dir": convert_dir,
                    "size": pipeline['sizeADR']
                }
                write_to_exchange(exchange, convert_msg)
                pipeline['message_hist'].append(len(message_history))
                convert_msg['pipeline'] = pipeline_id
                message_history.append(convert_msg)

                # Complete and remove pipeline from active_orders
                pipeline['status'] = 'COMPLETED'
                try:
                    self.adr_active_orders.remove(pipeline_id)
                except ValueError:
                    pass
        else:
            # A FILL is received after an OUT is received
            # I think this will not happen, but just in case:
            print("WARN: FILL received after OUT")
            # There isn't anything to handle though, just a fyi message.