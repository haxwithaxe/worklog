
from datetime import datetime, timedelta, time
import re

import color

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 8

DURATION_FACTORS = {
	'd': 60 * 60 * 8,
	'h': 60 * 60,
	'm': 60,
}

DURATION_RE = re.compile( r'\s*(?:\s*(\d+(?:\.\d+)?)([{0}]))\s*'.format( ''.join( DURATION_FACTORS.keys() ) ) )



def now():
	"""datetime.now() with seconds zeroed out"""
	now = datetime.now()
	return now.replace( second = 0, microsecond = 0 )



def duration_to_timedelta(duration):
	"""Convert a human readable time duration to a timedelta object

	Recognizes a sequence of one or more integers or floats appended with a
	unit (d,h,m), optionally separated by whitespace.

	Fractions less than 1 require a leading 0.

	Examples:
		15m
		0.5h
		1.5h
		1d 4.5h
		1d 4h 30m

	"""
	seconds = 0
	for match in DURATION_RE.finditer( duration ):
		seconds = seconds + ( float( match.group(1) ) * DURATION_FACTORS[match.group(2)] )
	return timedelta( seconds = seconds )


def resolve_at_or_ago( args = None, date = None ):
	if args.at:
		hour, minute = args.at.split( ':' )
		start = time( hour = int( hour ), minute = int( minute ) )
		return datetime.combine( date, start )
	elif args.ago:
		return now() - duration_to_timedelta( args.ago )
	else:
		return now()


class Duration:
	"""Represents a time duration in just hours, and minutes.

	Easy for conversion to jira-format

	"""

	def __init__(self, delta):
		self.delta = delta
		self.seconds = int(delta.total_seconds())
		self.hours, seconds = divmod(self.seconds, SECONDS_IN_HOUR)
		self.minutes, _ = divmod(seconds, SECONDS_IN_MINUTE)

	def __str__(self):
		parts = list()
		if self.hours > 0:
			parts.append("{:d}h".format(self.hours))
		if self.minutes > 0:
			parts.append("{:d}m".format(self.minutes))
		return " ".join(parts)

	def formatted(self):
		parts = ["", ""]
		if self.hours > 0:
			parts[0] = "{:d}h".format(self.hours)
		if self.minutes > 0:
			parts[1] = "{:d}m".format(self.minutes)
		return "{:>3} {:>3}".format(*parts)

	def colorized(self, **kwargs):
		bold_kwargs = kwargs.copy()
		bold_kwargs["bold"] = True
		parts = ["   ", "   "]
		if self.hours > 0:
			parts[0] = color.cyan( '{:2d}'.format( self.hours ), **bold_kwargs ) + color.cyan( 'h', **kwargs )
		if self.minutes > 0:
			parts[1] = color.blue( '{:2d}'.format( self.minutes ), **bold_kwargs ) + color.blue( 'm', **kwargs )
		return ' '.join( parts )
