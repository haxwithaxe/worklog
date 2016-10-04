
import os

CONFIG_PATH = os.path.expanduser( '~/.worklog/config.json' )


NO_ROLLUP_KEYWORDS = ( 'lunch', 'break' )


class Usage( Exception ):
	
	def __init__( self, section = None ):
		super().__init__( 'Request to show usage for section: "{}"'.format(section or 'all') )
		self.section = section
