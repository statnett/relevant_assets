import datetime
import pickle

from enum import Enum
from decorator import decorator


def time_this(fn):
    """
    This decorator time the input function :func:`fn`
    """
    def timed_fn(fn, *args, **kwargs):
        time1 = datetime.datetime.now()
        result = fn(*args, **kwargs)
        calc_time = datetime.datetime.now() - time1
        print('%s execution time: %s.' % (fn.__name__, str(calc_time)))
        return result
    return decorator(timed_fn, fn)


class RaspEnum(Enum):
    def __str__(self):
        return self.value[1]

    def get_index(self):
        return self.value[0]

    @classmethod
    def get_enum(cls, index):
        e = [e.value for e in cls if e.value[0] == index][0]
        return cls.__new__(cls, e)

    @classmethod
    def enum_from_string(cls, index):
        e = [e.value for e in cls if e.value[1] == index][0]
        return cls.__new__(cls, e)

    @classmethod
    def enum_from_name_string(cls, name):
        e = [e.value for e in cls if e.name == name][0]
        return cls.__new__(cls, e)

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] >= other.value[0]
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] > other.value[0]
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] <= other.value[0]
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] < other.value[0]
        return NotImplemented


def write_to_pickle(file_name, data, file_path=r'c:\temp'):
    with open(file_path + '\\' + file_name, 'wb') as f:
        pickle.dump(data, f, protocol=2)


def read_data(file_name, file_path=r'c:\temp'):
    with open(file_path + '\\' + file_name, 'rb') as f:
        data = pickle.load(f)
    return data
