import select
import time
import gamepad

def print_button(btn, pressed):
    print('{0} {1}'.format(btn.name, 'pressed' if pressed else 'released'))

def print_analog(analog, value):
    print('{0} {1}'.format(analog.name, value))

def main():
    with gamepad.GameSirG4s() as gamesir_g4s:
        dev = gamesir_g4s.get_dev()
        gamesir_g4s.register_button_cb(print_button)
        gamesir_g4s.register_analog_cb(print_analog)

        if dev is None:
            print('Failed to find device')
            return

        print('Using device {0}: {1} {2}'.format(dev.path, dev.name, dev.phys))
        print('Leds: {0}'.format(dev.leds(verbose=True)))
        print('Force feedback: {0}'.format(dev.ff_effects_count))
        print('Capabilities: \n{0}\n'.format(dev.capabilities(verbose=True)))
    
        #while True:
        #    x = dev.absinfo(evdev.ecodes.ABS_X)
        #    y = dev.absinfo(evdev.ecodes.ABS_Y)
        #    z = dev.absinfo(evdev.ecodes.ABS_Z)
        #    rz = dev.absinfo(evdev.ecodes.ABS_RZ)
        #    gas = dev.absinfo(evdev.ecodes.ABS_GAS)
        #    b = dev.absinfo(evdev.ecodes.ABS_BRAKE)
        #    hat0x = dev.absinfo(evdev.ecodes.ABS_HAT0X)
        #    hat0y = dev.absinfo(evdev.ecodes.ABS_HAT0Y)
        #    print('x: {0} y: {1} z: {2} rz: {3} gas: {4} break: {5} hat0x: {6} hat0y: {7}'.format(x.value, y.value, z.value, rz.value, gas.value, b.value, hat0x.value, hat0y.value))
        #    print('keys: {0}'.format(dev.active_keys(verbose=False)))
        #    time.sleep(0.1)
        
        #for event in dev.read_loop():
        #    print(event)
        
        while True:
            _, _, _ = select.select([ dev.fd ], [], [])
            gamesir_g4s.process()

main()
