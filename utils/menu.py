from functools import wraps

def as_menu(D, name, icon=None, shortcut=None, tip=None, checkable=False, signal=None, callback=None, enabled=True):

    def func(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        D.addMenu(name, icon, shortcut, tip, checkable, signal, callback, enabled, wrapper)
        return f
    return func