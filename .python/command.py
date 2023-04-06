# Adapted from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch06s07.html
# Changes by Ariel Nunez <ingenieroariel>
import os, subprocess, fcntl, select, sys

def makeNonBlocking(fd):
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    try:
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    except AttributeError:
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NDELAY)

def call(command, stream_output=False):
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    outfd = child.stdout.fileno()
    errfd = child.stderr.fileno()
    makeNonBlocking(outfd)
    makeNonBlocking(errfd)
    outdata = errdata = ''
    outeof = erreof = 0
    while 1:
        ready = select.select([outfd, errfd], [], [])
        if outfd in ready[0]:
            outchunk = child.stdout.read().decode('ascii', errors='ignore')
            if outchunk == '':
                outeof = 1
            if stream_output:
                sys.stdout.write(outchunk)
                sys.stdout.flush()
            outdata = outdata + outchunk
        if errfd in ready[0]:
            errchunk = child.stderr.read().decode('ascii', errors='ignore')
            if errchunk == '':
                erreof = 1
            errdata = errdata + errchunk
        if outeof and erreof:
            break
        select.select([], [], [], .1)
    err = child.wait()
    if err != 0:
        raise RuntimeError(f'{command} failed with exit code {err}\n{errdata}')
    return outdata

def getCommandOutput2(command):
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    data, errdata = child.communicate()
    err = child.returncode
    if err:
        raise RuntimeError(f'{command} failed with exit code {err}')
    return data

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        call(command, stream_output=True)
    else:
        print("Usage: python example.py <command>")