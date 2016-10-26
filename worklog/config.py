
import json

from worklog import CONFIG_PATH


class Config:

	__passthrough = ( 'get', 'update' )

	def __init__( self, values, defaults, name = None ):
		self._values = values
		self._defaults = defaults or {}
		self.name = name

	def __setitem__( self, item, value ):
		# unpack Config objects so json can handle them
		if isinstance( value , Config ):
			value = dict( value )
		self._values[item] = value

	def __getitem__( self, item ):
		return self._values[item]

	def __iter__( self ):
		return iter( tuple( self._values.items() ) )

	def __getattr__( self, attr ):
		if attr in self.__passthrough:
			return getattr( self._values, attr )
		elif attr in self._values:
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

	def __init__( self, filename = None, defaults = None ):
		super().__init__( values = None, defaults = defaults, name = 'config' )
		self._filename = filename or CONFIG_PATH

	def __enter__( self ):
		self.__read()
		return self

	def __exit__( self, *err ):
		self.__write()

	def __read( self ):
		try:
			with open( self._filename, 'r' ) as config_file:
				self._values = json.load( config_file )
		except FileNotFoundError as e:
			print( e )

	def __write( self ):
		if self._values:
			try:
				with open( self._filename, 'w' ) as config_file:
					json.dump( self._values, config_file, sort_keys = True, indent = 4 )
			except FileNotFoundError as e:
				print( e )
