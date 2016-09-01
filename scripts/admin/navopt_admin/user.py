from .table import format_table
from .util import prompt
import bcrypt
import click
import getpass
import operator


DEFAULT_FIELDS = ('_id', 'email', 'signed_terms', 'organizations')
DEFAULT_SORT_FIELDS = 'email'
DEFAULT_ADMIN_FIELDS = (
    '_id',
    'username',
    'password',
    'execPermission',
    'supportPermission',
    'associatedNavOptEmail',
)
DEFAULT_ADMIN_SORT_FIELDS = 'username'


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


@cli.command('list-admin')
@click.pass_context
def list_admin(ctx):
    mongo_cluster = ctx.obj['cluster'].dbsilo('dbsilo1').mongo_cluster()

    with mongo_cluster.master() as mongo:
        print format_table(
            mongo['xplainIO'].adminusers.find(),
            fields=DEFAULT_ADMIN_FIELDS,
            sort_field=DEFAULT_ADMIN_SORT_FIELDS,
            key=lambda field: (lambda item: item.get(field)),
        )


@cli.command('create-admin')
@click.option('--exec/--no-exec', 'exec_permission', default=False)
@click.option('--support/--no-support', 'support_permission', default=False)
@click.option('--email', default=None)
@click.argument('username')
@click.pass_context
def create_admin(ctx,
                 exec_permission,
                 support_permission,
                 email,
                 username):
    mongo_cluster = ctx.obj['cluster'].dbsilo('dbsilo1').mongo_cluster()

    password = getpass.getpass('password: ')
    confirm_password = getpass.getpass('confirm_password: ')

    if password != confirm_password:
        ctx.fail('password does not match')

    user = {
        'username': username,
        'password': bcrypt.hashpw(password, bcrypt.gensalt(10, '2a')),
        'execPermission': exec_permission,
        'supportPermission': support_permission,
        'associatedNavOptEmail': email,
    }

    with mongo_cluster.master() as mongo:
        db = mongo['xplainIO']

        user_record = db.adminusers.find_one({'username': username})
        if user_record is None:
            db.adminusers.insert_one(user)
            print 'created admin'
        else:
            user_record.update(user)
            db.adminusers.update({'_id': user_record['_id']}, user)
            print 'updated admin'


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
