import abc
import websockets
import json
import requests
import asyncio

class WSClientBase(abc.ABC):
    def __init__(self, url: str, message: dict | list):
        self.session = websockets.connect(url)
        self.message = message
        self.data = {}
        
    async def __aenter__(self):
        await self.session.__aenter__()
        return self
    
    async def __aexit__(self, *args, **kwargs):
        await self.session.__aexit__(*args, **kwargs)
        
    async def start(self):
        raise NotImplemented(f"Start for ws client {self.url} not created")

    def parser(self, pair: dict):
        raise NotImplemented(f"Parser for ws client {self.url} not created")

class Binance(WSClientBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self):
        async with self.session as session:
            await session.send(json.dumps(self.message))
            async for message in session:
                for pair_data in json.loads(message):
                    try:
                        self.data[pair_data['s']] = pair_data['c']
                    except Exception as _:
                        continue

class Kraken(WSClientBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self, coins_url):
        request = requests.get(coins_url)
        data = request.text
        pairs = []
        for pair_data in json.loads(data)['result'].values():
            pairs.append(pair_data['wsname'])
        
        await self.parser(pairs)

    async def parser(self, symbols):
        self.message['pair'] = symbols
        async with self.session as session:
            await session.send(json.dumps(self.message))
            async for message in session:
                try:
                    symbol = json.loads(message)[3].replace('/','')
                    price = json.loads(message)[1]['c'][0]
                    self.data[symbol] = price
                except:
                    continue