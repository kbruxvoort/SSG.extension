class Color:
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            # hexcode constructor
            hexcode = args[0].lstrip('#').upper()
            self.rgb = self._hex_to_rgb(hexcode)
            self.int_value = self._rgb_to_int(self.rgb)
            self.hexcode = '#' + hexcode
        elif len(args) == 1 and isinstance(args[0], int):
            # int constructor
            self.int_value = args[0]
            self.rgb = self._int_to_rgb(self.int_value)
            self.hexcode = self._rgb_to_hex(self.rgb)
        elif len(args) == 3 and all(isinstance(arg, int) for arg in args):
            # RGB constructor
            self.rgb = args
            self.int_value = self._rgb_to_int(self.rgb)
            self.hexcode = self._rgb_to_hex(self.rgb)
        else:
            raise ValueError('Invalid arguments for color constructor')
    
    def get_rgb(self):
        return self.rgb
    
    def get_int_value(self):
        return self.int_value
    
    def get_hexcode(self):
        return self.hexcode
    
    def _int_to_rgb(self, int_value):
        return ((int_value >> 16) & 0xff, (int_value >> 8) & 0xff, int_value & 0xff)
    
    def _rgb_to_int(self, rgb):
        return rgb[0] + rgb[1] * 256 + rgb[2] * 256 * 256
    
    def _rgb_to_hex(self, rgb):
        return '#' + '%02x%02x%02x'.upper() % rgb
    
    def _hex_to_rgb(self, hexcode):
        return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))
