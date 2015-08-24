import json
import os


class Config:

    def __init__( self, values, defaults, name = None ):
        self._values = values
        self._defaults = defaults or {}
        self.name = name

    def __getattr__( self, attr ):
        if attr in self._values:
            if isinstance( self._values, list ):
                return self._values[self._values.index( attr )]
            if isinstance( self._values, dict ):
                if isinstance( self._values[attr], dict ):
                    return Config( self._values[attr], self._defaults.get( attr ) )
            return self._values[attr]
        elif self._defaults and attr in self._defaults:
            return self._defaults[attr]
        elif hasattr( self._values, attr ):
            return getattr( self._values, attr )
        raise AttributeError( 'Configuration section "{}" not found'.format( attr ) )


class ConfigFile( Config ):

    def __init__( self, filename, defaults = None ):
        Config.__init__( self, values = None, defaults = defaults, name = 'config' )
        self._filename = filename
        try:
            with open( self._filename, 'r' ) as config_file:
                self._values = json.load( config_file )
        except FileNotFoundError as e:
            print( e )



def datetime_as_dict( obj ):
	return {
		"__klass__": "datetime",
		"year": obj.year,
		"month": obj.month,
		"day": obj.day,
		"hour": obj.hour,
		"minute": obj.minute,
		"second": obj.second,
		"microsecond": obj.microsecond,
	}
