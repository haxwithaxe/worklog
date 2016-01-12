#!/usr/bin/python3

import argparse
from datetime import datetime, timedelta
from collections import Callable
from getpass import getpass
from jira.client import JIRA
from jira.utils import JIRAError
import os
import textwrap

import color
from config import ConfigFile
from state import Worklog, Task, GoHome, DummyRightNow, Abort
from time_utils import *



def on_start( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		start = resolve_at_or_ago( args, date = worklog.when )
		ticket = args.ticket
		description = " ".join(args.description)
		while len(description.strip()) == 0:
			try:
				description = input("Task description: ")
			except KeyboardInterrupt:
				raise Abort()
			except EOFError:
				raise Abort()
		worklog.insert( Task( start = start, ticket = ticket, description = description, logged = False, config = config ) )
	report( worklog, config )



def on_resume( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		start = resolve_at_or_ago( args, date = worklog.when )
		descriptions = list()
		for description in reversed([ task.description for task in worklog if isinstance(task, Task) ]):
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
				idx = int(input("Which description: "))
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
	report( worklog, config )


def on_stop( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		worklog.insert( GoHome( start = resolve_at_or_ago( args, date = worklog.when ) ) )
	report( worklog, config )


def log_to_jira( worklog, config ):

	oauth_token = None
	oauth_token_secret = None

	oauth_dict = {
		'access_token': oauth_token,
		'access_token_secret': oauth_token_secret,
		'consumer_key': None,
		'key_cert': open('/home/ckoepke/dev/worklog/rsa.pem').read()
	}
	options = { 'server': config.jira.server or  input( '\nJira Server: ' ) }
	#username = config.jira.username or input( '\nJira Username: ' )
	#password = config.jira.password or getpass()
	auth = ( username, password )
	try:
		jira = JIRA( options=options,oauth=oauth_dict)
		#jira = JIRA( options, basic_auth = auth )
	except JIRAError as e:
		print(e)
		return None
	print( 'Logging work ...' )
	if len( worklog ) > 0:
		for task, next_task in worklog.pairwise():
			if isinstance( task, GoHome ):
				continue
			if task.ticket is not None and not task.logged:
				duration = Duration( delta = next_task.start - task.start )
				if not duration.seconds:
					continue
				started = '{}-{}-{}T{}:{}:00.000-0400'.format(
					task.start.year,
					task.start.month,
					task.start.day,
					task.start.hour,
					task.start.minute
				)
				ticket = jira.issue( task.ticket )
				print( '\nLogging {} to ticket {}'.format( duration, ticket ) )
				jira.add_worklog(
					issue = ticket,
					timeSpent = str( duration ),
					started = datetime.strptime( started, '%Y-%m-%dT%H:%M:%S.000%z' )
				)
				task.logged = True
	print( 'Done.' )



def report( worklog, config ):
	lines = []
	total = timedelta( seconds = 0 )
	rollup = dict()
	lines.append( '{} {}'.format(
		color.bold( 'Worklog Report for' ),
		color.purple( worklog.when.strftime( '%F' ), bold = True )
	) )
	if len( worklog ) == 0:
		lines.append( '	no entries' )
	else:
		for task, next_task in worklog.pairwise():
			if isinstance( task, GoHome ):
				continue
			if isinstance( next_task, DummyRightNow ):
				colorize_end_time = color.yellow
			else:
				colorize_end_time = color.green
			delta = next_task.start - task.start
			if task.include_in_rollup():
				total += delta
				if task.description not in rollup:
					rollup[task.description] = delta
				else:
					rollup[task.description] += delta
			if delta > timedelta():
				if not task.logged:
					task.logged = False
				lines.append( '	{:5s} {} {:5s} {}{!s:>7}{} {} {}  {}'.format(
					color.green( task.start.strftime( '%H:%M' ) ),
					color.black( '-', intense = True ),
					colorize_end_time( next_task.start.strftime( '%H:%M' ) ),
					color.black( '(', intense = True ),
					Duration( delta ).colorized(),
					color.black( ')', intense = True ),
					{True: color.green('*'), False: color.red('*')}[task.logged],
					task.ticket,
					task.description
				) )

		lines.append( '\n	{!s:>7}  {}'.format(
			Duration( total ).colorized( underline = True ),
			color.colorize( 'TOTAL', bold = True, underline = True )
		) )
		for key in sorted( rollup.keys() ):
			lines.append( '	{!s:>7}  {}'.format(
				Duration( rollup[key] ).colorized(),
				color.bold( key )
			) )
		print( '\n'.join( lines ) )



def on_report( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		report( worklog, config )



def on_upload( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		log_to_jira( worklog, config )



def main():
	parser = argparse.ArgumentParser(
		description = "manage and report time allocation",
		formatter_class = argparse.RawDescriptionHelpFormatter,
		epilog = textwrap.dedent("""
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

	args = parser.parse_args()
	config_path = os.path.expanduser( '~/.worklog/config.json' )
	config = ConfigFile( config_path )
	color.ENABLED = config.features.colorize
	try:
		handler = globals()["on_{}".format(args.command)]
	except KeyError:
		parser.print_help()
	else:
		if isinstance( handler, Callable ):
			handler( args, config )
		else:
			parser.error("unrecognized command: '{}'".format(args.command))


if __name__ == "__main__":
	try:
		main()
	except Abort:
		pass

