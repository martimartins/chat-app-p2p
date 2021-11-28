"""Server TCP socket Protocol,
o servidor ira ser responsavel de dar uma lista de ips
(clientes que se connectaram anteriormente) aos
clientes que se connectão ao servidor

@author: Martim Martins
@class: RCOM
"""
import asyncio

from typing import List, Optional

SERVER = ("0.0.0.0", 7472)

class TCPServer(asyncio.Protocol):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.clients: List[asyncio.transports.BaseTransport] = []

    @classmethod
    async def run(cls, loop: asyncio.AbstractEventLoop):
        self = cls(loop)

        server = await loop.create_server(lambda: self, *SERVER)
        print(f"[SERVER] Servidor inicado em {SERVER}.")

        async with server:
            await server.serve_forever()

    def peername(self, t):
        return t.get_extra_info('peername')

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        print("Nova conexão ->", self.peername(transport))

        fmt = "-".join(map(lambda c: ':'.join(str(x) for x in self.peername(c)), self.clients)) or "-"
        transport.write(fmt.encode("utf-8"))
        
        self.clients.append(transport)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        print("Parece que alguem saiu!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop() 
    loop.run_until_complete(TCPServer.run(loop))

