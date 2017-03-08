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
from datetime import datetime
from datetime import timedelta
import avro.io
import avro.schema

out_type = 'profiles'
extraction_dir = '/home/xplain/case128714/128714/impala/'
out_dir = '/tmp/citi_analysis/'
out_file_name = out_dir + 'impala_' + out_type
start_date = datetime(2017, 02, 21, 0, 0)
end_date = datetime(2018, 02, 24, 0, 0)
EPOCH = datetime.utcfromtimestamp(0)
CONFIG_DICT = {'queries': {'directory': 'work_summary',
                           'metadata_split_char': ' ',
                           'output_keys': ['queryId', 'user', 'statement',
                                           'queryState', 'startTimeMillis',
                                           'endTimeMillis', 'durationMillis',
                                           'queryType', 'serviceName',
                                           'defaultDatabase', 'rowsProduced'],
                           'extract_type': 'day',
                           'time_key': 'startTimeMillis'},
               'profiles': {'directory': 'work_details',
                            'metadata_split_char': '!',
                            'output_keys': [],
                            'extract_type': 'all',
                            'time_key': 'defaultStartTimeMs'}}

CUR_CONFIG = CONFIG_DICT[out_type]
SCHEMA_DIR = extraction_dir + CUR_CONFIG['directory'] + '/partition_metadata/'
DATA_DIR = extraction_dir + CUR_CONFIG['directory'] + '/partitions/'
output_keys = CUR_CONFIG['output_keys']

#query has [runtimeProfileAvailable', frontEndHostId', defaultDatabase', syntheticAttributes', estimatedTimes', endTimeMillis', queryId', user', statement', rowsProduced', queryState', startTimeMillis', durationMillis', queryType', serviceName']
#profile has [defaultStartTimeMs', defaultEndTimeMs', serviceName', compressedRuntimeProfile', frontEndHostId']

json_pattern = re.compile('{(.*)}')


def unix_time_millis(dt):
    return (dt - EPOCH).total_seconds() * 1000.0

start_timestamp = unix_time_millis(start_date)
end_timestamp = unix_time_millis(end_date)

'''
Loop through the metadata information.
Use the details from the metadata to
    read the relevant data.
Gather the relevant data for NavOpt.
Store the data to a csv.
'''

out_dict = {}
out_list = []
schema_db = plyvel.DB(SCHEMA_DIR)
count = 0
for raw_partition_name, raw_schema in schema_db:
    '''
    the keys in the schema table look like:
        PARTITION_queries queries_YYYY-MM-DDTHH:MM:SS.SSSZ
    '''
    key_arr = raw_partition_name.split(CUR_CONFIG['metadata_split_char'])
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

        if CUR_CONFIG['extract_type'] == 'day':
            time_key = CUR_CONFIG['time_key']
            if time_key not in tmp_dict:
                continue
            if (tmp_dict[time_key] >= start_timestamp) and (tmp_dict[time_key] <= end_timestamp):
                tmp_date = datetime.fromtimestamp(tmp_dict[time_key]/1000.0)
                tmp_key = '%s_%s_%s'%(tmp_date.month, tmp_date.day, tmp_date.year)
                if tmp_key not in out_dict:
                    out_dict[tmp_key] = []
                out_dict[tmp_key].append(tmp_dict)
            else:
                continue
        if CUR_CONFIG['extract_type'] == 'all':
            time_key = CUR_CONFIG['time_key']
            if time_key not in tmp_dict:
                continue
            tmp_date = datetime.fromtimestamp(tmp_dict[time_key]/1000.0)
            tmp_key = '%s_%s_%s_%s_%s_%s'%(tmp_date.month, tmp_date.day, tmp_date.year, tmp_date.hour, tmp_date.minute, tmp_date.second)
            if tmp_key not in out_dict:
                out_dict[tmp_key] = []
            out_dict[tmp_key].append(tmp_dict)
        if CUR_CONFIG['extract_type'] == 'default':
            tmp_key = 'default'
            if tmp_key not in out_dict:
                out_dict[tmp_key] = []
            out_dict[tmp_key].append(tmp_dict)
    data_db.close()
schema_db.close()

for tmp_key in out_dict:
    out_list = out_dict[tmp_key]
    tmp_out_file_name = out_file_name + '_' + tmp_key + '.csv'
    with open(tmp_out_file_name, 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, output_keys, lineterminator='\n')
        dict_writer.writeheader()
        dict_writer.writerows(out_list)
