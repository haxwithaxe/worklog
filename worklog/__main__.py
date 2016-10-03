
import argparse
from collections import Callable
import os
import textwrap

from worklog import alias
from worklog import color
from worklog.config import ConfigFile
from worklog.report import Report
from worklog.state import Worklog, Task, GoHome, Abort
from worklog.time_utils import resolve_at_or_ago
from worklog.upload import log_to_jira



def on_start( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		start = resolve_at_or_ago( args, date = worklog.when )
		ticket = args.ticket
		description = ' '.join( args.description )
		while len( description.strip() ) == 0:
			try:
				description = input( 'Task description: ' )
			except KeyboardInterrupt:
				raise Abort()
			except EOFError:
				raise Abort()
		worklog.insert( Task( start = start, ticket = ticket, description = description, logged = False, config = config ) )
	print( Report( worklog, config ) )



def on_resume( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		start = resolve_at_or_ago( args, date = worklog.when )
		descriptions = list()
		for description in reversed( [ task.description for task in worklog if isinstance( task, Task ) ] ):
			if description not in descriptions:
				descriptions.append( description )
		# when using resume, it means we're no longer working on the description that is now the first
		# item in this list, because of how we've sorted it. It is quite inconvenient for the first
		# choice to be the one we know for sure the user won't pick, bump it to the end of the line
		most_recent_description = descriptions.pop( 0 )
		descriptions.append( most_recent_description )
		for idx, description in enumerate( descriptions ):
			print( '[{:d}] {}'.format( idx, description ) )
		description = None
		while description is None:
			try:
				idx = int( input( "Which description: " ) )
				description = descriptions[idx]
				for task in worklog:
					if task.description == description:
						ticket = task.ticket
			except KeyboardInterrupt:
				raise Abort()
			except EOFError:
				raise Abort()
			except ( ValueError, IndexError ):
				print( 'Must be an integer between 0 and {:d}'.format( len( descriptions ) ) )
		worklog.insert( Task( start = start, ticket = ticket, description = description, logged = True, config = config ) )
	print( Report( worklog, config ) )



def on_stop( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		worklog.insert( GoHome( start = resolve_at_or_ago( args, date = worklog.when ) ) )
	print( Report( worklog, config ) )



def on_report( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		print( Report( worklog, config ) )



def on_upload( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		log_to_jira( worklog, config )



def main():
	config_path = os.path.expanduser( '~/.worklog/config.json' )
	config = ConfigFile( config_path )
	command_aliases = dict( alias.get_aliases( config ).__iter__() )
	parser = argparse.ArgumentParser(
		prog = 'worklog',
		description = "manage and report time allocation",
		formatter_class = argparse.RawDescriptionHelpFormatter,
		epilog = textwrap.dedent( """\
			DURATIONs
			  Spans of time can be provided in a concise format, a series of integers or
			  floats each appended with a unit: d, h, m. Whitespace between each component
			  is optional. Fractions less than 1 require a leading 0.

			  Note that a day is 8 hours.

			  Examples:
				15m
				0.5h
				1.5h
				1d 4.5h
				1d 4h 30m
				1d4h30m

			  Note that, while whitespace is optional, if you do specify a duration on the
			  command line and it includes whitespace, you"ll have to quote it.

			DATEs
			  Dates should be provided in the form YYYY-MM-DD.

			TIMEs
			  Times should be provided in the form HH:MM. All times used, including "now",
			  have their seconds zeroed out. All times provided on the command line are
			  assumed to occur today.

			Config File:
			  ~/.worklog/config.json - Can be created to store username and password to avoid
			  being prompted to type in your credentials for Jira authentication.

			  Example File:
				{ "username" : "jsmith" }

			  WARNING:
				Uploading multiple times in one calendar day will cause inconsistencies with time tracking
				on the server side.
		""" ),
	)
	sub_parser = parser.add_subparsers( dest = 'command' )

	common_parser = argparse.ArgumentParser( add_help = False )
	common_parser.add_argument( '--day', '-d', help = 'manage the worklog for DATE, defaults to today' )

	blurb = 'start a new task, closing the currently open task if any'
	start_parser = sub_parser.add_parser( 'start', help = blurb, description = blurb, parents = [ common_parser ] )
	start_parser.add_argument( '--ago', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
	start_parser.add_argument( '--at', metavar = 'TIME', help = 'start the task at TIME, instead of now' )
	start_parser.add_argument( '-t', '--ticket', metavar = 'TICKET', help = 'the TICKET associated with the task' )
	start_parser.add_argument( 'description', metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

	blurb = 'like start, but reuse the description from a previous task in this worklog by seleting it from a list'
	resume_parser = sub_parser.add_parser( 'resume', help = blurb, description = blurb, parents = [ common_parser ] )
	resume_parser.add_argument( '--ago', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
	resume_parser.add_argument( '--at', metavar = 'TIME', help = 'start the task at TIME, instead of now' )

	blurb = 'close the currently open task'
	stop_parser = sub_parser.add_parser( 'stop', help = blurb, description = blurb, parents = [ common_parser ] )
	stop_parser.add_argument( '--ago', metavar = 'DURATION', help = 'close the open task DURATION time ago, instead of now' )
	stop_parser.add_argument( '--at', metavar = 'TIME', help = 'close the open task at TIME, instead of now' )

	blurb = 'report the current state of the worklog'
	report_parser = sub_parser.add_parser( 'report', help = blurb, description = blurb, parents = [ common_parser ] )

	blurb = 'uploads worklog time to jira'
	upload_parser = sub_parser.add_parser( 'upload', help = blurb, description = blurb, parents = [ common_parser ] )

	blurb = 'short cut to "start <alias>"'
	alias_parser = sub_parser.add_parser( 'alias', aliases = tuple( command_aliases.keys() ), help = blurb, description = blurb )
	alias_parser.add_argument( '--ago', default = None, metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
	alias_parser.add_argument( '--at', default = None, metavar = 'TIME', help = 'start the task at TIME, instead of now' )
	alias_parser.add_argument( '-t', '--ticket', default = None, metavar = 'TICKET', help = 'the TICKET associated with the task' )
	alias_parser.add_argument( 'description', default = None, metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

	args = parser.parse_args()
	color.ENABLED = config.features.colorize
	# If an alias was passed as the command unpack the values and reparse with start as the command.
	if args.command in command_aliases:
		args_kwargs = [ 'start' ]
		kwargs = dict( args._get_kwargs() )
		alias_str = alias.resolve_alias( kwargs.pop( 'command' ), command_aliases )
		description = [ alias_str ] + kwargs.pop( 'description' )
		for option, value in kwargs.items():
			args_kwargs.append( '--' + option )
			args_kwargs.append( value )
		args_kwargs.extend( description )
		args_kwargs.extend( args._get_args() )
		args = parser.parse_args( args_kwargs )
	try:
		handler = globals()['on_{}'.format( args.command )]
	except KeyError:
		parser.print_help()
	else:
		if isinstance( handler, Callable ):
			handler( args, config )
		else:
			parser.error( "unrecognized command: '{}'".format( args.command ) )



if __name__ == "__main__":
	try:
		main()
	except Abort:
		pass
