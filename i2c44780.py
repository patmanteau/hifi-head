# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
#from builtins import *

import smbus
from time import sleep
#from string import maketrans

# TODO: ugly umlaut hack

cap_uml_a = [0x0a, 0x00, 0x0e, 0x11, 0x1f, 0x11, 0x11, 0x00]
cap_uml_o = [0x0a, 0x00, 0x0e, 0x11, 0x11, 0x11, 0x0e, 0x00]
cap_uml_u = [0x0a, 0x00, 0x11, 0x11, 0x11, 0x11, 0x0e, 0x00]
_transtable = {
    ord('Ä'): chr(0x05),
    ord('ä'): chr(0xe1),
    ord('Ö'): chr(0x06),
    ord('ö'): chr(0xef),
    ord('Ü'): chr(0x07),
    ord('ü'): chr(0xf5),
    ord('ß'): chr(0xe2)
}

class I2CDevice:
    def __init__(self, addr, port = 1):
        self.addr = addr
        self.bus = smbus.SMBus(port)

    # Write a single command
    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd)
        sleep(0.0001)

    # Write a command with an argument
    def write_cmd_arg(self, cmd, arg):
        self.bus.write_byte_data(self.addr, cmd, arg)
        sleep(0.0001)

    # Write a block of data (31 bytes max)
    def write_block_data(self, cmd, data):
        self.bus.write_block_data(self.addr, cmd, data)
        sleep(0.0001)

    # Read a single byte
    def read(self):
        return self.bus.read_byte(self.addr)

    # Read a single byte with command
    def read_data(self, cmd):
        return self.bus.read_byte_data(self.addr, cmd)

    # Read a block of data
    def read_block_data(self, cmd):
        return self.bus.read_block_data(self.addr, cmd)

# Commands
CLEAR_DISPLAY = 0x01
RETURN_HOME = 0x02
ENTRY_MODE_SET = 0x04
DISPLAY_CONTROL = 0x08
CURSOR_SHIFT = 0x10
FUNCTION_SET = 0x20
SET_CGRAM_ADDR = 0x40
SET_DDRAM_ADDR = 0x80

# Arguments for ENTRY_MODE_SET
ENTRY_RIGHT = 0x00
ENTRY_LEFT = 0x02
ENTRY_SHIFT_INC = 0x01
ENTRY_SHIFT_DEC = 0x00

# Arguments for DISPLAY_CONTROL
DISPLAY_ON = 0x04
DISPLAY_OFF = 0x00
CURSOR_ON = 0x02
CURSOR_OFF = 0x00
BLINK_ON = 0x01
BLINK_OFF = 0x00

# Arguments for CURSOR_SHIFT
DISPLAY_MOVE = 0x08
CURSOR_MOVE = 0x00
MOVE_RIGHT = 0x04
MOVE_LEFT = 0x00

# Arguments for FUNCTION_SET
MODE_8_BIT = 0x10
MODE_4_BIT = 0x00
MODE_2_LINE = 0x08
MODE_1_LINE = 0x00
MODE_5x10 = 0x04
MODE_5x8 = 0x00

# Arguments for backlight control
BACKLIGHT_ON = 0x08
BACKLIGHT_OFF = 0x00

# Enable bit
En = 0b00000100
# Read/write bit
Rw = 0b00000010
# Register select bit
Rs = 0b00000001

class I2C_44780:
    def __init__(self, addr = 0x27):
        self._lcd = I2CDevice(addr)
        self._backlight = BACKLIGHT_ON
        self._function_set = MODE_2_LINE | MODE_5x8 | MODE_4_BIT
        self._display_control = DISPLAY_ON | CURSOR_OFF | BLINK_OFF
        self._entry_mode_set = ENTRY_LEFT

        # reset expanderand turn backlight off (Bit 8 =1)
        #self._raw_write(self._backlight)

        # put the LCD into 4-bit mode
        self._write_4_bit(0x03 << 4)
        sleep(0.005)
        self._write_4_bit(0x03 << 4)
        sleep(0.005)
        self._write_4_bit(0x03 << 4)
        sleep(0.0005)
        self._write_4_bit(0x02 << 4)

        self.send_command(FUNCTION_SET | self._function_set)
        self.send_command(DISPLAY_CONTROL | self._display_control)
        self.send_command(CLEAR_DISPLAY)
        self.send_command(ENTRY_MODE_SET | self._entry_mode_set)
        sleep(0.2)

        # install umlaut chars
        self.create_char(5, cap_uml_a)
        self.create_char(6, cap_uml_o)
        self.create_char(7, cap_uml_u)


    def _raw_write(self, data):
        self._lcd.write_cmd(data | self._backlight)

    def _strobe(self, data):
        self._raw_write(data | En)
        sleep(0.0005)
        self._raw_write(data & ~En)
        sleep(0.0001)

    def _write_4_bit(self, data):
        self._raw_write(data)
        self._strobe(data)

    # write a command or data
    def _write(self, val, mode=0):
        self._write_4_bit(mode | (val & 0xf0))
        self._write_4_bit(mode | ((val << 4) & 0xf0))

    def send_command(self, cmd):
        self._write(cmd, 0)

    def send_data(self, data):
        self._write(data, Rs)

    def backlight(self, state):
        if state:
            self._backlight = BACKLIGHT_ON
            self._raw_write(0)
        else:
            self._backlight = BACKLIGHT_OFF
            self._raw_write(0)

    def clear(self):
        self.send_command(CLEAR_DISPLAY)
        sleep(0.002)
        self.home()

    def home(self):
        self.send_command(RETURN_HOME)
        sleep(0.002)

    def move_cursor(self, col, row):
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        self.send_command(SET_DDRAM_ADDR | (col + row_offsets[row]))

    def display(self, state):
        if state:
            self._display_control |= DISPLAY_ON
        else:
            self._display_control &= ~DISPLAY_ON
        self.send_command(DISPLAY_CONTROL | self._display_control)

    def cursor(self, state):
        if state:
            self._display_control |= CURSOR_ON
        else:
            self._display_control &= ~CURSOR_ON
        self.send_command(DISPLAY_CONTROL | self._display_control)

    def blink(self, state):
        if state:
            self._display_control |= BLINK_ON
        else:
            self._display_control &= ~BLINK_ON
        self.send_command(DISPLAY_CONTROL | self._display_control)

    def create_char(self, location, charmap):
        location &= 0x7
        self.send_command(SET_CGRAM_ADDR | (location << 3))
        for i in range(8):
            self.send_data(charmap[i])

    def write(self, string, line):
        line_offsets = [0x80, 0xC0, 0x94, 0xD4]
        self.send_command(line_offsets[line])

        # TODO: ugly umlaut hack
        tr_string = string.translate(_transtable)

        for char in tr_string:
            self.send_data(ord(char))

