
import os

from worklog.config import ConfigFile


def get_aliases( config = None ):
	if not config:
		config = ConfigFile()
	return config.aliases or {}


def resolve_alias( alias, aliases ):
	print( alias, aliases )
	if alias in aliases:
		return ' '.join( ( aliases[alias], alias ) )
	return False


if __name__ == "__main__":
	print( ' '.join( get_aliases().keys() ) )
