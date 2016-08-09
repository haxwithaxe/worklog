
from collections import namedtuple



class BadAlias( Exception ):
	pass

class NewArgs:

	def __init__( self, data ):
		self.__data = data

	def __iter__( self ):
		return iter( self.__data )

	def __getitem__( self, key ):
		return self.__data[key]

	def __setitem__( self, key, value ):
		self.__data[key] = value

	def __getattr__( self, attr ):
		if attr in self.__data:
			return self.__data[attr]

	def update( self, data ):
		self.__data.update( data )


def handle_alias( args, config ):
	alias = None
	if len(args.alias) > 1:
		line = ' '.join( args.alias )
		if line in config.aliases:
			alias = config.aliases.get( line )
	elif args.alias[0] in config.aliases:
		alias = config.aliases.get( args.alias[0] )
		alias['description'] += ' '.join( args.alias[1:] )
	if alias:
		new_args = NewArgs( alias )
	else:
		raise BadAlias( 'Invalid command: {}'.format( args.alias ) )
	return new_args
