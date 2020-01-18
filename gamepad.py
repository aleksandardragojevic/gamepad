import evdev
import enum
import select

class Buttons(enum.Enum):
    ARROW_LEFT = enum.auto()
    ARROW_RIGHT = enum.auto()
    ARROW_UP = enum.auto()
    ARROW_DOWN = enum.auto()
    FACE_LEFT = enum.auto()
    FACE_RIGHT = enum.auto()
    FACE_UP = enum.auto()
    FACE_BOTTOM = enum.auto()
    SHOULDER_LEFT_TOP = enum.auto()
    SHOULDER_LEFT_BOTTOM = enum.auto()
    SHOULDER_RIGHT_TOP = enum.auto()
    SHOULDER_RIGHT_BOTTOM = enum.auto()
    STICK_LEFT = enum.auto()
    STICK_RIGHT = enum.auto()
    SELECT = enum.auto()
    START = enum.auto()

class Analog(enum.Enum):
    STICK_LEFT_X = enum.auto()
    STICK_LEFT_Y = enum.auto()
    STICK_RIGHT_X = enum.auto()
    STICK_RIGHT_Y = enum.auto()
    SHOULDER_LEFT = enum.auto()
    SHOULDER_RIGHT = enum.auto()

class ButtonState:
    def __init__(self, button):
        self.button = button
        self.pressed = False
        self.changed = False

class AnalogState:
    def __init__(self, analog):
        self.analog = analog
        self.val = 0
        self.changed = False

class GameSirG4s:
    __DEV_NAME = 'Gamesir-G4s'
    __EXPECTED_ABS_COUNT = 8
    
    def __init__(self):
        self.__dev = None
        self.__button_table = { k : ButtonState(k) for k in Buttons }
        self.__analog_table = { k : AnalogState(k) for k in Analog }
        # pure analog
        self.__analog_mapping = {
            evdev.ecodes.ABS_X : Analog.STICK_LEFT_X,
            evdev.ecodes.ABS_Y : Analog.STICK_LEFT_Y,
            evdev.ecodes.ABS_Z : Analog.STICK_RIGHT_X,
            evdev.ecodes.ABS_RZ : Analog.STICK_RIGHT_Y,
            evdev.ecodes.ABS_BRAKE : Analog.SHOULDER_LEFT,
            evdev.ecodes.ABS_GAS : Analog.SHOULDER_RIGHT
        }
        # pure buttons
        self.__button_mapping = {
            evdev.ecodes.BTN_X : Buttons.FACE_LEFT,
            evdev.ecodes.BTN_B : Buttons.FACE_RIGHT,
            evdev.ecodes.BTN_Y : Buttons.FACE_UP,
            evdev.ecodes.BTN_A : Buttons.FACE_BOTTOM,
            evdev.ecodes.BTN_TL2 : Buttons.SHOULDER_LEFT_BOTTOM,
            evdev.ecodes.BTN_TL : Buttons.SHOULDER_LEFT_TOP,
            evdev.ecodes.BTN_TR2 : Buttons.SHOULDER_RIGHT_BOTTOM,
            evdev.ecodes.BTN_TR : Buttons.SHOULDER_RIGHT_TOP,
            evdev.ecodes.BTN_THUMBL : Buttons.STICK_LEFT,
            evdev.ecodes.BTN_THUMBR : Buttons.STICK_RIGHT,
            evdev.ecodes.BTN_SELECT : Buttons.SELECT,
            evdev.ecodes.BTN_START : Buttons.START
        }
        # analogs that are buttons
        self.__analog_buttons_mapping = {
            evdev.ecodes.ABS_HAT0X : (Buttons.ARROW_LEFT, Buttons.ARROW_RIGHT),
            evdev.ecodes.ABS_HAT0Y : (Buttons.ARROW_UP, Buttons.ARROW_DOWN)
        }
        # user callbacks
        self.__button_cb = None
        self.__analog_cb = None
        
    def open(self):
        all_dev = [evdev.device.InputDevice(p) for p in evdev.util.list_devices()]
        
        for d in all_dev:
            if self.__check_dev(d):
                self.__dev = d
                self.__read_init_state()
            else:
                d.close()
    
    def __read_init_state(self):
        for btn_key in self.__dev.active_keys():
            self.__process_key(True, btn_key)

        for ev_code, analog in self.__analog_mapping.items():
            abs_info = self.__dev.absinfo(ev_code)
            self.__process_analog(abs_info.value, analog)

        for ev_code, analog in self.__analog_buttons_mapping.items():
            abs_info = self.__dev.absinfo(ev_code)
            self.__process_analog_button(ev_code, abs_info.value, analog)

    def close(self):
        if self.__dev is not None:
            self.__dev.close()
            self.__dev = None
            
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_ts):
        self.close()
                
    def __check_dev(self, d):
        if d.name.find(GameSirG4s.__DEV_NAME) == -1:
            print('Not using {0}'.format(d.name))
            return False
        
        cap = d.capabilities()
        
        if evdev.ecodes.EV_ABS not in cap:
            print('Not using {0} as there are no EV_ABS'.format(d.name))
            return False
        
        if len(cap[evdev.ecodes.EV_ABS]) != GameSirG4s.__EXPECTED_ABS_COUNT:
            print('Not using {0} as there are not enough EV_ABS {1}'.format(d.name, len(cap[evdev.ecodes.EV_ABS])))
            return False
        
        return True
    
    def get_dev(self):
        return self.__dev

    def process(self):
        for e in self.__dev.read():
            self.__process_one(e)

    def wait_for_event(self, **kwargs):
        t = kwargs.get('timeout', None)

        if t is None:
            r, _, _ = select.select([ self.__dev.fd ], [], [])
        else:
            r, _, _ = select.select([ self.__dev.fd ], [], [], t)
        
        if len(r) == 1:
            self.process()

    def __process_one(self, ev):
        if ev.type == evdev.ecodes.EV_KEY:
            self.__process_key(ev.code, ev.value == 1)
        elif ev.type == evdev.ecodes.EV_ABS:
            self.__process_abs(ev.code, ev.value)

    def __process_key(self, ev_code, pressed):
        button = self.__button_mapping.get(ev_code, None)

        if button is None:
            print('Failed to map key {0}', evdev.util.resolve_ecodes(evdev.ecodes.ecodes, [ev_code])[0])
        else:
            state = self.__button_table[button]
            self.__process_button(pressed, state)
    
    def __process_button(self, pressed, state):
        state.pressed = pressed
        state.changed = True

        if self.__button_cb is not None:
            self.__button_cb(state.button, pressed)

    def __process_abs(self, ev_code, value):
        buttons = self.__analog_buttons_mapping.get(ev_code, None)

        if buttons is not None:
            self.__process_analog_button(ev_code, value, buttons)
        else:
            analog = self.__analog_mapping.get(ev_code, None)

            if analog is None:
                print('Failed to map analog {0}', evdev.util.resolve_ecodes(evdev.ecodes.ecodes, [ev_code])[0])
            else:
                self.__process_analog(value, analog)

    def __process_analog_button(self, ev_code, value, buttons):
        button_0 = self.__button_table[buttons[0]]
        button_1 = self.__button_table[buttons[1]]

        # value == -1 means the first button was pressed, value == 1 the second
        if value == -1:
            if not button_0.pressed:
                self.__process_button(True, button_0)
            if button_1.pressed:
                self.__process_button(False, button_1)
        elif value == 0:
            if button_0.pressed:
                self.__process_button(False, button_0)
            if button_1.pressed:
                self.__process_button(False, button_1)
        elif value == 1:
            if button_0.pressed:
                self.__process_button(False, button_0)
            if not button_1.pressed:
                self.__process_button(True, button_1)
        else:
            print('Unexpected value {0} for analog button {1}', value, evdev.util.resolve_ecodes(evdev.ecodes.ecodes, [ev_code])[0])

    def __process_analog(self, value, analog):
        state = self.__analog_table[analog]

        state.value = value
        state.changed = True

        if self.__analog_cb is not None:
            self.__analog_cb(analog, value)

    def get_analog_value(self, analog):
        return self.__analog_table[analog].value

    def is_pressed(self, button):
        return self.__button_table[button].pressed
    
    def has_just_been_pressed(self, button):
        state = self.__button_table[button]
        ret = state.pressed and state.changed
        state.changed = False
        return ret
    
    def register_button_cb(self, cb):
        self.__button_cb = cb

    def deregister_button_cb(self):
        self.__button_cb = None

    def register_analog_cb(self, cb):
        self.__analog_cb = cb

    def deregister_analog_cb(self):
        self.__analog_cb = None
