import asyncio
import websockets
import shlex
import i2c44780

LCD = None

class Response():
    OK = 'OK'
    ERR = 'ERR'

    def __init__(self, status, msg=''):
        self.msg = msg
        self.status = status

    def line(self):
        return '{}: {}'.format(self.status, self.msg)

def ok(msg=''):
    return Response(Response.OK, msg)

def error(msg=''):
    return Response(Response.ERR, msg)

def cmd_line(args):
    if len(args) < 2:
        return error('line: insufficient args, 2 expected')
    else:
        LCD.write(' '.join(args[1:]), int(args[0]))
        return ok()

def cmd_clear():
    LCD.clear()
    return ok()

def cmd_backlight(args):
    if len(args) < 1:
        return error('backlight: insufficient args, 1 expected')
    else:
        if args[0].strip().lower() == 'off':
            LCD.backlight(False)
            return ok()
        elif args[0].strip().lower() == 'on':
            LCD.backlight(True)
            return ok()
        else:
            return error('backlight: unknown arg, either on or off')

def handle_command(cmd):
    tokens = shlex.split(cmd)
    if len(tokens) == 0:
        return error('empty command line')

    cmd = tokens[0].strip().lower()
    args = tokens[1:]
    if cmd == 'line':
        return cmd_line(args)

    elif cmd == 'clear':
        return cmd_clear()

    elif cmd == 'backlight':
        return cmd_backlight(args)

    else:
        return error('{}: unknown command'.format(cmd))

@asyncio.coroutine
def serve(websocket, path):
    cmdline = yield from websocket.recv()
    response = handle_command(cmdline)

    yield from websocket.send(response.line())
    print("> {}".format(response.line()))


def main():
    global LCD
    LCD = i2c44780.I2C_44780()
    start_server = websockets.serve(serve, 'localhost', 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()
