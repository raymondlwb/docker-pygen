import logging

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(module)s.%(funcName)s - %(message)s')


def get_logger(name):
    return logging.getLogger(name)


def set_log_level(level):
    logging.root.setLevel(level)


class EnhancedDict(dict):
    def __init__(self, *args, **kwargs):
        super(EnhancedDict, self).__init__(*args, **kwargs)
        self.default_value = kwargs.get('default')
        self.ignore_case = kwargs.get('ignore_case', True)

    def __getattr__(self, item):
        if item in self:
            return self[item]

        elif self.ignore_case and hasattr(item, 'lower'):
            for key in self:
                if hasattr(key, 'lower') and key.lower() == item.lower():
                    return self[key]

        return self.default_value


class EnhancedList(list):
    @property
    def first(self):
        if len(self):
            return self[0]

    @property
    def first_value(self):
        for item in self:
            if item:
                return item

    @property
    def last(self):
        if len(self):
            return self[-1]

    def __getattr__(self, item):
        return self.__dict__[item]

    def __setattr__(self, key, value):
        self.__dict__[key] = value
