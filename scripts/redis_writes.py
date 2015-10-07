import time
from flightpath.RedisConnector import *

tenant = 'de33904f-fbab-c5f9-7b00-805d16b7df86'
redis_conn = RedisConnector(tenant)
batch_mode = False
start_time = time.time()

num_iter = 1000
times = {'create': 0, 'subtract': 0, 'add':0, 'read':0}
redis_conn.create_pipeline()
for i in range(0,num_iter):
    totalQueryCount = i*12
    i = str(i)
    
    s = time.time()
    redis_conn.createEntityProfile(i,'blah')
    times['create'] += time.time()-s
    s = time.time()

    queryCount = redis_conn.getEntityProfile(i, "totalQueryCount")["totalQueryCount"]
    times['read'] += time.time()-s
    
    queryCount = int(queryCount) if queryCount else 0
    
    s = time.time()
    redis_conn.incrEntityCounter(i, "totalQueryCount", sort = True, incrBy = -1*queryCount, batch_mode=batch_mode)
    times['add'] += time.time()-s

    s = time.time()
    redis_conn.incrEntityCounter(i, "totalQueryCount", sort = True, incrBy = totalQueryCount, batch_mode = batch_mode)
    times['subtract'] += time.time()-s
redis_conn.execute_pipeline()
print times