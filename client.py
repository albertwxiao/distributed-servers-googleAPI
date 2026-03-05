import asyncio
import time

async def tcp_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 12001)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def I_am_at(ID, location): 
    message = " ".join(["IAMAT", ID, location, str(time.time())])
    await tcp_client(message)

async def whats_at(ID, radius, upper_bound):
    message = " ".join(["WHATSAT", ID, str(radius), str(upper_bound)])
    await tcp_client(message)

async def main():
    clientID = "strawberry.cs.ucla.edu"
    location = "+34.063700-118.445400"
    await I_am_at(clientID, location)
    # await whats_at(clientID, 3, 2)
    
asyncio.run(main())

