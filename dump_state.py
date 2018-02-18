import gdb
import re
import os.path

class CommandDumpState(gdb.Command):
    """
    This command should save off all memory segments including mapped in libraries, and all registers.
    Dealing with threads would be too painful and pointless, so only care about the current context.

    optional arguments:
        base_dir: directory to place memory dumps in, default is ./
    """

    def __init__(self):
        gdb.Command.__init__(self, 'dumpstate', gdb.COMMAND_DATA)

    def _get_proc_mappings(self):
        addr_list = list()
        raw_map_text = gdb.execute('info proc mappings', to_string=True)
        useful_map_text = re.search('Start Addr\s*End Addr\s*Size\s*Offset\s*objfile\s*\n([\s\S]*)', raw_map_text)
        if useful_map_text:
            for line in useful_map_text.group(1).split('\n'):
                info = re.search('^\s*([0-9a-fA-Fx]+)\s*([0-9a-fA-Fx]+)\s*([0-9a-fA-Fx]+)\s*([0-9a-fA-Fx]+)\s*(.*)$', line)
                if info and len(info.groups()) == 5:
                    addr_list.append(self.addr_entry(info.group(1), # start addr
                                                        info.group(2), # end addr
                                                        info.group(3), # size
                                                        info.group(4), # offset
                                                        info.group(5))) # objfile

        return addr_list

    def _dump_addr_list(self, addr_list, base_dir):
        for entry in addr_list:
            outname = os.path.join(base_dir, entry.start)
            gdb.execute('dump binary memory {} {} {}'.format(outname, entry.start, entry.end))

    def invoke(self, arg, from_tty):
        args = arg.split(' ')
        if len(args) == 1:
            # Valid single argument or no argument
            if args[0] ne '':
                base_dir = args[0]
            else:
                base_dir = './'
        elif len(args) > 1:
            # Invalid invocation
            print('Invalid number of arguments. Usage: dumpstate [optional base_dir]')
            return

        if not os.path.isdir(base_dir):
            print('Invalid target directory, directory does not exist')
            return

        addr_list = self._get_proc_mappings()
        self._dump_addr_list(addr_list, base_dir)
        return

    class addr_entry():
        start = ""
        end = ""
        size = ""
        offset = ""
        objfile = ""

        def __init__(self, start, end, size, offset, objfile):
            self.start = start
            self.end = end
            self.size = size
            self.offset = offset
            self.objfile = objfile

CommandDumpState()

