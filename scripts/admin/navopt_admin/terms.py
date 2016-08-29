from .util import prompt
import click


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
def list(ctx):
    with ctx.obj['cluster'].dbsilo('dbsilo1').mongo_master() as mongo:
        for term in mongo['xplainIO'].terms_and_conditions.find():
            print 'version:', term.get('version')
            print term.get('text', '')[0:1000]
            print '...'
            print '-' * 78
            print


@cli.command()
@click.argument('version', required=False)
@click.pass_context
def show(ctx, version):
    with ctx.obj['cluster'].dbsilo('dbsilo1').mongo_master() as mongo:
        terms_and_conditions = mongo['xplainIO'].terms_and_conditions

        if version is None:
            terms = terms_and_conditions.find(
                {},
                {'_id': 0}).sort('version', -1).limit(1)
        else:
            terms = terms_and_conditions.find(
                {'version': version},
                {'_id': 0})

        try:
            term = next(terms)
        except StopIteration:
            ctx.fail('no term found for version')

        print 'version:', term['version']
        print term['text']


@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.pass_context
def update(ctx, filename):
    with open(filename) as f:
        text = f.read().strip()

    with ctx.obj['cluster'].dbsilo('dbsilo1').mongo_master() as mongo:
        db = mongo['xplainIO']

        terms = db.terms_and_conditions.find().sort('version', -1).limit(1)

        try:
            term = next(terms)
        except StopIteration:
            version = 1
        else:
            if term.get('text') == text:
                ctx.fail('terms unchanged')

            version = term.get('version', 0) + 1
            print term

        msg = 'are you sure you want to update the terms? [yes/no] '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('terms not updated')

        db.terms_and_conditions.update(
            {'version': version},
            {'$set': {'text': text, 'version': version}},
            upsert=True)

        msg = 'do you want to reset the user signed terms? [yes/no] '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('signed terms not reset')

        db.users.update({}, {'$set': {'signed_terms': False}}, multi=True)

        print 'signed terms reset'
