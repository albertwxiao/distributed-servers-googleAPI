import asyncio
import time


serverID = "Bailey"
READ_BUFFER = 255

clientInfo = []
def update_clientInfo(unsplit_msg):
    newmsg = unsplit_msg.split(' ')
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == newmsg[3]:
            clientInfo[i] = newmsg
            return
    clientInfo.append(newmsg)

def get_clientInfo(client):
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == client:
            return (" ".join(clientInfo[i]))
    raise Exception("Client was not found")

def make_error_msg(message):
    return "? " + message

async def respond_IAMAT(received_msg):
    print("Responding to IAMAT")
    try:
        split_msg = received_msg.split(' ')
        time_diff = time.time() - float(split_msg[3])
        if time_diff >= 0:
            time_diff = "+" + str(time_diff)
        else:
            time_diff = "-" + str(time_diff)
        message = " ".join(["AT", serverID, time_diff, split_msg[1], split_msg[2], split_msg[3]])
        update_clientInfo(message)

    except Exception:
        message = make_error_msg(received_msg)

    return message


async def respond_WHATSAT(received_msg):
    print("Responding to WHATSAT")
    try:
        split_msg = received_msg.split(' ')
        if (int(split_msg[2]) > 50) or (int(split_msg[3]) > 20):
            raise Exception("Arguments are too large")
        message = (get_clientInfo(split_msg[1]) + " Google place info")

    except Exception:
        message = make_error_msg(received_msg)

    return message


async def handle_client(reader, writer):
    data = await reader.read(READ_BUFFER)
    message = data.decode()
    split_message = message.split(' ')      # does it handle leading or trailing white spaces?

    if split_message[0] == "IAMAT":
        output_msg = await respond_IAMAT(message)
    elif split_message[0] == "WHATSAT":
        output_msg = await respond_WHATSAT(message)
    else:
        output_msg = make_error_msg(message)

    writer.write(output_msg.encode())
    await writer.drain()
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
