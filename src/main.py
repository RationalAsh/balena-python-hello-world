#!/usr/bin/env python3

from ST7789 import ST7789, BG_SPI_CS_FRONT
from PIL import Image, ImageDraw

import random
import time
import os

# Buttons
BUTTON_A = 4
BUTTON_B = 7
BUTTON_X = 3
BUTTON_Y = 0

# Onboard RGB LED
LED_R = 17
LED_G = 27
LED_B = 22

# General
SPI_PORT = 0
SPI_CS = 0
SPI_DC = 6
BACKLIGHT = 5

# Screen dimensions
WIDTH = 240
HEIGHT = 320

buffer = Image.new("RGB", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(buffer)

draw.rectangle((0, 0, 50, 50), (255, 0, 0))
draw.rectangle((320-50, 0, 320, 50), (0, 255, 0))
draw.rectangle((0, 240-50, 50, 240), (0, 0, 255))
draw.rectangle((320-50, 240-50, 320, 240), (255, 255, 0))

display = ST7789(
    port=SPI_PORT,
    cs=SPI_CS,
    dc=SPI_DC,
    backlight=BACKLIGHT,
    width=WIDTH,
    height=HEIGHT,
    rotation=180,
    spi_speed_hz=60 * 1000 * 1000
)

while True:
    display.display(buffer)
    time.sleep(1.0 / 60)

# if __name__ == '__main__':
#     while True:
#         print([d for d in os.listdir('/dev') if 'spi' in d])
#         time.sleep(1.0)