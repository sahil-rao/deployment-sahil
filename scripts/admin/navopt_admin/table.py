import tabulate
import operator


def format_table(items, fields, key,
                 sort_field=None,
                 show_header=True):
    field_keys = [key(field) for field in fields]

    table = [
        [field_key(item) for field_key in field_keys]
        for item in items
    ]

    if sort_field:
        sort_index = fields.index(sort_field)
        table.sort(key=operator.itemgetter(sort_index))

    if show_header:
        headers = fields
        tablefmt = 'simple'
    else:
        headers = ()
        tablefmt = 'plain'

    return tabulate.tabulate(table, headers=headers, tablefmt=tablefmt)
