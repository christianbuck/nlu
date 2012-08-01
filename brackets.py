

def escape_brackets(s):
    s = s.replace('(', '-LRB-')
    s = s.replace(')', '-RRB-')
    s = s.replace('[', '-LSB-')
    s = s.replace(']', '-RSB-')
    s = s.replace('{', '-LCB-')
    s = s.replace('}', '-RCB-')
    return s

def unescape_brackets(s):
    s = s.replace('-LRB-','(')
    s = s.replace('-RRB-',')')
    s = s.replace('-LSB-','[')
    s = s.replace('-RSB-',']')
    s = s.replace('-LCB-','{')
    s = s.replace('-RCB-','}')
    return s
