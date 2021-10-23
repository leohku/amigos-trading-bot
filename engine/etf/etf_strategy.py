class ETFStrategy():
    def __init__(self):
        pass

    def getStrategies(self, etf_asks, etf_bids, bond_asks, bond_bids, gs_asks, gs_bids, ms_asks, ms_bids, wfc_asks, wfc_bids):

        etf_best_bid = etf_bids[0][0]
        etf_best_ask = etf_asks[0][0]

        bond_best_bid = bond_bids[0][0]
        bond_best_ask = bond_asks[0][0]

        gs_best_bid = gs_bids[0][0]
        gs_best_ask = gs_asks[0][0]

        ms_best_bid = ms_bids[0][0]
        ms_best_ask = ms_asks[0][0]

        wfc_best_bid = wfc_bids[0][0]
        wfc_best_ask = wfc_asks[0][0]

        basket_bid = bond_best_bid + gs_best_bid + ms_best_bid + wfc_best_bid
        basket_ask = bond_best_ask + gs_best_ask + ms_best_ask + wfc_best_ask

        print(f"GS Price: {gs_best_bid}")

        # if (etf_best_bid - basket_ask) > 10:

        #     return [{
        #     "action": "SELL",
        #     "price": etf_best_bid,
        #     "size": 1
        # }]

        # if (basket_bid - etf_best_ask) > 3:

        #     return [{
        #     "action": "BUY",
        #     "price": etf_best_ask,
        #     "size": 1
        # }]

        # else:
        #     return []

        return [
            {
            "action": "SELL",
            "price": 4290,
            "size": 10
            },
            {
            "action": "SELL",
            "price": 4280,
            "size": 20
            },
            {
            "action": "SELL",
            "price": 4270,
            "size": 20
            },
            {
            "action": "BUY",
            "price": 4260,
            "size": 20
            },
            {
            "action": "BUY",
            "price": 4250,
            "size": 20
            },
            {
            "action": "BUY",
            "price": 4240,
            "size": 10
            }
        ]