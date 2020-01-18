from sense_hat import SenseHat
from time import sleep, perf_counter_ns
from gamepad import GameSirG4s, Buttons
import json
import sys

DEFAULT_FN = 'image.json'

sense = SenseHat()
sense.set_rotation(270)

# Define some colours
w = (150, 150, 150) # White
b = (0, 0, 255) # Blue
g = (0, 255, 0) # Green
r = (255, 0, 0) # Green
e = (0, 0, 0) # Black
pe = (255, 200, 150) # Peach
nd = (0x4B, 0x00, 0x82) #indigo
pu =(0xA0, 0x20, 0xF0)# Purple

colours = [ w, b, g, r, e, pe, nd, pu ]

HEIGHT = 8
WIDTH = 8

image = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
]

def set_pixel(x, y, c):
    image[y * WIDTH + x] = c
    sense.set_pixel(x, y, c)

def get_pixel(x, y):
    return image[y * WIDTH + x]

def print_button(btn, pressed):
    print('{0} {1}'.format(btn.name, 'pressed' if pressed else 'released'))

def print_analog(analog, value):
    print('{0} {1}'.format(analog.name, value))

def main():
    if len(sys.argv) >= 2:
        print('Loading image from file {0}'.format(sys.argv[1]))
        global image
        image = read_from_file(sys.argv[1])
    
    try:
        with GameSirG4s() as gamesir_g4s:
            dev = gamesir_g4s.get_dev()
            gamesir_g4s.register_button_cb(print_button)
            gamesir_g4s.register_analog_cb(print_analog)

            if dev is None:
                print('Failed to find device')
            else:
                main_loop(gamesir_g4s)
    except KeyboardInterrupt:
        print('Exiting...')
        
def write_to_file(fn=DEFAULT_FN):
    with open(fn, 'w') as f:
        json.dump(image, f)
        
def read_from_file(fn=DEFAULT_FN):
    with open(fn, 'r') as f:
        return json.load(f)

def main_loop(gpad, update_delay_ms=200):
    x = 0
    y = 0
    new_x = x
    new_y = y
    old_c = image[0]
    old_clr_idx = 0
    clr_idx = 0
    clr = colours[clr_idx]

    sense.set_pixels(image)
    set_pixel(x, y, clr)

    last_change = perf_counter_ns()

    while True:
        gpad.wait_for_event(timeout=0)

        if x == new_x:
            if gpad.is_pressed(Buttons.ARROW_RIGHT):
                new_x = 0 if x == WIDTH - 1 else x + 1
            elif gpad.is_pressed(Buttons.ARROW_LEFT):
                new_x = WIDTH - 1 if x == 0 else x - 1       

        if y == new_y:
            if gpad.is_pressed(Buttons.ARROW_DOWN):
                new_y = 0 if y == HEIGHT - 1 else y + 1
            elif gpad.is_pressed(Buttons.ARROW_UP):
                new_y = HEIGHT - 1 if y == 0 else y - 1       

        if old_clr_idx == clr_idx:
            if gpad.has_just_been_pressed(Buttons.FACE_LEFT):
                clr_idx = 0 if clr_idx == len(colours) - 1 else clr_idx + 1
                clr = colours[clr_idx]

        if gpad.has_just_been_pressed(Buttons.FACE_RIGHT):
            x = 0
            y = 0
            new_x = x
            new_y = y
            old_c = image[0]
            set_pixel(x, y, clr)
            
        if gpad.has_just_been_pressed(Buttons.SHOULDER_LEFT_TOP):
            write_to_file()

        now = perf_counter_ns()

        if now - last_change > update_delay_ms * 1000000:
            last_change = now

            if old_clr_idx != clr_idx:
                set_pixel(x, y, clr)
                old_clr_idx = clr_idx

            if x != new_x or y != new_y:
                set_pixel(x, y, old_c)

                x = new_x
                y = new_y
                old_c = get_pixel(x, y)

                set_pixel(x, y, clr)
            
            sleep(0.1)

main()
