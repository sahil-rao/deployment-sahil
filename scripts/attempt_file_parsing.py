import pandas


def execute(params):
    script_path = params['script_path']
    col_delim = str(params['col_delim'])
    row_delim = str(params['row_delim'])

    df = pandas.read_csv(script_path,
                         delimiter=col_delim,
                         lineterminator=row_delim,
                         skipinitialspace=True,
                         error_bad_lines=False)

    print df[:10]

if __name__ == '__main__':
    params = {}
    script_path = '/tmp/script_name.sql'
    col_delim = ','
    row_delim = '\n'
    execute(params)
