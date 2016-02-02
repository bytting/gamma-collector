import os, fcntl

def setblocking(fd, state):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    if state:
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
    else:
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

