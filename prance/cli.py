# -*- coding: utf-8 -*-
"""CLI for prance."""

__author__ = 'Jens Finkhaeuser'
__copyright__ = 'Copyright (c) 2016-2018 Jens Finkhaeuser'
__license__ = 'MIT +no-false-attribs'
__all__ = ()


import click

import prance


def __write_to_file(filename, specs):  # noqa: N802
  """
  Write specs to the given filename.

  This takes into account file name extensions as per `fs.write_file`.
  """
  from prance.util import fs, formats
  contents = formats.serialize_spec(specs, filename)
  fs.write_file(filename, contents)


def __parser_for_url(url, resolve, backend, strict):  # noqa: N802
  """Return a parser instance for the URL and the given parameters."""
  # Try the URL
  formatted = click.format_filename(url)
  click.echo('Processing "%s"...' % (formatted, ))

  from prance.util import fs
  fsurl = fs.abspath(url)
  import os.path
  if os.path.exists(fs.from_posix(fsurl)):
    url = fsurl

  # Create parser to use
  if resolve:
    click.echo(' -> Resolving external references.')
    return prance.ResolvingParser(url, lazy = True, backend = backend,
            strict = strict), formatted
  else:
    click.echo(' -> Not resolving external references.')
    return prance.BaseParser(url, lazy = True, backend = backend,
            strict = strict), formatted


def __validate(parser, name):  # noqa: N802
  """Validate a spec using this parser."""
  from prance.util.url import ResolutionError
  from prance import SwaggerValidationError
  try:
    parser.parse()
  except (ResolutionError, SwaggerValidationError) as err:
    msg = 'ERROR in "%s" [%s]: %s' % (name, type(err).__name__,
        str(err))
    click.secho(msg, err = True, fg = 'red')
    import sys
    sys.exit(1)

  # All good, next file.
  click.echo('Validates OK as %s!' % (parser.version,))


@click.group()
@click.version_option(version = prance.__version__)
def cli():
  pass  # pragma: no cover


class GroupWithCommandOptions(click.Group):
  """Allow application of options to group with multi command."""

  def add_command(self, cmd, name=None):
    click.Group.add_command(self, cmd, name=name)

    # add the group parameters to the command
    for param in self.params:
      cmd.params.append(param)

    # hook the commands invoke with our own
    cmd.invoke = self.build_command_invoke(cmd.invoke)
    self.invoke_without_command = True

  def build_command_invoke(self, original_invoke):
    def command_invoke(ctx):
      """Insert invocation of group function."""
      # separate the group parameters
      ctx.obj = dict(_params=dict())
      for param in self.params:
        name = param.name
        ctx.obj['_params'][name] = ctx.params[name]
        del ctx.params[name]

      # call the group function with its parameters
      params = ctx.params
      ctx.params = ctx.obj['_params']
      self.invoke(ctx)
      ctx.params = params

      # now call the original invoke (the command)
      original_invoke(ctx)

    return command_invoke


@click.group(cls = GroupWithCommandOptions)
@click.option(
    '--resolve/--no-resolve',
    default = True,
    help = 'Resolve external references before validation. The default is to '
           'do so.'
)
@click.option(
    '--backend',
    default = 'flex',
    metavar = 'BACKEND',
    nargs = 1,
    help = 'The validation backend to use. One of "flex", '
           '"swagger-spec-validator" or "openapi-spec-validator". The default'
           'is "flex".'
)
@click.option(
    '--strict/--no-strict',
    default = True,
    help = 'Be strict or lenient in validating specs. Strict validation '
           'rejects non-string spec keys, for example in response codes. '
           'Does not apply to the "flex" backend.'
)
@click.pass_context
def backend_options(ctx, resolve, backend, strict):
  ctx.obj['resolve'] = resolve
  ctx.obj['backend'] = backend
  ctx.obj['strict'] = strict


@backend_options.command()
@click.option(
    '--output-file', '-o',
    type = click.Path(exists = False),
    default = None,
    metavar = 'FILENAME',
    nargs = 1,
    help = '[DEPRECATED; see "compile" command] If given, write the '
           'validated specs to this file. Together with the --resolve '
           'option, the output file will be a resolved version of the input '
           'file.'
)
@click.argument(
    'urls',
    type = click.Path(exists = False),
    nargs = -1,
)
@click.pass_context
def validate(ctx, output_file, urls):
  """
  Validate the given spec or specs.

  If the --resolve option is set, references will be resolved before
  validation.

  Note that this merges referenced objects into the main specs. Validation
  backends used by prance cannot validate referenced objects, so resolving
  the references before validation allows for full spec validation.
  """
  # Ensure that when an output file is given, only one input file exists.
  if output_file:
    click.echo('The --output-file parameter is deprecated; use '
        'the "compile" command instead.', err = True)
  if output_file and len(urls) > 1:
    raise click.UsageError('If --output-file is given, only one input URL '
        'is allowed!')

  # Process files
  for url in urls:
    # Create parser to use
    parser, name = __parser_for_url(url, ctx.obj['resolve'],
        ctx.obj['backend'], ctx.obj['strict'])

    # Try parsing
    __validate(parser, name)

    # If an output file is given, write the specs to it.
    if output_file:
      __write_to_file(output_file, parser.specification)


@backend_options.command()
@click.argument(
    'urls',
    type = click.Path(exists = False),
    nargs = -1,
)
@click.argument(
    'output_file',
    type = click.Path(exists = False),
    nargs = 1,
)
@click.pass_context
def compile(ctx, urls, output_file):
  """
  FIXME

  Validate the given spec or specs.

  If the --resolve option is set, references will be resolved before
  validation.

  Note that this merges referenced objects into the main specs. Validation
  backends used by prance cannot validate referenced objects, so resolving
  the references before validation allows for full spec validation.
  """
  # Process files
  parsers = []
  for url in urls:
    # Create parser to use
    parser, name = __parser_for_url(url, ctx.obj['resolve'],
        ctx.obj['backend'], ctx.obj['strict'])

    # Try parsing
    __validate(parser, name)

    # Add to collection
    parsers.append(parser)

  print(parsers)

  # If an output file is given, write the specs to it.
  # if output_file:
  #   __write_to_file(output_file, parser.specification)


cli.add_command(validate)
cli.add_command(compile)
