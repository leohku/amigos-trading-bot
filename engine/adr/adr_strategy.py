class ADRStrategy():
    def __init__(self):
        pass

    def getStrategies(self, risk_limit, stock_risk_limit, conversion_fee, adr_asks, adr_bids, adr_stock_asks, adr_stock_bids, adr_total_position, adr_stock_total_position, pnl, adr_active_orders, trade_pipelines):

        adr_best_bid = adr_bids[0][0]
        adr_best_ask = adr_asks[0][0]

        adr_stock_best_bid = adr_stock_bids[0][0]
        adr_stock_best_ask = adr_stock_asks[0][0]

        net_position = adr_total_position + adr_stock_total_position

        if net_position != 0:
            if adr_total_position > 0:
                return [{
                "type": "HEDGE",
                "action": "SELL",
                "price": adr_stock_best_bid,
                "size": adr_total_position
            }]

            elif adr_total_position < 0:
                return [{
                "type": "HEDGE",
                "action": "BUY",
                "price": adr_stock_best_ask,
                "size": adr_total_position
            }]

            elif adr_stock_total_position > 0:
                return [{
                    "type": "HEDGE",
                    "action": "SELL",
                    "price": adr_best_bid,
                    "size": adr_stock_total_position
                }]

            elif adr_stock_total_position < 0:
                return [{
                    "type": "HEDGE",
                    "action": "BUY",
                    "price": adr_best_ask,
                    "size": adr_stock_total_position
                }]

        if (adr_best_bid - adr_stock_best_ask) > conversion_fee:

            return [{
                "type": "ARB",
                "actionADR": "SELL",
                "priceADR": adr_best_bid,
                "sizeADR": 1,
                "actionStock": "BUY",
                "priceStock": adr_stock_best_ask,
                "sizeStock": 1
            }]

        elif (adr_stock_best_bid - adr_best_ask) > conversion_fee:

            return [{
                "type": "ARB",
                "actionADR": "BUY",
                "priceADR": adr_best_ask,
                "sizeADR": 1,
                "actionStock": "SELL",
                "priceStock": adr_stock_best_bid,
                "sizeStock": 1
            }]

        else:
            return []