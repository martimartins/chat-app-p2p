# P2P Group Chat
Este chat app ira permitir que clientes entrem em uma sala que lá poderam falar sem existir um servidor a receber todos os envios de dados dos clientes/peers, possibilitando assim o chat app funcione sem um servidor centralizado.

## Arquitectura
Este p2p exemple utiliza biblioteca [asyncio](https://docs.python.org/3/library/asyncio-protocol.html) e [socket](https://docs.python.org/3/library/socket.html) para utilização de socket protocol para os clientes poderem comunicar entre clientes com protocol TCP de uma forma assíncrona.

### Cliente
O Cliente irá inicar uma conexão com o servidor
e receber ips de clientes que já se tiveram conectado anteriormente, ou seja que estão na room.
Após o cliente receber a lista de clientes, irá estabelecer uma conexão a todos os clientes da lista.
De seguida, irá começar a ouvir conexões de clientes para detetar novos clientes a entrar na room,
Recebendo handshake e adicionando o cliente à lista de clientes connectados.
![](https://cdn.discordapp.com/attachments/860150349985218573/911737056680611880/p2p_data_sending.drawio.png)
> Ilustração de um peer a fazer broadcast de informação para outros peers

### Servidor
O servidor ira ser responsável de dar uma lista de ips
(clientes que se connectaram anteriormente ou seja que estão na room) aos
novos clientes que se connectão ao servidor.

## Desenvolvimento
Para rodar este chat, tera de executar o servidor e o client, utilize para o servidor [Python >3.8](https://www.python.org/downloads/release/python-380/) e para o cliente pode utilizar [Python >3.7](https://www.python.org/downloads/release/python-370/).
#### Rodar servidor
Iniciar o servidor, que ira automaticamente iniciar um socket server em localhost na porta `7472`
```
~/chat-app-p2p/src$ # LINUX
~/chat-app-p2p/src$ python3 server.py

C:\chat-app-p2p\src> # WINDOWS
C:\chat-app-p2p\src> py server.py
```
#### Rodar cliente
Iniciar um cliente, que ira se connectar ao servidor `127.0.0.1:7472` by default, o ip e a porta do servidor que o cliente ira se conectar-se, pode ser alterado utilizando flag `--server <ip>` e para porta flag `--port <port>`.
```
~/chat-app-p2p/src$ # LINUX
~/chat-app-p2p/src$ python3 client.py

C:\chat-app-p2p\src> # WINDOWS
C:\chat-app-p2p\src> py client.py
```