import asyncio
import time
import re
import argparse
from srv_bailey import Bailey
from srv_bona import Bona
from srv_campbell import Campbell
from srv_clark import Clark
from srv_jaquez import Jaquez
from googleplace import request_google_api


IP_address = '127.0.0.1'
READ_BUFFER = 500

def get_port(ID):
    if ID == "Bailey":
        port = 12001
    elif ID == "Bona":
        port = 12032
    elif ID == "Campbell":
        port = 12063
    elif ID == "Clark":
        port = 12094
    elif ID == "Jaquez":
        port = 12125
    else:
        raise Exception("invalid ID")
    return port

def log_prefix(mode):
    if mode == 0:
        # input from client or server
        return "#>>"
    elif mode == 1:
        # output to client
        return "#<<"
    elif mode == 3:
        # output to server
        return "%<<"
    else:
        raise Exception("invalid write mode")

def log_write(message, mode, log_dir):
    log_msg = log_prefix(mode) + " " + message
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
            return (clientInfo[i])
    raise Exception("ClientNotFound")

def check_clientInfo(split_msg, srv):
    clientInfo = srv.clientInfo
    clientID = split_msg[4]
    timestamp = split_msg[6]
    new_clientInfo = ["AT", split_msg[2], split_msg[3], split_msg[4], split_msg[5], split_msg[6]]
    for i in range (0, len(clientInfo)):
        if clientInfo[i][3] == clientID:
            if float(timestamp) > float(clientInfo[i][5]):
                clientInfo[i] = new_clientInfo
                return True
            else:
                return False
    clientInfo.append(new_clientInfo)
    return True

def make_error_msg(message):
    return "? " + message

async def propagate_to_servers(og_msg, srv):
    split_msg = og_msg.split(" ")
    if (split_msg[0] == 'AT'):
        send_msg = True
        source = "client"
        message = " ".join(["PROP", srv.ID, split_msg[1], split_msg[2], split_msg[3], split_msg[4], split_msg[5]])
    elif (split_msg[0] == 'PROP'):
        send_msg = check_clientInfo(split_msg, srv)
        source = split_msg[1]
        split_msg[1] = srv.ID
        message = " ".join(split_msg)
    else:
        raise Exception("invalid message")

    if send_msg:
        for adjServer in srv.connectedServers:
            if adjServer != source:
                log_write(message, 3, srv.log_dir)
                await send_to_server(message, adjServer)

async def send_to_server(message, dest):
    try:
        reader, writer = await asyncio.open_connection(IP_address, get_port(dest))
        writer.write(message.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        print("Sent propogation msg to", str(dest))
    except ConnectionError as e:
        print(e)


async def respond_IAMAT(split_msg, srv):
    print("Responding to IAMAT")
    time_diff = time.time() - float(split_msg[3])
    if time_diff >= 0:
        time_diff = "+" + str(time_diff)
    else:
        time_diff = "-" + str(time_diff)
    message = " ".join(["AT", srv.ID, time_diff, split_msg[1], split_msg[2], split_msg[3]])
    update_clientInfo(message, srv)
    await propagate_to_servers(message, srv)
    return message


async def respond_WHATSAT(split_msg, srv):
    print("Responding to WHATSAT")
    
    if (int(split_msg[2]) > 50) or (int(split_msg[3]) > 20):
        raise Exception("InvalidGoogPlaceArgs")
    clientInfo = get_clientInfo(split_msg[1], srv.clientInfo)
    location = clientInfo[4]
    radius = int(split_msg[2])
    maxCount = int(split_msg[3])
    google_place_info = await request_google_api(location, radius, maxCount)
    message = (" ".join(clientInfo) + "\n" + google_place_info)

    return message


def make_handle_connection(srv):
    async def handle_connection(reader, writer):
        data = await reader.read(READ_BUFFER)
        message = data.decode()
        log_write(message, 0, srv.log_dir)

        try:
            split_message = re.split('[ \n\r\t]+', message.strip())

            if split_message[0] == "IAMAT":
                output_msg = await respond_IAMAT(split_message, srv)
            elif split_message[0] == "WHATSAT":
                output_msg = await respond_WHATSAT(split_message, srv)
            elif split_message[0] == "PROP":
                print("Received propagation msg")
                await propagate_to_servers(message, srv)
                output_msg = None
            else:
                raise Exception("Command did not match any options")

        except Exception as e:
            output_msg = make_error_msg(message)
            print("Error: ", str(e))

        if output_msg != None:
            output_msg += "\n"
            log_write(output_msg, 1, srv.log_dir)
            writer.write(output_msg.encode())
            await writer.drain()
        print("Close the connection")
        writer.close()
        await writer.wait_closed()
    return handle_connection


async def start_server_instance(srv):
    server = await asyncio.start_server(make_handle_connection(srv), IP_address, get_port(srv.ID))
    print('Started server on port', get_port(srv.ID))

    async with server:
        await server.serve_forever()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("srvID", help="The server ID.")
    args = parser.parse_args()

    if args.srvID == "Bailey":
        bailey = Bailey()
        await start_server_instance(bailey)
    elif args.srvID == "Bona":
        bona = Bona()
        await start_server_instance(bona)
    elif args.srvID == "Campbell":
        campbell = Campbell()
        await start_server_instance(campbell)
    elif args.srvID == "Clark":
        clark = Clark()
        await start_server_instance(clark)
    elif args.srvID == "Jaquez":
        jaquez = Jaquez()
        await start_server_instance(jaquez)
    else:
        print("invalid args")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server closed via keyboard interrupt")

