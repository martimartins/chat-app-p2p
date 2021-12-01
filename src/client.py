"""Client/Server TCP socket Protocol
O Cliente irá inicar uma conexão com o servidor
e receber ips de clientes que já se tiveram conectado anteriormente.
Após o cliente receber a lista de clientes, irá conectar-se a todos eles.

De seguida, irá começar a ouvir conexões de clientes,
para assim, um cliente conseguir detetar novos clientes
recebendo handshake e adicionando o cliente à lista de clientes connectados.

@author: Martim Martins
@class: RCOM
"""
import asyncio
import socket
import logging

from typing import (
    TYPE_CHECKING,
    Optional,
    TypeVar,
    List,
    ClassVar,
    Tuple,
    Union,
    Any,
    Type,
)

_logger = logging.getLogger("client")

TC = TypeVar(name="TC", bound="TCPClient")
SERVER: Optional[Tuple[str, int]] = None


def _init_args_():
    from argparse import ArgumentParser

    parser = ArgumentParser()

    # Configurar argumento para debug
    parser.add_argument("-d", "--debug", default=False, action="store_true")

    # Configurar argumento para server ip dinamico
    parser.add_argument(
        "-s",
        "--server",
        default="127.0.0.1",  # localhost
        type=str,
        help="Ip do servidor que o cliente ira tentar se connectar e ter a lista de clientes disponíveis.",
    )

    # Configurar argumento para server port
    parser.add_argument(
        "-p",
        "--port",
        default=7472,
        type=int,
        help="Porta onde o servidor está a alucar.",
    )

    # returnar agumentos formatados
    return parser.parse_args()


async def ainput(prompt: Any = ""):
    """Este method ira executar :meth:`input` em uma thread em separado do event loop asyncio,
    que ira fazer o input executar de forma assíncrona."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)


class TCPClient(asyncio.Protocol):
    """Class que representará 1 cliente connectado
    a este cliente,

    Esta class ira ser instanceada para cada conexão feita."""

    name: ClassVar[Optional[str]] = None
    clients: ClassVar[List[asyncio.transports.BaseTransport]] = []

    # Gerar uma porta valido
    _sock: ClassVar[Union[socket.socket, Tuple[str, int]]] = socket.socket()

    if TYPE_CHECKING:
        loop: asyncio.AbstractEventLoop
        name: str

    def __init__(self, loop) -> None:
        self.loop = loop or asyncio.get_event_loop()

        if not self.name:
            self.name = input("Escreva um nome: ")[:40] or "Unknow"

    async def _init_server_(self):
        server = await self.loop.create_server(lambda: self, *self._sock)

        _logger.debug(
            "A ouvir clientes em %s",
            "".join(str(sock.getsockname()) for sock in server.sockets),
        )

    @classmethod
    async def run(cls, loop: asyncio.AbstractEventLoop):
        # Instancear o objecto,
        self = cls(loop)

        # Gerar a porta valida.
        self._sock.bind(("0.0.0.0", 0))
        addr = self._sock.getsockname()
        self._sock.close()
        self._sock = addr

        # Criar uma conecão com o servidor para receber o ips de clientes
        await self.recv_clients()

        # Iniciar um "servidor", que
        # permitira clientes se connectarem a este cliente.
        await self._init_server_()

        loop.create_task(self.chat())

    async def broadcast(self, data: str):
        """Este method ira enviar data
        para todos os clientes que tirevem
        connectados com este cliente.

        Parametros
        ---------
        data: :class:`str`
            Data que ira ser enviada.
        """
        buffer = data.encode("utf-8")

        for transport in self.clients:
            try:
                transport.write(buffer)
            except:
                # tirar o cliente da cache
                # se ouver algum error ao enviar data
                _logger.info(
                    "Client `%s` foi removido devido a não esta disponível",
                    transport.get_extra_info("peername"),
                )
                self.clients.remove(transport)

    async def connect_peers(self, clients: List[Tuple[str, int]]):
        # Connectar a todos os clientes recebidos pelo servidor.
        for client in clients:
            try:
                await self.loop.create_connection(lambda: self, *client)
            except:
                _logger.error("Error ao tentar connectaro com o peer `%s`", client)

    async def recv_clients(self) -> None:
        try:
            # Inciar uma conexão com o servidor
            _logger.debug("A tentar inicial uma conexão com o servidor (`%s`)", SERVER)
            r, w = await asyncio.open_connection(*SERVER, local_addr=self._sock)
        except Exception:
            _logger.warning(
                "Ocoreu um error ao connectar-se ao servidor,\nNão foi possivel obter a list de clientes connectados a pool.\nA tentar novamente em 5s..."
            )
            await asyncio.sleep(5)
            return await self.recv_clients()

        # Receber data do servidor
        data = await r.read(2048)

        if not data:
            _logger.warning("Servidor enviou EOF")
            await asyncio.sleep(5)
            return await self.recv_clients()

        # Fazer a conexão com todos os clientes que foram recebidos do servidor
        self.loop.create_task(
            self.connect_peers([x.split(":") for x in data.decode().split("-") if x])
        )

        # Fechar a conexão entre o servidor
        # Porque não existe necessidade de continuar
        # com a conexão com o servidor.
        w.close()
        _logger.debug("Conexão com o servidor `%s` foi fechada com sucesso.", SERVER)

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        # Quando ouver um cliente a connectar-se a este cliente,
        # Ira adicionar a cache de clientes.
        _logger.debug(
            "Conexão recebida do cliente `%s`", transport.get_extra_info("peername")
        )
        self.clients.append(transport)

    def data_received(self, data: bytes) -> None:
        # Quando houver data recebida,
        # Ira ser printada no teminal

        print(data.decode())

    async def chat(self) -> None:
        while 1:
            msg = await ainput(">>> ")

            # Verificar se existe realmente texto na messagem.
            if msg:
                print(f"<Eu> :: {msg}")
                await self.broadcast(f"<{self.name}> :: {msg}")


if __name__ == "__main__":
    # Opção para server ip dinãmico.
    args = _init_args_()

    # Configurar server de acordo com argv dado
    # dado ao iniciar a script.
    SERVER = (args.server, args.port)

    # Configurar logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.CRITICAL,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(TCPClient.run(loop))

    try:
        loop.run_forever()
    finally:
        loop.close()
