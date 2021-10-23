class BondStrategy():
    def __init__(self):
        pass

    def getStrategies(self, fair_value, risk_limit, bond_asks, bond_bids, total_position, pnl, bond_active_orders, trade_pipelines):
        # WARNING: Do not mutate any passed in arguments

        # Returns an array of actions
        # TODO: complete with real strategy

        # Single action
        # return [{
        #     "action": "BUY",
        #     "price": 990,
        #     "size": 10
        # }]

        # Multi-action
        return [
            {
            "action": "SELL",
            "price": 8430,
            "size": 25
            },
            {
            "action": "SELL",
            "price": 8410,
            "size": 25
            },
            {
            "action": "BUY",
            "price": 8390,
            "size": 25
            },
            {
            "action": "BUY",
            "price": 8370,
            "size": 25
            }
        ]
