import asyncio
import time
import re
import argparse
from srv_bailey import Bailey
from srv_bona import Bona


IP_address = '127.0.0.1'
READ_BUFFER = 255

def get_port(ID):
    if ID == "Bailey":
        result = 12001
    elif ID == "Bona":
        result = 12032
    elif ID == "Campbell":
        result = 12063
    elif ID == "Clark":
        result = 12094
    elif ID == "Jaquez":
        result = 12125
    else:
        raise Exception("invalid ID")
    return result

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

def log_write(message, mode, log_dir):
    log_msg = log_prefix(mode) + " " + message + "\n"
    with open(log_dir, 'a') as f:
        f.write(log_msg)

def update_clientInfo(unsplit_msg, srv):
    clientInfo = srv.clientInfo
    newmsg = unsplit_msg.split(' ')
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == newmsg[3]:
            clientInfo[i] = newmsg
            return
    clientInfo.append(newmsg)

def get_clientInfo(client, clientInfo):
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == client:
            return (" ".join(clientInfo[i]))
    raise Exception("ClientNotFound")

def make_error_msg(message):
    return "? " + message

async def send_to_servers(message, srv, source):
    for adjServer in srv.connectedServers:
        if adjServer != source:
            await send_to_server(message, adjServer)

async def send_to_server(message, dest):
    reader, writer = await asyncio.open_connection(IP_address, get_port(dest))
    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def respond_IAMAT(split_msg, srv):
    print("Responding to IAMAT")
    time_diff = time.time() - float(split_msg[3])
    if time_diff >= 0:
        time_diff = "+" + str(time_diff)
    else:
        time_diff = "-" + str(time_diff)
    message = " ".join(["AT", srv.ID, time_diff, split_msg[1], split_msg[2], split_msg[3]])
    update_clientInfo(message, srv)
    return message


async def respond_WHATSAT(split_msg, srv):
    print("Responding to WHATSAT")
    
    if (int(split_msg[2]) > 50) or (int(split_msg[3]) > 20):
        raise Exception("InvalidGoogPlaceArgs")
    message = (get_clientInfo(split_msg[1], srv.clientInfo) + " Google place info")

    return message


def make_handle_client(srv):
    async def handle_client(reader, writer):
        data = await reader.read(READ_BUFFER)
        message = data.decode()
        log_write(message, 0, srv.log_dir)

        try:
            split_message = re.split('[ \n\r\t]+', message.strip())

            if split_message[0] == "IAMAT":
                output_msg = await respond_IAMAT(split_message, srv)
            elif split_message[0] == "WHATSAT":
                output_msg = await respond_WHATSAT(split_message, srv)
            else:
                raise Exception("Command did not match any options")

        except Exception as e:
            output_msg = make_error_msg(message)
            print("Error: ", str(e))

        log_write(output_msg, 1, srv.log_dir)
        writer.write(output_msg.encode())
        await writer.drain()
        print("Close the connection")
        writer.close()
        await writer.wait_closed()
    return handle_client


async def start_server_instance(srv):
    server = await asyncio.start_server(make_handle_client(srv), IP_address, get_port(srv.ID))
    print('Started server on port', get_port(srv.ID))

    async with server:
        await server.serve_forever()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("srvID", help="The server ID.")
    args = parser.parse_args()

    bailey = Bailey()
    bona = Bona()

    if args.srvID == "Bailey":
        await start_server_instance(bailey)
    elif args.srvID == "Bona":
        await start_server_instance(bona)
    else:
        print("invalid args")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server closed via keyboard interrupt")

