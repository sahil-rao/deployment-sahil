import io
import re
import csv
import json
import plyvel
import avro.io
import avro.schema

IMPALA_DIR = '/home/xplain/tmp/impala/'
SCHEMA_DIR = IMPALA_DIR + 'work_summary/partition_metadata/'
DATA_DIR = IMPALA_DIR + 'work_summary/partitions/'
OUT_FILE_NAME = '/tmp/impala_queries.csv'
OUTPUT_KEYS = ['queryId', 'user', 'statement', 'queryState', 'durationMillis',
               'queryType', 'serviceName', 'defaultDatabase']

json_pattern = re.compile('{(.*)}')

'''
Loop through the metadata information.
Use the details from the metadata to
    read the relevant data.
Gather the relevant data for NavOpt.
Store the data to a csv.
'''
out_list = []
schema_db = plyvel.DB(SCHEMA_DIR)
for raw_partition_name, raw_schema in schema_db:
    '''
    the keys in the schema table look like:
        PARTITION_queries queries_2017-02-17T08:38:55.599Z
    '''
    key_arr = raw_partition_name.split(' ')
    if len(key_arr) < 2:
        #this skips any keys that don't have enough info.
        continue
    file_dir = key_arr[1]
    #this pulls out the JSON object from the value.
    json_result = json_pattern.search(raw_schema)
    if not json_result:
        continue
    avro_schema_str = json_result.group(0)
    schema = avro.schema.parse(avro_schema_str)

    data_db = plyvel.DB(DATA_DIR+file_dir)
    for tmp_key, raw_profile in data_db:
        '''
        Loads the avro schema and the serialized data as an object.
        '''
        bytes_reader = io.BytesIO(raw_profile)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(schema)
        decoded_data = reader.read(decoder)

        #We only care about specific keys.
        tmp_dict = {x: decoded_data[x] for x in OUTPUT_KEYS}

        if 'statement' in tmp_dict:
            s = tmp_dict['statement']
            if type(s) is unicode:
                '''
                This makes sure the query is utf8 formatted
                    and is on a single line. Much easier to truncate the file.
                '''
                tmp_dict['statement'] = s.encode('utf8').encode('string_escape')
        out_list.append(tmp_dict)
    data_db.close()
schema_db.close()

with open(OUT_FILE_NAME, 'wb') as output_file:
    dict_writer = csv.DictWriter(output_file, OUTPUT_KEYS, lineterminator='\n')
    dict_writer.writeheader()
    dict_writer.writerows(out_list)
