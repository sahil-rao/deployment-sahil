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
spool col_stats.xcollog 

--Below query is used to get table stats info, the '||' is used for concatentation,
--even though you specifiy owner it shows recycle table which starts with 'BIN$*' we ignore those 
select table_name||','||column_name||','||data_type||','||num_distinct||','||num_nulls||','||avg_col_len 
from dba_tab_columns 
where owner=upper('&1')
and table_name NOT LIKE 'BIN$%';

spool off;
exit;
