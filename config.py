# written for python3

import configparser

class ConfigError(Exception):
    """ Custom Exception for importing scripts to throw inorder to indicate a missing config or config value. """
    pass


class Config:
    """ """

    def __init__(self, filename, default_section="main"):
        self.filename = filename
        self.default_section = default_section
        self.config = configparser.ConfigParser()
        self.config.read([self.filename])

    def _has_section(self, section, option, exception=True):
        """ Wrap ConfigParser.has_section in order to throw meaningful errors. """
        if self.config.has_section(section):
            return True
        if exception:
            raise AttributeError("Section: '{}' does not exists in '{}'".format(section, self.filename))
        return False

    def _has_option(self, section, option, exception=True):
        """ Wrap ConfigParser.has_section in order to throw meaningful errors. """
        if self._has_section(section) and self.conf.has_option(section, option):
            return True
        if exception:
            raise AttributeError("Section: '{}' in '{}' does not contain the option '{}'".format(section, self.filename, option))
        return False

    def _get_option(self, option, section=None, value_type=None):
        """ """
        section = section or self.default_section
        if self._has_option(section, option):
            return self.gettyped(section, option, value_type)

    def _get_typed(self, section, option, value_type):
        typed_getters = {None: self.config.get, int: self.config.get_int, float: self.config.get_float, bool: self.config.get_boolean}
        return typed_getters[value_type](section, option)


    def __getattr__(self, attr):
        """ """
        try:
            object.__getattribute__(self, attr)
        except AttributeError:
            if self. _has_option(self.default_section, attr, exception=False):
                return self._get_option(self.default_section, attr)
            else:
                section, option = attr.split('_', 1)
                typed_option, value_type = option.split('_', 1)
                if self._has_option(section, option, exception=False):
                    return self._get_option(section, option)
                if self._has_option(section, typed_option):
                    return self._get_option(section, typed_option, value_type)

if __name__ == "__main__":
    print(Config(filename="test.ini").__dict__)
