from functools import wraps
def singleton(cls):
    _instance = {}
    
    @wraps(cls)
    def inner(*args, **kargs):
        
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
            cls.instance = _instance[cls]
        return _instance[cls]
    return inner