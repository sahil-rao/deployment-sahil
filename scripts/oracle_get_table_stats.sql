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
select num_rows||','||blocks||','||avg_row_len||','||TO_CHAR(LAST_ANALYZED, 'MM/DD/YYYY HH24:MI:SS')||','||table_name
from dba_tables 
where owner=upper('&1');

spool off;
exit;
