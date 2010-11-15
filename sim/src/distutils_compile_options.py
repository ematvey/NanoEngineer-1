# Copyright 2006 Nanorex, Inc.  See LICENSE file for details. 
import sys
import re
import distutils.sysconfig
import distutils.ccompiler

class FakeCompiler:
    def __init__(self):
        self.compiler_type = distutils.ccompiler.get_default_compiler()
    def set_executables(self, **kw):
        for k in kw: setattr(self, k, kw[k])

mcc = FakeCompiler()
distutils.sysconfig.customize_compiler(mcc)

if len(sys.argv) < 2:
    import pprint
    pprint.pprint(mcc.__dict__)
else:
    for arg in sys.argv[1:]:
        cmd = getattr(mcc, arg)
        cmd = re.sub(r'(gcc|g\+\+)(-[0-9\.]+)? (.+)', r'\3', cmd)
        cmd = re.sub(r' -arch [a-z0-9_-]+', r'', cmd)
        #if cmd.startswith("gcc ") or cmd.startswith("g++ "):
        #    cmd = cmd[4:]
        print cmd
