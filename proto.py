
ping = 'ping'
pong = 'pong'
set_gain = 'set_gain'
set_gain_ok = 'set_gain_ok'
get_gain = 'get_gain'
gain = 'gain'
get_fix = 'get_fix'
fix = 'fix'
spec = 'spec'
spec_ok = 'spec_ok'
close = 'close'
connection_new = 'connection_new'
connection_reg = 'connection_reg'
connection_close = 'connection_close'
unknown = 'unknown'

class Command(object):
    def __init__(self, name='', args=[]):
        self.name = name
        self.args = args

class Spectrum(Command):
    def __init__(self):
        Command.__init__(self, 'spec', [])
        self.latitude_start = 0.0
        self.latitude_end = 0.0
        self.longitude_start = 0.0
        self.longitude_end = 0.0
        self.altitude_start = 0.0
        self.altitude_end = 0.0
        self.time_start = None
        self.time_end = None
        self.channel_count = 0
        self.channels = []
