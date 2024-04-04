from websocket_manager import Binance, Kraken
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from typing import Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(binance.start())
    asyncio.create_task(kraken.start('https://api.kraken.com/0/public/AssetPairs'))
    yield
    
app = FastAPI(lifespan=lifespan)

binance = Binance("wss://stream.binance.com:9443/ws", {
                "method": "SUBSCRIBE",
                "params": [f"!ticker@arr"],
                "id": 1
            })

kraken = Kraken("wss://ws.kraken.com/", {"event":"subscribe", "subscription":{"name":"ticker"}, "pair":["BTC/USDT"]})


@app.get("/prices")
async def get_prices(pair: Optional[str] = None, exchange: Optional[str] = None):
    if exchange is None and pair is None:
        aggregation_dict = {}
        if len(binance.data) > len(kraken.data):
            for key, value in binance.data.items():
                try:
                    aggregation_dict[key] = {"kraken":kraken.data[key], "binance":value}
                except:
                    continue
            return {"data":aggregation_dict}
        
        if len(binance.data) > len(kraken.data):
            for key, value in kraken.data.items():
                try:
                    aggregation_dict[key] = {"kraken":value, "binance":binance.data[key]}
                except:
                    continue
            return {"data":aggregation_dict}

    if pair is not None and exchange is None:
        return {"error":"You cant use only pair there."}
    
    if exchange.lower() == 'binance':
        if pair is not None and pair.upper() in binance.data:
            return {"pair":pair.upper(),"data":f"{pair.upper()}:{binance.data[pair.upper()]}"}
        return {"data":binance.data}
    
    if exchange.lower() == 'kraken':
        if pair is not None and pair.upper() in kraken.data:
            return {"pair":pair.upper(),"data":f"{pair.upper()}:{kraken.data[pair.upper()]}"}
        return {"data":kraken.data}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)