import re
import sys
import struct
from inspect import getargspec


class VirtualMachine():

    NUM_REGISTERS = 8
    MOD = 32768
    CHALLENGE_FILENAME = "challenge.bin"
    WALKTHROUGH_FILENAME = "walkthrough.txt"
    LOG_FILENAME = "log.txt"
    DUMP_FILENAME = "opcode_dump.txt"

    OPCODES = ("halt", "set", "push", "pop", "eq", "gt", "jmp", "jt", "jf", "add",
               "mult", "mod", "and", "or", "not", "rmem", "wmem", "call", "ret",
               "out", "in", "noop")

    def __init__(self):
        """
        initialize memory storage and index, read input file/program into memory
        """
        self.walkthrough_index = 0
        self.use_walkthrough = False
        self.logging_enabled = False
        self.input_buffer = ""
        self.memory_index = 0
        self.stack = []
        self.register = [0]*self.NUM_REGISTERS
        self.memory = self.read_program(self.CHALLENGE_FILENAME)
        self.walkthrough_steps = self.read_walkthrough(self.WALKTHROUGH_FILENAME)
        self.dump_program(self.DUMP_FILENAME)


    #====================virtual machine run/terminate code=====================


    def get_opcode_func_and_args(self):
        """
        At the current memory index, retrieves the current opcode ID, opcode, and corresponding
        func and args, all while incrementing the memory index for each read
        """
        assert self.memory_index < len(self.memory)

        opcode_id = self.memory[self.memory_index]

        try:
            opcode = self.OPCODES[opcode_id] #read opcode
        except:
            opcode = "unknown"

        func = getattr(self, "op_{}".format(opcode))
        num_args = len(getargspec(func).args)-1 #num. of args from func(), -1 (for self)
        args = []
        for arg_i in xrange(num_args):
            self.memory_index+=1 #next argument
            args.append(self.memory[self.memory_index])
        self.memory_index+=1 #increase index to next opcode
        return opcode_id, opcode, func, args


    def run(self):
        """
        Runs the virtual machine
        """
        self.memory_index = 0

        while self.memory_index < len(self.memory):
            opcode_id, opcode, func, args = self.get_opcode_func_and_args()

            if self.walkthrough_index >= len(self.walkthrough_steps):
                self.use_walkthrough = False

            if self.logging_enabled:
                self.log_state(opcode, args)

            func(*args) #run the function with the relevant args passed in
            #note that self.memory_index may change if a jmp is performed

        self.terminate()


    def terminate(self):
        """
        Close log, terminate virtual machine
        """
        if self.logging_enabled: self.toggle_logging()
        sys.exit()


    #======================getters, setters, correctors=========================


    def resolve_value(self, a):
        """
        Returns the correct value based on which range it falls into.
        Numbers 0..32767 mean a literal value
        Numbers 32768..32775 instead mean registers 0..7
        Numbers 32776..65535 are invalid
        """
        if 0 <= a < self.MOD:
            return a
        elif self.MOD <= a < self.MOD + self.NUM_REGISTERS:
            return self.get_register(a)
        else:
            raise IndexError("literal <a> = {} must be between 0 <= a <= {}.".format(a, self.MOD + self.NUM_REGISTERS - 1))


    def get_register(self, a):
        """
        Retrieve value from register[a % MOD]
        """
        assert self.MOD <= a < self.MOD + self.NUM_REGISTERS
        return self.register[a % self.MOD]


    def set_register(self, a, b):
        """
        Set register[a % MOD] to value b
        """
        assert self.MOD <= a < self.MOD + self.NUM_REGISTERS
        self.register[a % self.MOD] = b


    def get_memory(self, a):
        """
        Read value at memory[a]
        """
        assert a < len(self.memory)
        return self.memory[a]


    def set_memory(self, a, b):
        """
        Set memory[a] to value b
        """
        assert a < len(self.memory)
        self.memory[a] = b


    #===================bulk data read / write procedures=======================


    def read_program(self, infile):
        """
        Read the program from the input file into the memory buffer
        """
        memory = []
        try:
            f = open(infile,"rb")
            chunk = f.read(2)
            while chunk != '':
                memory.append(int(struct.unpack('<H', chunk)[0]))
                chunk = f.read(2)
            f.close()
        except:
            raise IOError("File {} not found.".format(infile))
        return memory


    def read_walkthrough(self,walkthrough_filename):
        """
        Read the walkthrough steps from file into list
        """
        steps = []
        try:
            for line in open(walkthrough_filename,"r"):
                steps.append(line.strip())
        except:
            raise IOError("File {} not found.".format(walkthrough_filename))
        return steps


    def dump_program(self, dump_filename):
        """
        Dumps the program's opcodes and arguments to a file.
        """
        self.memory_index = 0
        f = open(dump_filename, "w")
        memory_start = 0
        memory_end = 0
        unknowns = []

        while self.memory_index < len(self.memory):
            opcode_id, opcode, func, args = self.get_opcode_func_and_args()
            memory_end = memory_start + len(args)
            line = (memory_start, memory_end, opcode_id, opcode, self.format_args(args))
            f.writelines("memory indices {}-{} : opid {} ({}): args {}\n".format(*line))
            memory_start = memory_end + 1
        self.memory_index = 0
        f.close()


    def log_state(self, opcode, args):
        """
        Logs the current state of the virtual machine
        (registers, stack, arguments, and memory index)
        """
        log_cur_index = self.memory_index - len(args)-1
        self.log_file.write("registers: {} \n".format(str(self.register)))
        self.log_file.write("stack (last 5): ...{}\n".format(str(self.stack[-5:])))
        self.log_file.write("opcode: {}, args: {}\n".format(opcode, self.format_args(args)))
        self.log_file.write("current index: {}\n\n".format(log_cur_index))


    #===========================support functions==============================


    def format_args(self,args):
        """
        Replaces memory index literals with Register IDs when writing args,
        for clarity (e.g. when writing to the log, the opcode dump file, etc)
        """
        new_args = []
        for arg in args:
            if self.MOD <= int(arg) < self.MOD + self.NUM_REGISTERS:
                new_args.append("Register {}".format(int(arg) % self.MOD))
            else:
                new_args.append(int(arg))
        return str(new_args)


    def toggle_logging(self):
        """
        Activates logging if currently inactive, and vice-versa
        """
        if self.logging_enabled == False:
            print "Logging started."
            self.logging_enabled = True
            self.log_file = open(self.LOG_FILENAME,"w")
        else:
            print "Logging stopped."
            self.logging_enabled = False
            self.log_file.close()


    def hack_teleporter(self):
        """
        Solves the teleporter puzzle by hard-coding the correct output of the Ackermann
        procedure into the registers while bypassing the procedure itself.
        See notes.txt for more details.
        """
        self.set_memory(6027,1)             #entry point for the modified Ackermann function
        self.set_memory(6028,self.MOD+0)
        self.set_memory(6029,6)
        self.set_memory(6030,18)            #early return
        self.set_register(self.MOD+7,25734) #A(4,1,25734) = 6 mod 2^15

        print "Teleporter hacked. It will now redirect you correctly."


    def custom_input(self):
        """
        Checks to see if any custom commands were entered by the user.
        If so, perform the custom action and return True so the input buffer can be cleared.
        Otherwise it will return False and the user's input will be processed normally.
        """

        if "log" in self.input_buffer.strip():
            self.toggle_logging()
            return True

        if self.input_buffer.strip() == "quit":
            self.terminate()
            return True

        if self.input_buffer.strip() == "use walkthrough":
            self.use_walkthrough = True
            return True

        if self.input_buffer.strip() == "hack teleporter":
            self.hack_teleporter()
            return True

        return False


    #======================opcode commands / functions==========================


    def op_halt(self):
        """
        halt: 0 (stop execution and terminate the program)
        """
        self.terminate()


    def op_set(self, a, b):
        """
        set: 1 a b (set register <a> to the value of <b>)
        """
        self.set_register(a, self.resolve_value(b))


    def op_push(self, a):
        """
        push: 2 a (push <a> onto the stack)
        """
        self.stack.append(self.resolve_value(a))


    def op_pop(self, a):
        """
        pop: 3 a (remove the top element from the stack and write it into <a>; empty stack = error)
        """
        if len(self.stack)==0:
            raise Exception("Cannot pop from an empty stack during op_pop()")
        else:
            top_element = self.stack.pop()
            self.set_register(a, top_element)


    def op_eq(self, a ,b, c):
        """
        eq: 4 a b c (set <a> to 1 if <b> is equal to <c>; set it to 0 otherwise)
        """
        self.set_register(a, int(self.resolve_value(b) == self.resolve_value(c)))


    def op_gt(self, a, b, c):
        """
        gt: 5 a b c (set <a> to 1 if <b> is greater than <c>; set it to 0 otherwise)
        """
        self.set_register(a, int(self.resolve_value(b) > self.resolve_value(c)))


    def op_jmp(self, a):
        """
        jmp: 6 a (jump to <a>)
        """
        assert a < len(self.memory)
        self.memory_index = a


    def op_jt(self, a, b):
        """
        jt: 7 a b (if <a> is nonzero, jump to <b>)
        """
        if self.resolve_value(a) != 0:
            self.op_jmp(b)


    def op_jf(self, a, b):
        """
        jf: 8 a b (if <a> is zero, jump to <b>)
        """
        if self.resolve_value(a) == 0:
            self.op_jmp(b)


    def op_add(self, a, b, c):
        """
        add: 9 a b c (assign into <a> the sum of <b> and <c> (modulo 32768))
        """
        self.set_register(a, (self.resolve_value(b) + self.resolve_value(c)) % self.MOD)


    def op_mult(self, a, b, c):
        """
        mult: 10 a b c (store into <a> the product of <b> and <c> (modulo 32768))
        """
        self.set_register(a, (self.resolve_value(b) * self.resolve_value(c)) % self.MOD)


    def op_mod(self, a, b, c):
        """
        mod: 11 a b c (store into <a> the remainder of <b> divided by <c>)
        """
        self.set_register(a, self.resolve_value(b) % self.resolve_value(c))


    def op_and(self, a, b, c):
        """
        and: 12 a b c (stores into <a> the bitwise and of <b> and <c>)
        """
        self.set_register(a, self.resolve_value(b) & self.resolve_value(c))


    def op_or(self, a, b, c):
        """
        or: 13 a b c (stores into <a> the bitwise or of <b> and <c>)
        """
        self.set_register(a, self.resolve_value(b) | self.resolve_value(c))


    def op_not(self, a, b):
        """
        not: 14 a b (stores 15-bit bitwise inverse of <b> in <a>)
        """
        self.set_register(a, (self.MOD - 1) - self.resolve_value(b))


    def op_rmem(self, a, b):
        """
        rmem: 15 a b (read memory at address <b> and write it to <a>)
        """
        self.set_register(a, self.get_memory(self.resolve_value(b)))


    def op_wmem(self, a, b):
        """
        wmem: 16 a b (write the value from <b> into memory at address <a>)
        """
        self.set_memory(self.resolve_value(a), self.resolve_value(b))


    def op_call(self, a):
        """
        call: 17 a (write the address of the next instruction to the stack and jump to <a>)
        """
        self.stack.append(self.memory_index)
        self.op_jmp(self.resolve_value(a))


    def op_ret(self):
        """
        ret: 18 (remove the top element from the stack and jump to it; empty stack = halt)
        """
        if len(self.stack)==0:
            self.op_halt()
        else:
            top_element = self.stack.pop()
            self.op_jmp(top_element)


    def op_out(self, a):
        """
        out: 19 a (write the character represented by ascii code <a> to the terminal)
        """
        sys.stdout.write(chr(self.resolve_value(a)))


    def op_in(self, a):
        """
        in: 20 a (read a character from the terminal and write its ascii code to <a>;
        it can be assumed that once input starts, it will continue until a newline is
        encountered; this means that you can safely read whole lines from the keyboard
        and trust that they will be fully read.
        """

        if self.input_buffer == "":
            if self.use_walkthrough == True:
                self.input_buffer = self.walkthrough_steps[self.walkthrough_index].lower().strip() + "\n"
                self.walkthrough_index+=1
            else:
                self.input_buffer = raw_input().lower().strip() + "\n"

            if self.custom_input():
                self.input_buffer == ""
                return

        self.set_register(a, ord(self.input_buffer[0]))
        self.input_buffer = self.input_buffer[1:]


    def op_noop(self):
        """
        noop: 21 (no operation)
        """
        pass


    def op_unknown(self):
        """
        unknown opcode, in the event of error
        """
        pass


def main():
    virtual_machine = VirtualMachine()
    virtual_machine.run()


if __name__ == "__main__":
    main()
