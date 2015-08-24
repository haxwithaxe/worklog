#! /usr/bin/python3

import argparse
from collections import Callable
from collections.abc import MutableSequence
from datetime import date, datetime, timedelta, time
import errno
from getpass import getpass
from jira.client import JIRA
import json
import os
import re
import textwrap

import color
from config import ConfigFile

class Abort( Exception ):
    pass


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


def resolve_at_or_ago( args, date ):
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
        self.minutes, seconds = divmod(self.seconds, SECONDS_IN_MINUTE)

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


class Task:

    def __init__( self, start, ticket, description, logged = False ):
        self.start = start
        self.ticket = ticket
        self.description = description.strip()
        self.logged = logged

    def include_in_rollup(self):
        if self.description.lower() == "lunch":
            return False
        if self.description.lower() == "break":
            return False
        return True


class GoHome( object ):

    def __init__( self, start, *unused ):
        self.start = start


class DummyRightNow( Task ):

    def __init__( self ):
        super( DummyRightNow, self ).__init__( start = now(), ticket = '', description = '' )


class Worklog( MutableSequence ):

    def __init__( self, when = None ):
        self.when = date
        self._set_when( when )
        self.persist_path = os.path.expanduser( '~/.worklog/{}-2.json'.format( self.when.strftime( '%F' ) ) )
        try:
            with open(self.persist_path, "r") as json_file:
                self.store = json.load(json_file, object_hook=dict_to_object)
        except IOError as err:
            if err.errno == errno.ENOENT:
                self.store = list()
            else:
                raise

    def _set_when( self, when ):
        """ figure out the time context of this worklog. """
        if when is None:
            self.when = date.today()
        elif isinstance(when, str):
            if re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", when):
                self.when = datetime.strptime(when, "%Y-%m-%d").date()
            else:
                self.when = datetime.today()+timedelta(days=int(when))

    def __getitem__(self, *args):
        return self.store.__getitem__(*args)

    def __setitem__(self, *args):
        return self.store.__setitem__(*args)

    def __delitem__(self, *args):
        return self.store.__delitem__(*args)

    def __len__(self, *args):
        return self.store.__len__(*args)

    def insert(self, *args):
        value = self.store.append(*args)
        self.store.sort(key=lambda t: t.start)
        return value

    def save(self):
        directory = os.path.split(self.persist_path)[0]
        if not os.access(directory, os.F_OK):
            os.makedirs(directory, mode=0o755)
        with open(self.persist_path, "w") as json_file:
            json.dump(self.store, json_file, cls=KlassEncoder, indent=4)

    def pairwise(self):
        offset = self.store[1:]
        offset.append(DummyRightNow())
        return zip(self.store, offset)


class KlassEncoder( json.JSONEncoder ):
    """Encodes Task objects and datetime objects to JSON using __klass__ indicator key"""

    def default( self, obj ):
        if isinstance( obj, ( Task, GoHome ) ):
            d = obj.__dict__.copy()
            d["__klass__"] = obj.__class__.__name__
            return d
        elif isinstance(obj, datetime):
            return {
                "__klass__": "datetime",
                "year": obj.year,
                "month": obj.month,
                "day": obj.day,
                "hour": obj.hour,
                "minute": obj.minute,
                "second": obj.second,
                "microsecond": obj.microsecond,
            }
        else:
            return json.JSONEncoder.default(obj)


def dict_to_object(d):
    """ When this was an instance method on a subclass of json.JSONDecoder, python totally fucked up giving me `TypeError: __init__() got multiple values for argument "object_hook"` even though I was overriding, not adding, my own object_hook pulling it out into a global function (ugh) and passing it along to json.load as the object_hook option worked around this stupid problem.
    """
    if "__klass__" not in d:
        return d
    klass = d.pop("__klass__")
    try:
        factory = globals()[klass]
    except KeyError:
        d["__klass__"] = klass
        return d
    else:
        return factory(**d)


def parse_common_args( args ):
    return Worklog( when = args.day )


def on_start( args, config ):
    worklog = parse_common_args( args )

    start = resolve_at_or_ago( args, date = worklog.when )
    ticket = args.ticket

    try:
        description = " ".join(args.description)
        while len(description.strip()) == 0:
            try:
                description = input("Task description: ")
            except KeyboardInterrupt:
                raise Abort()
            except EOFError:
                raise Abort()
        if config.features.get( 'scrape-ticket' ) and description and not ticket:
            ticket = _pull_ticket_from_description( description, config )
        worklog.insert( Task( start = start, ticket = ticket, description = description, logged = False ) )
        worklog.save()
    except Abort:
        print()
    report( worklog, config )


def _pull_ticket_from_description( description, config ):
    if not description:
        return None
    ticket_re = re.compile( '({})-[0-9]+'.format( '|'.join( config.jira.get('projects', []) ) ) )
    re_match = ticket_re.search( description )
    if re_match:
        ticket = re_match.group()
        return ticket


def on_resume( args, config ):
    worklog = parse_common_args( args )
    start = resolve_at_or_ago( args, date = worklog.when )
    try:
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
        worklog.insert( Task( start = start, ticket = ticket, description = description, logged = True ) )
        worklog.save()
    except Abort:
        print()
    report( worklog, config )


def on_stop( args, config ):
    worklog = parse_common_args( args )
    worklog.insert( GoHome( start = resolve_at_or_ago( args, date = worklog.when ) ) )
    worklog.save()
    report( worklog, config )


def log_to_jira( worklog, config ):
    options = { 'server': config.jira.server or  input( '\nJira Server: ' ) }
    username = config.jira.username or input( '\nJira Username: ' )
    password = config.jira.password or getpass()
    auth = ( username, password )
    jira = JIRA( options, basic_auth = auth )
    if len( worklog ) > 0:
        for task, next_task in worklog.pairwise():
            if isinstance( task, GoHome ):
                continue
            if task.ticket is not None and not task.logged:
                time = Duration( delta = next_task.start - task.start )
                if not time.seconds:
                    continue
                started = '{}-{}-{}T{}:{}:00.000-0400'.format(
                    task.start.year,
                    task.start.month,
                    task.start.day,
                    task.start.hour,
                    task.start.minute
                )
                ticket = jira.issue( task.ticket )
                print( '\nLogging {} to ticket {}'.format( time, ticket ) )
                jira.add_worklog(
                    issue = ticket,
                    timeSpent = str( time ),
                    started = datetime.strptime( started, '%Y-%m-%dT%H:%M:%S.000%z' )
                )
                task.logged = True


def report( worklog, config ):
    total = timedelta( seconds = 0 )
    rollup = dict()
    print( '{} {}'.format(
        color.bold( 'Worklog Report for' ),
        color.purple( worklog.when.strftime( '%F' ), bold = True )
    ) )
    if len( worklog ) == 0:
        print( '    no entries' )
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
            print( '    {:5s} {} {:5s} {}{!s:>7}{}  {}  {}'.format(
                color.green( task.start.strftime( '%H:%M' ) ),
                color.black( '-', intense = True ),
                colorize_end_time( next_task.start.strftime( '%H:%M' ) ),
                color.black( '(', intense = True ),
                Duration( delta ).colorized(),
                color.black( ')', intense = True ),
                task.ticket,
                task.description
            ) )

        print( '\n    {!s:>7}  {}'.format(
            Duration( total ).colorized( underline = True ),
            color.colorize( 'TOTAL', bold = True, underline = True )
        ) )
        for key in sorted( rollup.keys() ):
            print( '    {!s:>7}  {}'.format(
                Duration( rollup[key] ).colorized(),
                color.bold( key )
            ) )


def on_report( args, config ):
    worklog = parse_common_args( args )
    report( worklog, config )


def on_upload( args, config ):
    worklog = parse_common_args( args )
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

