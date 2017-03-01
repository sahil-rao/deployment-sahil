# (c) Copyright 2017 Cloudera, Inc. All rights reserved.

__author__ = 'Samir Pujari'
__copyright__ = 'Copyright 2017, Cloudera, Inc.'
__credits__ = ['Samir Pujari']
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Samir Pujari'
__email__ = 'samir@cloudera.com'

import io
import re
import csv
import json
import zlib
import plyvel
import avro.io
import avro.schema


out_type = 'queries'
extraction_dir = '/home/xplain/tmp/impala/'
out_file_name = '/tmp/impala_' + out_type + '.csv'

CONFIG_DICT = {'queries': {'directory': 'work_summary',
                         'metadata_split_char': ' ',
                         'output_keys': ['queryId', 'user', 'statement',
                                         'queryState', 'startTimeMillis',
                                         'endTimeMillis', 'durationMillis',
                                         'queryType', 'serviceName',
                                         'defaultDatabase', 'rowsProduced']},
               'profiles': {'directory': 'work_details',
                           'metadata_split_char': '!',
                           'output_keys': []}}
SCHEMA_DIR = extraction_dir + CONFIG_DICT[out_type]['directory'] + '/partition_metadata/'
DATA_DIR = extraction_dir + CONFIG_DICT[out_type]['directory'] + '/partitions/'
output_keys = CONFIG_DICT[out_type]['output_keys']

#query has [runtimeProfileAvailable', frontEndHostId', defaultDatabase', syntheticAttributes', estimatedTimes', endTimeMillis', queryId', user', statement', rowsProduced', queryState', startTimeMillis', durationMillis', queryType', serviceName']
#profile has [defaultStartTimeMs', defaultEndTimeMs', serviceName', compressedRuntimeProfile', frontEndHostId']

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
    key_arr = raw_partition_name.split(CONFIG_DICT[out_type]['metadata_split_char'])
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
        if output_keys:
            tmp_dict = {x: decoded_data[x] for x in output_keys}
        else:
            output_keys = decoded_data.keys()
            tmp_dict = decoded_data

        if 'compressedRuntimeProfile' in tmp_dict:
            tmp_dict['compressedRuntimeProfile'] = repr(zlib.decompress(tmp_dict['compressedRuntimeProfile']))

        if 'statement' in tmp_dict:
            s = tmp_dict['statement']
            if type(s) is unicode:
                '''
                This makes sure the query is utf8 formatted
                    and is on a single line. Much easier to truncate the file.
                '''
                tmp_dict['statement'] = s.encode('utf8')
                tmp_dict['statement'] = tmp_dict['statement'].replace("\n", " ")
        out_list.append(tmp_dict)
    data_db.close()
schema_db.close()

with open(out_file_name, 'wb') as output_file:
    dict_writer = csv.DictWriter(output_file, output_keys, lineterminator='\n')
    dict_writer.writeheader()
    dict_writer.writerows(out_list)
