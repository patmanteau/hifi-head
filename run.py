import asyncio
import websockets
import shlex
import i2c44780

DISPLAY = None
ANIM_FUTURE = None

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

class Line():
    def __init__(self, text='', offset=0, incr=1):
        self.text = text
        self.offset = offset
        self.incr = incr

class Display():
    def __init__(self):
        self.anim_future = None
        self.lcd = i2c44780.I2C_44780()
        self.lines = [Line() for i in range(4)]

    def clear(self):
        self.lcd.clear()

    def backlight_on(self):
        self.lcd.backlight(True)

    def backlight_off(self):
        self.lcd.backlight(False)

    #@asyncio.coroutine
    def start_animation(self):
        if self.anim_future is None or self.anim_future.done():
            self.anim_future = asyncio.async(self.step_animation())
            return ok('animation started')
        else:
            return ok('animation was already running, nothing to be done')
            #asyncio.run_until_complete(run_animation)

    def stop_animation(self):
        if self.anim_future is not None and not self.anim_future.done():
            self.anim_future.cancel()
            return ok('animation stopped')
        else:
            return ok('animation was not running, nothing to be done')

    #@asyncio.coroutine
    def step_animation(self):
        print('anim step')
        for index, line in [(i, l) for (i, l) in enumerate(self.lines) if len(l.text) > 20]:
            next_offset = line.offset + line.incr
            if next_offset < 0:
                next_offset = 0
                line.incr *= -1
            elif len(line.text) - next_offset < 20:
                next_offset = len(line.text) - 20
                line.incr *= -1
            line.offset = next_offset
            next_text = line.text[line.offset:line.offset+20]
            self.lcd.write(next_text, index)
            print(line.text, ':', line.offset, ':', line.offset+20)
            print(next_text)

    def set_line(self, i, text):
        self.lines[i] = Line(format(text, ' <20'))
        self.lcd.write(self.lines[i].text[:20], i)
        print('line {}: {}'.format(i, self.lines[i].text))

def cmd_line(args):
    if len(args) < 2:
        return error('line: insufficient args, 2 expected')
    else:
        DISPLAY.set_line(int(args[0]), ' '.join(args[1:]))
        return ok()

def cmd_clear():
    DISPLAY.clear()
    return ok()

def cmd_backlight(args):
    if len(args) < 1:
        return error('backlight: insufficient args, 1 expected')
    else:
        if args[0].strip().lower() == 'off':
            DISPLAY.backlight_off()
            return ok()
        elif args[0].strip().lower() == 'on':
            DISPLAY.backlight_on()
            return ok()
        else:
            return error('backlight: unknown arg, either on or off')

@asyncio.coroutine
def step_animation():
    while True:
        DISPLAY.step_animation()
        yield from asyncio.sleep(1)

def cmd_animation(args):
    global ANIM_FUTURE

    if len(args) < 1:
        return error('animation: insufficient args, 1 expected')

    if args[0].strip().lower() == 'off':
        if ANIM_FUTURE is not None and not ANIM_FUTURE.done():
            ANIM_FUTURE.cancel()
            return ok('animation stopped')
        else:
            return ok('animation was not running, nothing to be done')
        #return DISPLAY.stop_animation()

    elif args[0].strip().lower() == 'on':
        if ANIM_FUTURE is None or ANIM_FUTURE.done():
            ANIM_FUTURE = asyncio.async(step_animation())
            return ok('animation started')

        else:
            return ok('animation was already running, nothing to be done')
            #asyncio.run_until_complete(run_animation)
        #return DISPLAY.start_animation()

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
        DISPLAY.clear()
        return ok('display cleared')

    elif cmd == 'backlight':
        return cmd_backlight(args)

    elif cmd == 'animation':
        return cmd_animation(args)

    else:
        return error('{}: unknown command'.format(cmd))

@asyncio.coroutine
def serve(websocket, path):
    cmdline = yield from websocket.recv()
    response = handle_command(cmdline)

    yield from websocket.send(response.line())
    print("> {}".format(response.line()))


def main():
    global DISPLAY
    DISPLAY = Display()
    start_server = websockets.serve(serve, 'localhost', 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()
