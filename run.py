import asyncio
import websockets
import shlex
import i2c44780

LCD = None

def cmd_line(args):
    print(args)
    if len(args) < 2:
        return 'ERR: line: insufficient args, 2 expected'
    else:
        LCD.write(' '.join(args[1:]), int(args[0]))
        return 'OK'

def cmd_clear():
    LCD.clear()
    return 'OK'

def handle_command(cmd):
    tokens = shlex.split(cmd)
    if len(tokens) == 0:
        return 'ERR: empty command line'

    cmd = tokens[0].strip().lower()
    args = tokens[1:]
    if cmd == 'line':
        return cmd_line(args)

    elif cmd == 'clear':
        return cmd_clear()

    else:
        return '{}: unknown command'.format(cmd)

@asyncio.coroutine
def serve(websocket, path):
    cmdline = yield from websocket.recv()
    response = handle_command(cmdline)

    yield from websocket.send(response)
    print("> {}".format(response))


def main():
    global LCD
    LCD = i2c44780.I2C_44780()
    start_server = websockets.serve(serve, 'localhost', 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()
