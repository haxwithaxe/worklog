# written for python3

import configparser

class ConfigError(Exception):
    """ Custom Exception for importing scripts to throw inorder to indicate a missing config or config value. """
    pass

class Config:

    def __init__(self, file_name, default_section='main'):
        self.file_name = file_name
        self.default_section = default_section
        self.conf = configparser.ConfigParser()
        self.conf.read(self.file_name)
        self._load()

    def _load(self):
        for attr, value in self.conf.items(self.default_section):
            if attr in self.__dict__:
                raise AttributeError("'%s' already exists as an attribute in this object." % attr)
            setattr(attr, value)
        for sec in self.conf.sections():
            if sec in self.__dict__:
                raise AttributeError("'%s' already exists as an attribute in this object." % sec)
            setattr(sec, {})
            self.sec.update(dict(self.conf.items(sec)))

    def __getattribute__(self, attr):
        if attr in self.__dict__:
            return self.__dict__.get(attr)
        elif attr.split('_', 1)[0] in self.__dict__:
            sec, opt = attr.split('_', 1)
            if opt in self.__dict__.get(sec):
                return self.__dict__.get(sec).get(opt)
        raise AttributeError("'%s' is not an attribute of this object.")

