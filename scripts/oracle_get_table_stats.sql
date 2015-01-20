-- __copyright__ = 'Copyright 2014, Xplain.IO Inc.'
-- __license__ = ''
--__version__ = '0.1'

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
spool table_stats.log 

set serveroutput on format wrapped;
begin
    DBMS_OUTPUT.put_line('TABLE_NAME,AVG_ROW_LEN,NUM_ROWS,ROW_RANGE');
end;
/

--Below query is used to get table stats info, the '||' is used for concatentation 
select table_name||','||avg_row_len||','||num_rows||','||CASE WHEN num_rows <=99999 THEN 'Extra Small'
                                                              WHEN num_rows <=999999 THEN 'Small'
                                                              WHEN num_rows <=99999999 THEN 'Medium'
                                                              WHEN num_rows <=999999999 THEN 'Large'
                                                              WHEN num_rows <=1000000000 THEN 'Extra Large'
                                                              ELSE '1B+'
                                                              END AS row_range
from dba_tables
where owner=upper('&1');

spool off;
exit;
