-- __copyright__ = 'Copyright 2014, Xplain.IO Inc.'
-- __license__ = ''
--__version__ = '0.1'

set head off
set feed off
set echo off
set heading off
set feedback off
set verify off
set trimspool on
set headsep off
set pagesize 0
set linesize 132
spool ddl_schema.xdlog 

--set this below stuff to disable output of detailed table related info
EXECUTE DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'PRETTY',true);
EXECUTE DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'STORAGE',false);
EXECUTE DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'SEGMENT_ATTRIBUTES',false);
EXECUTE DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'TABLESPACE',false);
--set this below stuff to disable output of detailed key table related info
EXECUTE DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'CONSTRAINTS',false);
EXECUTE DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'REF_CONSTRAINTS',false);
--This below query get DDL info, append semicolon as delimiter.
select to_char(DBMS_METADATA.GET_DDL ('TABLE', table_name, owner)), ';'
FROM dba_tables 
where owner=upper('&1');

spool off;
exit;
