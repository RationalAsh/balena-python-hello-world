#!/bin/sh

SWCLK=25
SWDIO=24
SRST=18

echo "Exporting SWCLK and SRST pins."
echo $SWCLK > /sys/class/gpio/export
echo $SRST > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio$SWCLK/direction
echo "out" > /sys/class/gpio/gpio$SRST/direction

echo "Setting SWCLK low and pulsing SRST."
echo "0" > /sys/class/gpio/gpio$SWCLK/value
echo "0" > /sys/class/gpio/gpio$SRST/value
echo "1" > /sys/class/gpio/gpio$SRST/value

echo "Unexporting SWCLK and SRST pins."
echo $SWCLK > /sys/class/gpio/unexport
echo $SRST > /sys/class/gpio/unexport

echo "Ready for OpenOCD."

openocd -c "adapter driver bcm2835gpio; \\
bcm2835gpio peripheral_base 0xFE000000; \\
bcm2835gpio speed_coeffs 236181 60; \\
adapter gpio swclk $SWCLK; \\
adapter gpio swdio $SWDIO; \\
adapter gpio srst $SRST; \\
adapter srst delay 100; \\
adapter srst pulse_width 100; \\
transport select swd; \\
set CHIPNAME stm32f446re; \\
source [find target/stm32f4x.cfg]; \\
reset_config srst_only srst_push_pull; \\
adapter speed 276; \\
init; \\
reset halt; \\
stm32f2x mass_erase 0; \\
flash write_image erase motor-controller.bin 0x08000000; \\
flash verify_image motor-controller.bin 0x08000000; \\
reset; \\
shutdown"

echo "Done."