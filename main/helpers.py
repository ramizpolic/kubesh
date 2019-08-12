import string
import random
import argparse
import sys

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def randomstr(len=8):
    """Generate a random string of lowercase letters and digits """
    text = string.ascii_lowercase + string.digits
    return ''.join(random.choice(text) for i in range(len))

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)