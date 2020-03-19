'''
Character definitions and utilities
'''

import math


# ordinals for characters
ORD_NUL = 0
ORD_BS = 8      # backspace = ^H
ORD_TAB = 9     # (horizontal) tab = ^I
ORD_LF = 10     # line feed = ^J
ORD_CR = 13     # carriage return = ^M
ORD_ESC = 27    # escape = ^[
ORD_DEL = 127   # delete = ^?

ORD_CTRL_A = 1
ORD_CTRL_B = 2
ORD_CTRL_C = 3
ORD_CTRL_D = 4
ORD_CTRL_E = 5
ORD_CTRL_F = 6
ORD_CTRL_G = 7
ORD_CTRL_H = 8
ORD_CTRL_I = 9
ORD_CTRL_J = 10
ORD_CTRL_K = 11
ORD_CTRL_L = 12
ORD_CTRL_M = 13
ORD_CTRL_N = 14
ORD_CTRL_O = 15
ORD_CTRL_P = 16
ORD_CTRL_Q = 17
ORD_CTRL_R = 18
ORD_CTRL_S = 19
ORD_CTRL_T = 20
ORD_CTRL_U = 21
ORD_CTRL_V = 22
ORD_CTRL_W = 23
ORD_CTRL_X = 24
ORD_CTRL_Y = 25
ORD_CTRL_Z = 26


# actual characters
NUL = chr(ORD_NUL)
BS = chr(ORD_BS)      # backspace = ^H
TAB = chr(ORD_TAB)    # (horizontal) tab = ^I
LF = chr(ORD_LF)      # line feed = ^J
CR = chr(ORD_CR)      # carriage return = ^M
ENTER = CR
ESC = chr(ORD_ESC)    # escape = ^[
DEL = chr(ORD_DEL)    # delete = ^?

CTRL_A = chr(ORD_CTRL_A)
CTRL_B = chr(ORD_CTRL_B)
CTRL_C = chr(ORD_CTRL_C)
CTRL_D = chr(ORD_CTRL_D)
CTRL_E = chr(ORD_CTRL_E)
CTRL_F = chr(ORD_CTRL_F)
CTRL_G = chr(ORD_CTRL_G)
CTRL_H = chr(ORD_CTRL_H)
CTRL_I = chr(ORD_CTRL_I)
CTRL_J = chr(ORD_CTRL_J)
CTRL_K = chr(ORD_CTRL_K)
CTRL_L = chr(ORD_CTRL_L)
CTRL_M = chr(ORD_CTRL_M)
CTRL_N = chr(ORD_CTRL_N)
CTRL_O = chr(ORD_CTRL_O)
CTRL_P = chr(ORD_CTRL_P)
CTRL_Q = chr(ORD_CTRL_Q)
CTRL_R = chr(ORD_CTRL_R)
CTRL_S = chr(ORD_CTRL_S)
CTRL_T = chr(ORD_CTRL_T)
CTRL_U = chr(ORD_CTRL_U)
CTRL_V = chr(ORD_CTRL_V)
CTRL_W = chr(ORD_CTRL_W)
CTRL_X = chr(ORD_CTRL_X)
CTRL_Y = chr(ORD_CTRL_Y)
CTRL_Z = chr(ORD_CTRL_Z)


def make_printable(string, max_line_len = None):
    """ Replace non-printable characters with codes """
    result = ''
    for ch in string:
        if ch < ' ':
            if ch == '\t':
                result += '\\t'
            elif ch == '\n':
                result += '\\n'
            elif ch == '\r':
                result += '\\r'
            else:
                result += '^' + chr(ord(ch)+ord('@'))
        elif ch < DEL:
            result += ch
        elif ch == DEL:
            result += 'DEL'
        else:
            o = ord(ch)
            result += "\\x%0.2x" % o
    
    if max_line_len is not None and max_line_len > 0:
        num_chars = len(result)
        if num_chars > max_line_len:
            num_lines = math.ceil(num_chars / max_line_len)
            temp = result
            result = ''
            for i in range(num_lines):
                if i > 0:
                    result += '\n'
                result += temp[i*max_line_len : (i+1)*max_line_len]

    return result


# Unit tests
if __name__ == '__main__':
    a = '123456789\x01\x02\x03\x04\x05\x06\x07\x08\x09' + ESC
    print(make_printable(a))
    print(make_printable(a, 10))


