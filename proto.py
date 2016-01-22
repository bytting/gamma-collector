
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

class Message(object):
    def __init__(self, command='', arguments={}):
        self.command = command
        self.arguments = arguments
