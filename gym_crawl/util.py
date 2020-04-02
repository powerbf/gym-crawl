'''
Utility functions
'''

def make_list(arg):
    '''Make arg into a list if it isn't already'''
    if arg is None:
        return []
    elif isinstance(arg, list):
        return arg
    else:
        return [arg]