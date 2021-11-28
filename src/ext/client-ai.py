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
import sys
import torch

from typing import TYPE_CHECKING, Optional, TypeVar, List, ClassVar, Tuple, Union, Any
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

_logger = logging.getLogger("client")

TC = TypeVar(name="TC", bound="TCPClient")
SERVER = ["192.168.0.3", 7472]

def _genarate_chat(self, text: str):
    input_id = self.tokenizer.encode(text + self.tokenizer.eos_token, return_tensors='pt')

    bot_input_ids = torch.cat([self.chat_ids, input_id], dim=-1) if self.chat_ids is not None else input_id

    chat_history_ids = self.model.generate(bot_input_ids, max_length=1000, pad_token_id=self.tokenizer.eos_token_id)
    self.chat_ids = chat_history_ids
    text = self.tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

    self.broadcast(f"<{self.name}> :: {text}")


class TCPClient(asyncio.Protocol):
    """Class que representará 1 cliente connectado
    a este cliente,

    Esta class ira ser instanceada para cada conexão feita."""
    tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-large")
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-large")

    name: ClassVar[Optional[str]] = None
    clients: ClassVar[List[asyncio.transports.BaseTransport]] = []

    # Gerar uma porta valido
    _sock: ClassVar[Union[socket.socket, Tuple[str, int]]] = socket.socket()

    chat_ids: Optional[Any] = None

    if TYPE_CHECKING:
        loop: asyncio.AbstractEventLoop
        name: str

    def __init__(self, loop) -> None:
        self.loop = loop or asyncio.get_event_loop()

        if not self.name:
            self.name = input("Escreva um nome: ")[:40]


    async def genarate_chat(self, text: str):
        with ThreadPoolExecutor(1, "AI_Chat") as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, _genarate_chat, self, text)

    async def _init_server_(self):
        server = await self.loop.create_server(lambda: self, *self._sock)

        _logger.info(
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

    def broadcast(self, data: str):
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
                _logger.info("Client removed")
                self.clients.remove(transport)

    async def connect_peers(self, clients: List[Tuple[str, int]]):
        for client in clients:
            try:
                await self.loop.create_connection(lambda: self, *client)
            except:
                _logger.error("Error ao tentar connectaro com o peer `%s`", client)

    async def recv_clients(self):
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
            _logger.info("Servidor enviou None EOF")
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

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        # Quando ouver um cliente a connectar-se a este cliente,
        # Ira adicionar a cache de clientes.
        _logger.info("Novo cliente %s", transport.get_extra_info("peername"))
        self.clients.append(transport)

    def data_received(self, data: bytes) -> None:
        # Quando houver data recebida,
        # Ira ser printada no teminal

        # formato: <Name> :: Data
        text = data.decode('utf-8').split(" :: ")

        print(data.decode())

        _logger.info("A começar a procurar uma resposta...")
        self.loop.create_task(self.genarate_chat(text[1]))
        _logger.info("Resposta encontrada `%s`", text)

if __name__ == "__main__":
    # Opção para server ip dinãmico.
    if len(sys.argv) >= 2:
        SERVER[0] = sys.argv[1]

    # Configurar logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(TCPClient.run(loop))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
