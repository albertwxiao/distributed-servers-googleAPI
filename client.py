import asyncio
import time
import argparse

clientID = "strawberry.cs.ucla.edu"
location = "+34.063700-118.445400"
IP_address = '127.0.0.1'
READ_BUFFER = 8000

async def tcp_client(message, port):
    reader, writer = await asyncio.open_connection(
        IP_address, port)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(READ_BUFFER)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def I_am_at(ID, location, port): 
    message = " ".join(["IAMAT", ID, location, str(time.time())])
    await tcp_client(message, port)

async def whats_at(ID, radius, upper_bound, port):
    message = " ".join(["WHATSAT", ID, str(radius), str(upper_bound)])
    await tcp_client(message, port)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="The server port.")
    parser.add_argument("action", help="The client action.")
    args = parser.parse_args()

    try:
        if args.action == "imat":
            await I_am_at(clientID, location, args.port)
        elif args.action == "what":
            await whats_at(clientID, 3, 2, args.port)
    except ConnectionError as e:
        print(e)
    
asyncio.run(main())

