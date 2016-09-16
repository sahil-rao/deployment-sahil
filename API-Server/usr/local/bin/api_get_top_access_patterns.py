#!/usr/bin/python

"""
Application API to get access pattern details.

"""
__author__ = 'Rituparna Agrawal'
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Rituparna Agrawal'
__email__ = 'parna@xplain.io'

from pymongo import MongoClient
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from json import *
from flightpath.Provenance import getMongoServer
from flightpath.services.app_append_core_pattern import *
import flightpath.utils as utils
import json
import pprint

pattern_mapping = {
        EntityType.SQL_PATTERN_JOIN: 'join',
        EntityType.SQL_PATTERN_CARTESIAN_JOIN: 'cartesian',
        EntityType.SQL_PATTERN_CORE_JOIN : 'core',
        EntityType.SQL_PATTERN_SNOWFLAKE_JOIN : 'snowflake',
        EntityType.SQL_PATTERN_STAR_JOIN : 'star', 
        EntityType.SQL_PATTERN_LINEAR_JOIN: 'linear',
        EntityType.SQL_PATTERN_COLUMNAR: 'sparse', 
        EntityType.SQL_PATTERN_FILTER: 'filter', 
        EntityType.SQL_PATTERN_COLUMN_FAMILY:'family',
        EntityType.SQL_PATTERN_CASE_STATEMENT:'CaseStatement', 
        EntityType.SQL_PATTERN_UNION:'union', 
        EntityType.SQL_PATTERN_AGGREGATION: 'AggregateFunction',
        EntityType.SQL_SUBQUERY: 'subquery',
        EntityType.SQL_INLINE_VIEW: 'inlineView'
}
INVALID_SUBQUERY_LOCATIONS = ('UNION', 'MINUS', 'UNION_ALL', 'INTERSECT', 'EXCEPT')

def execute(tenantid, msg_dict):
    '''
    Returns the details of the access patterns identfied by given list.
    '''
    entity_id = None
    pattern_type = None
    column_family_location = None

    if "pattern" in msg_dict:
        pattern_type = msg_dict["pattern"]
        '''
        check if in case of type column family
        if location was passed
        '''
        if pattern_type == 'family' and 'column_family_type' in msg_dict:
           column_family_location = msg_dict['column_family_type']

    if "byElapsedTime" in msg_dict:
        elapsed_time = msg_dict["byElapsedTime"]
    else:
        elapsed_time = False

    if "is_report" in msg_dict:
        is_report = msg_dict["is_report"]
    else:
        is_report = False

    client = getMongoServer(tenantid)
    db = client[tenantid]
    entities = db.entities

    redis_conn = RedisConnector(tenantid)
    mongoconn = Connector.getConnector(tenantid)
    if mongoconn is None:
        mongoconn = MongoConnector({'client':client, 'context':tenantid, \
                                   'create_db_if_not_exist':False})

    patternIds = []
    all_patterns = {}
    query_relations = {}
    qs_names_to_update = {}
    query_info_dict = {}

    found = False
    if pattern_type is not None:
        '''
        Searches for the pattern that was inputted.
        '''
        for pattern_entity_type in pattern_mapping:
            if pattern_mapping[pattern_entity_type] == pattern_type:
                found = True
                break
        else:
            pattern_entity_type = None

    if pattern_type is not None and found is False:
        return

    if pattern_entity_type is not None:
        if pattern_entity_type == "SQL_PATTERN_COLUMN_FAMILY" and is_report == True:
            # Regex query to exclude column families that contain inline views
            pattern_cursor = entities.find({"etype" : pattern_entity_type, "name": {"$regex": "^((?!u'IT).)*$"}}, {'_id':0}) 
        else:
            pattern_cursor = entities.find({"etype" : pattern_entity_type}, {'_id':0})
    else:
        pattern_cursor = entities.find({"etype" : {'$in': pattern_mapping.keys()}})

    for entity in pattern_cursor:
        all_patterns[entity['eid']] = entity

    start = 0
    end = 100
    delta = 100
    patterns = []

    """
    Loop over the top patterns from Redis. Create a list of 10.
    """
    while len(patterns) < 10:
        hybrid_patterns = []
        if pattern_entity_type is not None:
            if pattern_entity_type == "SQL_SUBQUERY":
                hybrid_patterns += redis_conn.getTopEtypeCounts("SQL_SUBQUERY", "instance_count", start, end)
            elif pattern_entity_type == "SQL_INLINE_VIEW":
                hybrid_patterns += redis_conn.getTopEtypeCounts("SQL_INLINE_VIEW", "instance_count", start, end)
            elif elapsed_time == True:
                hybrid_patterns += redis_conn.getTopEtypeCounts(pattern_entity_type, "totalElapsedTime", start, end)
            else:
                hybrid_patterns += redis_conn.getTopEtypeCounts(pattern_entity_type, "totalQueryCount", start, end)
        else:
            for pattern_entity_key in pattern_mapping:
                if pattern_entity_key == "SQL_SUBQUERY":
                    hybrid_patterns += redis_conn.getTopEtypeCounts("SQL_SUBQUERY", "instance_count", start, end)
                elif pattern_entity_key == "SQL_INLINE_VIEW":
                    hybrid_patterns += redis_conn.getTopEtypeCounts("SQL_INLINE_VIEW", "instance_count", start, end)
                elif elapsed_time == True:
                    hybrid_patterns += redis_conn.getTopEtypeCounts(pattern_entity_key, "totalElapsedTime", start, end)
                else:
                    hybrid_patterns += redis_conn.getTopEtypeCounts(pattern_entity_key, "totalQueryCount", start, end)

        """
          End of all patterns we know. So don't iterate further.
        """
        if len(hybrid_patterns) == 0:
            break

        patternIds = sorted(hybrid_patterns, key=lambda x: x[1], reverse = True)
        #patternIds = [temp_pattern[0] for temp_pattern in temp_patterns]

        process_patterns(redis_conn, db, entities, all_patterns, 10, patternIds, patterns, query_relations, qs_names_to_update, query_info_dict, column_family_location)
        start = end + 1
        end = end + delta

    for pat_eid in qs_names_to_update:
        entities.update({'eid': pat_eid}, {'$set': {'profile.qs_name' : qs_names_to_update[pat_eid]}})
    mongoconn.close()
    patterns = sorted(patterns, key = lambda x:x['totalQueryCount'], reverse = True)
    return patterns

def update_pattern_object(redis_conn, db, entities, pattern, pattern_entity, qs_names_to_update, query_info_dict):
    '''
    Input the pattern.
    Updates the pattern with the information needed for the UI.
    Returns the used eids to potentially be used later.
    '''
    pattern['totalQueryCount'] = 0

    queryCount = redis_conn.getEntityProfile(pattern_entity["eid"], "totalQueryCount")["totalQueryCount"]
    if queryCount == None:
        queryCount = 0
    pattern["totalQueryCount"] = int(queryCount)
    return None

def process_patterns(redis_conn, db, entities, all_patterns, final_count, patternIds, patterns, query_relations, qs_names_to_update, query_info_dict, column_family_location):
    count = len(patterns)
    for patternIdInfo in patternIds:
        patternEid = patternIdInfo[0]
        pat_inst_count = int(patternIdInfo[1])
        if patternEid not in all_patterns:
            continue

        pattern_entity = all_patterns[patternEid]
    
        #Column Family handling
        if pattern_entity['etype'] == "SQL_PATTERN_COLUMN_FAMILY" and column_family_location:
           if column_family_location != pattern_entity['profile']['location']:
              del all_patterns[patternEid]
              continue

        #Star Join handing.
        if pattern_entity['etype'] == "SQL_PATTERN_STAR_JOIN":
            '''
            This function is used to find core patterns for given star pattern
            append core pattern eid to the tables in star pattern, that are part
            of that respective core pattern
            '''
            #print "Entity id:", pattern_entity['eid']
            append_core_pattern_to_star(pattern_entity, entities)

        #Linear Join handing.
        if pattern_entity['etype'] == "SQL_PATTERN_LINEAR_JOIN":
            '''
            This function is used to find core patterns for given linear pattern
            append core pattern eid to the tables in linear pattern, that are part
            of that respective core pattern
            '''
            append_core_pattern_to_linear(pattern_entity, entities)
        
        #SUBQUERY Handling here
        #print json.dumps(pattern_entity, indent = 2)
        if (pattern_entity['etype'] == "SQL_SUBQUERY" or 
            pattern_entity['etype'] == "SQL_INLINE_VIEW"):
            
            '''
            Subqueries are not created as a pattern so are treated differently.
            '''
            subquery_pattern = {
                #'FullQueryList': {
                #    'queries':[]
                #},
                #'eid': pattern_entity["eid"],
                #'display_name': None,
                #'pat_eid': pattern_entity["eid"],
                'totalQueryCount': 0,
                'refersCTE': False,
                'occurrences': pat_inst_count,
                'location': None,
                'subqueryString': None,
                'table_eid': None
            }
            compiler_to_use = pattern_entity['compiler_to_use'] if 'compiler_to_use' in pattern_entity else 'gsp'
            origQuery = None
            location = None
            refersCTE = False
            qs_name = None
            if pattern_entity['etype'] == "SQL_SUBQUERY":
                if "display_name" in pattern_entity:
                    subquery_pattern["display_name"] = pattern_entity["display_name"]
                else:
                    subquery_pattern["display_name"] = 'Subquery %s'%pattern_entity['eid']
                subquery_pattern['type'] = 'subquery'
            else:
                if "display_name" in pattern_entity:
                    subquery_pattern["display_name"] = pattern_entity["display_name"]
                else:
                    subquery_pattern["display_name"] = 'Inline View %s'%pattern_entity['eid']
                subquery_pattern['type'] = 'inlineview'
            if compiler_to_use in pattern_entity['profile']["Compiler"]:
                if 'origQuery' in pattern_entity['profile']["Compiler"][compiler_to_use]:
                    origQuery = pattern_entity['profile']["Compiler"][compiler_to_use]['origQuery']
                if 'location' in pattern_entity['profile']["Compiler"][compiler_to_use]:
                    location = pattern_entity['profile']["Compiler"][compiler_to_use]['location']
                    if location in INVALID_SUBQUERY_LOCATIONS:
                        continue
                if 'refersCTE' in pattern_entity['profile']["Compiler"][compiler_to_use]:
                    refersCTE = pattern_entity['profile']["Compiler"][compiler_to_use]['refersCTE']
            if 'qs_name' in pattern_entity['profile']:
                qs_name = pattern_entity['profile']['qs_name']
            subquery_pattern['refersCTE'] = refersCTE
            subquery_pattern['subqueryString'] = origQuery
            subquery_pattern['location'] = location
            outer_queries = utils.get_all_outer_queries(redis_conn, subquery_pattern['eid'], path=set())
            subquery_pattern["FullQueryList"]["queries"] = []
            subquery_pattern['queryIds'] = list(outer_queries)
            subquery_pattern['totalQueryCount'] = 0
            for x in outer_queries:
                subquery_pattern['totalQueryCount'] += utils.get_instance_count(redis_conn, x, query_info_dict)

            #Gets the eid of the inline view table.
            iv_tables = redis_conn.getRelationships(subquery_pattern["eid"], None, 'WRITE')
            if iv_tables:
                subquery_pattern['table_eid'] = iv_tables[0]['end_en']

            """
            '''
            Attempts to get the name of the query set.
            Looks at pattern group.
            If there is no pattern group, looks on the pattern itself.
            '''
            group_eids = redis_conn.getRelationships(subquery_pattern["eid"], None, 'PATTERN_GROUP_ACCESS_PATTERN')[:1]

            p_group = None
            if len(group_eids) == 0:
                '''
                Look on pattern itself.
                If pattern doesn't have a name, then make one.
                '''
                if qs_name is not None:
                    subquery_pattern["FullQueryList"]['display_name'] = '%s'%(qs_name)
                else:
                    set_name = IdentityService.getNewCounterId(db, 'q_set')
                    qs_names_to_update[pattern_entity["eid"]] = set_name
                    subquery_pattern["FullQueryList"]['display_name'] = '%s'%(set_name)
            else:
                '''
                Look up the pattern group
                '''
                group_eid = group_eids[0]['end_en']
                p_group = entities.find_one({'eid':group_eid}, {'profile.qs_map':1, '_id':0})
                if p_group and 'profile' in p_group:
                    if 'qs_map' in p_group['profile']:
                        if subquery_pattern['pat_eid'] in p_group['profile']['qs_map']:
                            subquery_pattern["FullQueryList"]['display_name'] = '%s'%(p_group['profile']['qs_map'][subquery_pattern['pat_eid']]['display_name'])
            RelatedQueryLists = get_related_query_sets(redis_conn, entities, p_group, subquery_pattern['pat_eid'], query_info_dict)
            subquery_pattern['RelatedQueryLists'] = RelatedQueryLists
            """

            count = count + 1
            patterns.append(subquery_pattern)
            if count == final_count:
                break
            continue

        
        pattern = pattern_entity["profile"]
        if 'aggregateClauseHash' in pattern:
            pattern.pop('aggregateClauseHash') 
        '''
        query_eids is a list of queries that are related to the given pattern.
        '''
        query_eids = update_pattern_object(redis_conn, db, entities, pattern, pattern_entity, qs_names_to_update, query_info_dict)

        if 'qs_name' in pattern:
            pattern.pop('qs_name')
        if 'FullQueryList' in pattern:
            pattern['qids'] = pattern['FullQueryList']
            pattern.pop('FullQueryList')
        if 'tableEid' in pattern:
            pattern['tid'] = pattern['tableEid']
            pattern.pop('tableEid')
        if 'type' in pattern:
            pattern.pop('type')
        if 'aggregateColumns' in pattern:
            pattern.pop('aggregateColumns')
        if 'level' in pattern:
            pattern.pop('level')
        print "A pattern:", pattern
        patterns.append(pattern)
        count = count + 1

        if count == final_count:
            break

if __name__ == '__main__':
    #pprint.pprint(execute("64322d4d-eeaa-cf33-d0a8-279abbfe384b", {'pattern': 'linear', 'byElapsedTime': True}))
    #a = execute("64322d4d-eeaa-cf33-d0a8-279abbfe384b", {'pattern': 'subquery', 'byElapsedTime': False})
    #pprint.pprint(a)
    #pprint.pprint(execute("137772ca-5025-ce93-4f34-d98e3ee92330", {'pattern': 'family', 'byElapsedTime': False, 'column_family_type': 'SELECT'}))
    #pprint.pprint(execute("137772ca-5025-ce93-4f34-d98e3ee92330", {'pattern': 'family', 'byElapsedTime': False, 'column_family_type': 'GROUP BY'}))
    #a = execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {'pattern': 'AggregateFunction'})
    #a = execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {'pattern': 'filter'})
    #pprint.pprint(a)
    #print "======= AGGREGATES ========="
    a = execute("7f99e352-3533-0f3b-4a70-ff7f18d19c73", {'pattern': 'subquery'})
    pprint.pprint(a)
