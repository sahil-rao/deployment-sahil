from .table import format_table
from .util import prompt
import click
import operator


DEFAULT_FIELDS = ('_id', 'email', 'signed_terms', 'organizations')
DEFAULT_SORT_FIELDS = 'email'


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
def list(ctx):
    mongo_cluster = ctx.obj['cluster'].dbsilo('dbsilo1').mongo_cluster()

    with mongo_cluster.master() as mongo:
        print format_table(
            mongo['xplainIO'].users.find(),
            fields=DEFAULT_FIELDS,
            sort_field=DEFAULT_SORT_FIELDS,
            key=operator.itemgetter,
        )


@cli.command('accept-terms')
@click.argument('email')
@click.pass_context
def accept_terms(ctx, email):
    mongo_cluster = ctx.obj['cluster'].dbsilo('dbsilo1').mongo_cluster()

    with mongo_cluster.master() as mongo:
        db = mongo['xplainIO']
        user = db.users.find_one({'email': email})
        if user is None:
            ctx.fail('user does not exist')

        if user['signed_terms']:
            print 'user already accepted terms'
            return

        msg = 'Are you sure you want to accept these terms? [yes/no] '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('user unchanged')

        db.users.update(
            {'_id': user['_id']},
            {'$set': {'signed_terms': True}},
        )
