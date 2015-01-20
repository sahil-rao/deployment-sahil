-- __copyright__ = 'Copyright 2014, Xplain.IO Inc.'
-- __license__ = ''
--__version__ = '0.1'

set linesize 100 
set trimspool on
set long 100
set serveroutput on

--This code is used to drop table and in case of exception if its not present ignore it
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE sql_text_table';
   dbms_output.put_line('Droping the Table');
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

--This query is used to create table, which has information that we fetch from v$sql
create table sql_text_table as
select sql_id, elapsed_time, '"'||regexp_replace(sql_fulltext, CHR(10), ' ')||'"' as sql_fulltext
from v$sql
where parsing_schema_name=upper('&1') and parsing_user_id > 99;

--This procedure is used to dump sql_text_table create above into CSV file
CREATE OR REPLACE procedure DUMP_TABLE_TO_CSV( p_tname in varchar2,
                                    p_dir   in varchar2,
                                    p_filename in varchar2 )
   is
        l_output        utl_file.file_type;
        l_theCursor     integer default dbms_sql.open_cursor;
        l_columnValue   varchar2(4000);
        l_status        integer;
        l_query         varchar2(1000)
                       default 'select * from ' || p_tname;
       l_colCnt        number := 0;
       l_separator     varchar2(1);
       l_descTbl       dbms_sql.desc_tab;
   begin
       l_output := utl_file.fopen( p_dir, p_filename, 'w' );
       execute immediate 'alter session set nls_date_format=''dd-mon-yyyy hh24:mi:ss'' 
';
   
       dbms_sql.parse(  l_theCursor,  l_query, dbms_sql.native );
       dbms_sql.describe_columns( l_theCursor, l_colCnt, l_descTbl );
  
       for i in 1 .. l_colCnt loop
           utl_file.put( l_output, l_separator || '"' || l_descTbl(i).col_name || '"' 
);
           dbms_sql.define_column( l_theCursor, i, l_columnValue, 4000 );
           l_separator := ',';
       end loop;
       utl_file.new_line( l_output );
   
       l_status := dbms_sql.execute(l_theCursor);
   
       while ( dbms_sql.fetch_rows(l_theCursor) > 0 ) loop
           l_separator := '';
           for i in 1 .. l_colCnt loop
               dbms_sql.column_value( l_theCursor, i, l_columnValue );
               utl_file.put( l_output, l_separator || l_columnValue );
               l_separator := ',';
           end loop;
           utl_file.new_line( l_output );
       end loop;
       dbms_sql.close_cursor(l_theCursor);
       utl_file.fclose( l_output );
   
       execute immediate 'alter session set nls_date_format=''dd-MON-yy'' ';
   exception
       when others then
           execute immediate 'alter session set nls_date_format=''dd-MON-yy'' ';
           raise;
   end;
/

--This is function is used to create a directory where CSV file will be copied
CREATE OR REPLACE DIRECTORY SQL_TEXT_DIR AS '/tmp';

--This line execute above stored procedure
exec DUMP_TABLE_TO_CSV('sql_text_table','SQL_TEXT_DIR','sql_text.csv');

--This code is used to drop table and in case of exception if its not present ignore it
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE sql_text_table';
   dbms_output.put_line('Droping the Table');
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/
exit;
