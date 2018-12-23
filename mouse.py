import struct, os

fd = open("/dev/input/mice", "rb")

location_x = 0
location_y = 0


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def get_mouse_event():
    buf = fd.read(3);
    x, y = struct.unpack("bb", buf[1:])
    return Point(x, y)


while True:
    update = get_mouse_event()
    location_x += update.x
    location_y += update.y
    print("%d, %d" % (location_x, location_y))

fd.close()
