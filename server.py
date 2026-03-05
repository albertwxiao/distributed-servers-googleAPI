import asyncio
import time
import re


serverID = "Bailey"
log_dir = "logs/bailey.txt"
READ_BUFFER = 255


def log_prefix(mode):
    match mode:
        case 0:
            # input from client
            return "#>>"
        case 1:
            # output to client
            return "#<<"
        case 2:
            # input from server
            return "%>>"
        case 3:
            # output to server
            return "%<<"
        case _:
            raise Exception("invalid mode")

def log_write(message, mode):
    log_msg = log_prefix(mode) + " " + message + "\n"
    with open(log_dir, 'a') as f:
        f.write(log_msg)

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
    raise Exception("ClientNotFound")

def make_error_msg(message, e):
    return "? " + message + str(e)


async def respond_IAMAT(split_msg):
    print("Responding to IAMAT")
    time_diff = time.time() - float(split_msg[3])
    if time_diff >= 0:
        time_diff = "+" + str(time_diff)
    else:
        time_diff = "-" + str(time_diff)
    message = " ".join(["AT", serverID, time_diff, split_msg[1], split_msg[2], split_msg[3]])
    update_clientInfo(message)
    return message


async def respond_WHATSAT(split_msg):
    print("Responding to WHATSAT")
    
    if (int(split_msg[2]) > 50) or (int(split_msg[3]) > 20):
        raise Exception("InvalidPlaceArgs")
    message = (get_clientInfo(split_msg[1]) + " Google place info")

    return message


async def handle_client(reader, writer):
    data = await reader.read(READ_BUFFER)
    message = data.decode()
    log_write(message, 0)

    try:
        split_message = re.split('[ \n\r\t]+', message.strip())

        if split_message[0] == "IAMAT":
            output_msg = await respond_IAMAT(split_message)
        elif split_message[0] == "WHATSAT":
            output_msg = await respond_WHATSAT(split_message)
        else:
            raise Exception("Command did not match any options")

    except Exception as e:
        output_msg = make_error_msg(message, e)

    log_write(output_msg, 1)
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
