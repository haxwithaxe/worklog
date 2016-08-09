
ENABLED = True

RESET = 0
RESET_ENCODED = '\033[0m'

BOLD_ON = 1
BOLD_OFF = 22

FAINT_ON = 2
FAINT_OFF = 22

ITALIC_ON = 3
ITALIC_OFF = 23

UNDERLINE_ON = 4
UNDERLINE_OFF = 24

INVERSE_ON = 7
INVERSE_OFF = 27

STRIKE_ON = 9
STRIKE_OFF = 29

BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
PURPLE = 5
CYAN = 6
WHITE = 7
DEFAULT = 9


def encode( *values ):
	if not ENABLED:
		return ''
	return '\033[{}m'.format( ';'.join( str( value ) for value in values ) )


def build( before, value, after ):
	if not ENABLED:
		return value
	return '{}{}{}'.format( encode( *before ), value, encode( *after ) )


def vbuild( *values ):
	"""Infer the before and after based upon what's a string and what's a number.

	Maybe a dangerous convenience

	"""
	before = list()
	string_value = None
	after = list()
	eat = lambda x: before.append( x )

	for value in values:
		if isinstance( value, int ):
			eat( value )
		if isinstance( value, str ):
			if value is None:
				string_value = value
				eat = lambda x: after.append( x )
			else:
				raise ValueError( 'Too many strings in arguments' )

	return build( before, string_value, after )


def bold( s ):
	if not ENABLED:
		return s
	return vbuild( BOLD_ON, str( s ), BOLD_OFF )


def faint( s ):
	if not ENABLED:
		return s
	return vbuild( FAINT_ON, str( s ), FAINT_OFF )


def italic( s ):
	if not ENABLED:
		return s
	return vbuild( ITALIC_ON, str( s ), ITALIC_OFF )


def underline( s ):
	if not ENABLED:
		return s
	return vbuild( UNDERLINE_ON, str( s ), UNDERLINE_OFF )


def inverse( s ):
	if not ENABLED:
		return s
	return vbuild( INVERSE_ON, str( s ), INVERSE_OFF )


def strike( s ):
	if not ENABLED:
		return s
	return vbuild( STRIKE_ON, str( s ), STRIKE_OFF )


def colorize( value, fg = None, bg = None, intense = False, bold = False, faint = False, italic = False, underline = False, inverse = False, strike = False ):
	if not ENABLED:
		return value
	if bold and faint:
		raise ValueError( 'Values `bold` and `faint` are mutually exclusive.' )
	before = list()
	after = list()
	if intense:
		if fg is not None:
			fg += 60
		if bg is not None:
			bg += 60
	if fg is not None:
		fg += 30
		before.append( fg )
		after.append( DEFAULT + 30 )
	if bg is not None:
		bg += 40
		before.append( bg )
		after.append( DEFAULT + 40 )
	if bold:
		before.append( BOLD_ON )
		after.append( BOLD_OFF )
	if faint:
		before.append( FAINT_ON )
		after.append( FAINT_OFF )
	if italic:
		before.append( ITALIC_ON )
		after.append( ITALIC_OFF )
	if underline:
		before.append( UNDERLINE_ON )
		after.append( UNDERLINE_OFF )
	if inverse:
		before.append( INVERSE_ON )
		after.append( INVERSE_OFF )
	if strike:
		before.append( STRIKE_ON )
		after.append( STRIKE_OFF )
	return build( before, value, after )


def black( value, **kwargs ):
	kwargs['fg'] = BLACK
	return colorize( value, **kwargs )


def red( value, **kwargs ):
	kwargs['fg'] = RED
	return colorize( value, **kwargs )


def green( value, **kwargs ):
	kwargs['fg'] = GREEN
	return colorize( value, **kwargs )


def yellow( value, **kwargs ):
	kwargs['fg'] = YELLOW
	return colorize( value, **kwargs )


def blue( value, **kwargs ):
	kwargs['fg'] = BLUE
	return colorize( value, **kwargs )


def magenta( value, **kwargs ):
	kwargs['fg'] = MAGENTA
	return colorize( value, **kwargs )


def purple( value, **kwargs ):
	kwargs['fg'] = PURPLE
	return colorize( value, **kwargs )


def cyan( value, **kwargs ):
	kwargs['fg'] = CYAN
	return colorize( value, **kwargs )


def white( value, **kwargs ):
	kwargs['fg'] = WHITE
	return colorize( value, **kwargs )
