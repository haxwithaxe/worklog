
import argparse
from collections import Callable
import os

from worklog import alias
from worklog import color
from worklog.config import ConfigFile
from worklog.report import Report
from worklog.state import Worklog, Task, GoHome, Abort
from worklog.time_utils import resolve_at_or_ago
from worklog.upload import log_to_jira


CONFIG_PATH = '~/.worklog/config.json'
EPILOG = '''\
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
'''


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


def handle_dynamic_alias_commands( args, aliases ):
	if args.add:
		name = ''.join( args.add )
		value = ' '.join( args.description )
		print( 'Adding "{}" as an alias for "{}".'.format( name, value ) )
		aliases.set( name, value )
	elif args.remove:
		name = ''.join( args.remove )
		print( 'Removing "{}" as an alias.'.format( name ) )
		aliases.pop( name )


def translate_aliases( args, parser, aliases ):
	# If an alias was passed as the command unpack the values and reparse with start as the command.
	args_kwargs = [ 'start' ]
	kwargs = dict( args._get_kwargs() )
	alias_str = aliases.get( kwargs.pop( 'command' ) )
	description = [ alias_str ] + kwargs.pop( 'description' )
	# remove the alias specific options
	kwargs.pop( 'add' )
	kwargs.pop( 'remove' )
	for option, value in kwargs.items():
		args_kwargs.append( '--' + option )
		args_kwargs.append( value )
	args_kwargs.extend( description )
	args_kwargs.extend( args._get_args() )
	return parser.parse_args( args_kwargs )


def _description(sub_parser):
	sub_parser.add_argument(
			'description',
			default = None,
			metavar = 'DESCRIPTION',
			nargs = argparse.REMAINDER,
			help = "specify the task's description on the command line"
			)


def _ticket(sub_parser):
	sub_parser.add_argument( '-t', '--ticket', metavar = 'TICKET', help = 'the TICKET associated with the task' )

def _at(sub_parser):
	sub_parser.add_argument( '--ago', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )

def _ago(sub_parser):
	sub_parser.add_argument( '--at', metavar = 'TIME', help = 'start the task at TIME, instead of now' )


def _add_start_command( sub_parser, common_parser ):
	blurb = 'start a new task, closing the currently open task if any'
	start_parser = sub_parser.add_parser( 'start', help = blurb, description = blurb, parents = [ common_parser ] )
	_at( start_parser )
	_ago( start_parser )
	_ticket( start_parser )
	_description( start_parser )


def _add_resume_command( sub_parser, common_parser ):
	blurb = 'like start, but reuse the description from a previous task in this worklog by seleting it from a list'
	resume_parser = sub_parser.add_parser( 'resume', help = blurb, description = blurb, parents = [ common_parser ] )
	_at( resume_parser )
	_ago( resume_parser )


def _add_stop_command( sub_parser, common_parser ):
	blurb = 'close the currently open task'
	stop_parser = sub_parser.add_parser( 'stop', help = blurb, description = blurb, parents = [ common_parser ] )
	_at( stop_parser )
	_ago( stop_parser )


def _add_report_command( sub_parser, common_parser ):
	blurb = 'report the current state of the worklog'
	report_parser = sub_parser.add_parser( 'report', help = blurb, description = blurb, parents = [ common_parser ] )


def _add_upload_command( sub_parser, common_parser ):
	blurb = 'uploads worklog time to jira'
	sub_parser.add_parser( 'upload', help = blurb, description = blurb, parents = [ common_parser ] )


def _add_alias_command( sub_parser, common_parser, command_aliases ):
	blurb = 'short cut to "start <alias>" or add/remove aliases'
	alias_parser = sub_parser.add_parser( 
			'alias',
			aliases = command_aliases,
			help = blurb,
			description = blurb,
			parents = [ common_parser ]
			)
	_ago( alias_parser )
	_at( alias_parser )
	_ticket( alias_parser )
	_description( alias_parser )
	alias_parser.add_argument( '--add', metavar = 'ALIAS', nargs = 1 )
	alias_parser.add_argument( '--del', dest = 'remove', metavar = 'ALIAS', nargs = 1 )


def main( config ):
	aliases = alias.Aliases( config )
	command_aliases = tuple( aliases )
	parser = argparse.ArgumentParser(
		prog = 'worklog',
		description = "Manage and report time allocation",
		formatter_class = argparse.RawDescriptionHelpFormatter,
		epilog = EPILOG
	)
	sub_parser = parser.add_subparsers( dest = 'command' )
	common_parser = argparse.ArgumentParser( add_help = False )
	common_parser.add_argument( '--day', '-d', help = 'manage the worklog for DATE, defaults to today' )
	for add_parser in (
			_add_start_command,
			_add_resume_command,
			_add_stop_command,
			_add_report_command,
			_add_upload_command
			):
		add_parser( sub_parser, common_parser )
	_add_alias_command( sub_parser, common_parser, command_aliases )

	args = parser.parse_args()
	color.ENABLED = config.features.colorize

	if args.command == 'alias':
		handle_dynamic_alias_commands( args, aliases )
		raise Abort()
	elif args.command in command_aliases:
		args = translate_aliases( args, parser, aliases )
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
		config_path = os.path.expanduser( CONFIG_PATH )
		with ConfigFile( config_path ) as config:
			main( config )
	except Abort:
		pass
