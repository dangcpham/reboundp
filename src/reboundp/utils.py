from typing import List

def dim(x)->List[int]:
    """ Return the dimension of a list of lists. 
        From https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable

        Parameters
        ----------
        x : list
            List to check

        Returns
        -------
        dim : list
            Dimension of list
    """
    if not type(x) == list:
        return []
    return [len(x)] + dim(x[0])

def is_list(x)->bool:
    """ Check if object is a list, tuple, or numpy array.

        Parameters
        ----------
        x : object
            Object to check

        Returns
        -------
        is_list : bool
            True if object is a list, tuple, or numpy array. False otherwise.
    """
    if type(x) in [dict, tuple, str, int, float, bool]:
        return False
    else:
        try:
            iter(x)
            return True
        except TypeError:
            return False

def time_format(seconds: float) -> str:
    """ Convert seconds to human readable format.

        Parameters
        ----------
        seconds : float
            Time in seconds

        Returns
        -------
        time_format : str
            Time in human readable format
    """
    # TODO: remove this
    # seconds += 3600 * 5 + 60 * 30
    seconds_in_hour = 3600

    day = int(seconds) // (seconds_in_hour * 24)
    hour = (int(seconds) // seconds_in_hour) % 24
    minute = (int(seconds) % seconds_in_hour) // 60
    sec = (int(seconds) % seconds_in_hour) % 60

    if day > 0:
        return "{:01d}days {:02d}h{:02d}m{:02d}s".format(day, hour, minute, sec)
    elif hour > 0:
        return "{:02d}h{:02d}m{:02d}s".format(hour, minute, sec)
    elif minute > 0:
        return "{:02d}m{:02d}s".format(minute, sec)
    else:
        return "{:.2f}s".format(seconds)