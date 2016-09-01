import click


class CommaSeparatedListParamType(click.ParamType):
    name = 'list'

    def convert(self, value, param, ctx):
        return value.split(',')

COMMA_SEPARATED_LIST_TYPE = CommaSeparatedListParamType()


def prompt(msg, assume_yes=None):
    if assume_yes is not None:
        return assume_yes

    while True:
        response = raw_input(msg).lower()
        if response in ('yes', 'y'):
            return True
        elif response in ('no', 'n'):
            return False
