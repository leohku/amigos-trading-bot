from discord_webhook import DiscordWebhook, DiscordEmbed

class Logger():
    
    def __init__(self, test_mode):
        self.logger = None
        self.name = "Amigos"
        self.bond_pnl = -1

        self.mode = 'testing' if test_mode else 'live' 

        # discord server
        self.webhook_url = ""

        self.webhook = DiscordWebhook(url=self.webhook_url)
        self.embed = DiscordEmbed(title=self.mode+ 'Results', description='round ended', color='03b2f8')

    def logBond(self, bond_pnl):
        # TODO: take in a dictionary of message and unpack into fields 
        # e.g. environment = test/live/local

        self.bond_pnl = bond_pnl
    
        self.embed.add_embed_field(name='Bond PnL', value=self.bond_pnl)
        
        # embed.add_embed_field(name='Environment', value='Local Test')

    def logADR(self, adr_pnl):
        # TODO: take in a dictionary of message and unpack into fields 
        # e.g. environment = test/live/local
    
        self.embed.add_embed_field(name='ADR PnL', value=adr_pnl)
        
        # embed.add_embed_field(name='Environment', value='Local Test')


    def send(self):
        self.embed.set_timestamp()
        self.webhook.add_embed(self.embed)
        if self.bond_pnl < 0:
            return None
        response = self.webhook.execute()
        return response