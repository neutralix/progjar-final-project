class ServMsg:
    def __init__ (self, cmd, dest, msg):
        self.cmd = cmd
        self.dest = dest
        self.msg = msg

class CliMsg:
    def __init__ (self, dtype, msg):
        self.dtype = dtype
        self.msg = msg