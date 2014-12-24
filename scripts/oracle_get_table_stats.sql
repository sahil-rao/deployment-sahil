/*
 * Below are instruction on how to run this script
 * From a terminal where your oracle instancce is hosted, run below command:
 * "sqlplus <username>@orcl/<password> @/home/oracle/tpch/scripts/oracle_get_querylog.sql <owner_name>"
 */

set head off 
set feed off 
set echo off
#set colsep '|'
set heading off
set feedback off
set verify off
set trimspool on
set headsep off
set pagesize 0
set linesize 132
spool table_stats.xtblog 

--Below query is used to get table stats info, the '||' is used for concatentation 
select table_name||','||avg_row_len||','||num_rows||','||CASE WHEN num_rows <=9999 THEN 'Extra Small'
                                                              WHEN num_rows <=999999 THEN 'Small'
                                                              WHEN num_rows <=99999999 THEN 'Large'
                                                              WHEN num_rows <=99999999 THEN 'Extra Large'
                                                              ELSE '1B+'
                                                              END AS row_range
from dba_tables
where owner=upper('&1');

spool off;
exit;
