#!/bin/bash

tail -F /var/log/vsftpd.log | while read line; do
  echo "Got a line"
  if echo "$line" | grep -q 'OK UPLOAD:'; then
    #filename=$(echo "$line" | cut -d, -f2)

    #if [ -s "$filename" ]; then        
        #echo "File $filename uploaded\n" >> /tmp/filelog
    /home/ubuntu/baaz_upload.py "$line"
    #fi
  fi
done
