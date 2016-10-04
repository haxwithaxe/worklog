
class Aliases:

	def __init__( self, config ):
		self.config = config

	def __iter__( self ):
		return iter( dict( self.config.aliases ) )

	def __getitem__( self, alias ):
		if alias in dict( self.config.aliases ):
			return ' '.join( ( self.config.aliases[alias], alias ) )

	def __delitem__( self, alias ):
		_aliases = self.config.aliases
		_aliases.pop( alias )
		self.config['aliases'] = _aliases

	def __setitem__( self, alias, real_value ):
		_aliases = self.config.aliases or {}
		_aliases[alias] = real_value
		self.config['aliases'] = _aliases

	def __contains__( self, alias ):
		return alias in self.config.aliases

	def get( self, alias, default = None ):
		try:
			return self[alias]
		except KeyError:
			return default

	def set( self, alias, value ):
		self[alias] = value

	def pop( self, alias ):
		value = self[alias]
		del self[alias]
		return value


if __name__ == '__main__':
	from worklog.config import ConfigFile

	with ConfigFile() as config:
		print( ' '.join( Aliases( config ) ))
