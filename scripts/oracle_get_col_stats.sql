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
select table_name||','||column_name||','||data_type||','||num_distinct||','||num_nulls||','||avg_col_len
from dba_tab_columns 
where owner=upper('&1');

spool off;
exit;
