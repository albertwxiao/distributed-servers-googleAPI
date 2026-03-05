import asyncio
import time
import sys


serverID = "Bailey"

clientInfo = []
def update_clientInfo(newmsg):
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == newmsg[3]:
            clientInfo[i] = newmsg
            return
    clientInfo.append(newmsg)

def get_clientInfo(client):
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == client:
            return (" ".join(clientInfo[i]))
    print("Client was not found")
    sys.exit(1)

async def echo(message, writer, data):
    print(f"Received {message!r}")
    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

async def respond_IAMAT(received_msg, writer):
    print("Responding to IAMAT")
    time_diff = time.time() - float(received_msg[3])
    if time_diff >= 0:
        time_diff = "+" + str(time_diff)
    else:
        time_diff = "-" + str(time_diff)

    split_message = ["AT", serverID, time_diff, received_msg[1], received_msg[2], received_msg[3]]
    message = " ".join(split_message)
    update_clientInfo(split_message)
    writer.write(message.encode())
    await writer.drain()

async def respond_WHATSAT(received_msg, writer):
    print("Responding to WHATSAT")
    if (int(received_msg[2]) > 50) or (int(received_msg[3]) > 20):
        print("Received invalid arguments from client")
        sys.exit(1)

    message = (get_clientInfo(received_msg[1]) + "Google place info")
    writer.write(message.encode())
    await writer.drain()


async def handle_client(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    split_message = message.split(' ')      # handle leading or trailing white spaces?

    if split_message[0] == "IAMAT":
        await respond_IAMAT(split_message, writer)
    elif split_message[0] == "WHATSAT":
        await respond_WHATSAT(split_message, writer)
    else:
        print("Received message but did not match any valid options")

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', 12001)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

asyncio.run(main())
