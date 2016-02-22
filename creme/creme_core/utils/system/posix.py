# -*- coding: utf-8 -*-

# Code derived from https://github.com/millerdev/WorQ/blob/master/worq/pool/process.py

################################################################################
#
# Copyright (c) 2012 Daniel Miller
# Copyright (c) 2016 Hybird
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

from os import setpgrp
from subprocess import Popen
import signal
from sys import exit, version_info
from sys import executable as PYTHON_BIN


def enable_exit_handler(on_exit=lambda *args: exit()):
    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)


def disable_exit_handler():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def is_exit_handler_enabled():
    return signal.getsignal(signal.SIGINT) not in (signal.SIG_DFL, None) and \
           signal.getsignal(signal.SIGTERM) not in (signal.SIG_DFL, None)


def python_subprocess(script, python=PYTHON_BIN, start_new_session=False, **kwargs):
    # Hack that prevents signal propagation from parent process.
    # Useless in python 3 (use start_new_session instead)
    if version_info < (3, 2):
        kwargs.update(preexec_fn=setpgrp() if start_new_session else None)
    else:
        kwargs.update(start_new_session=start_new_session)

    return Popen([python, '-c', script], **kwargs)