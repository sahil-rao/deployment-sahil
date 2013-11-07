#!/bin/bash

#
# Hourly script to be run on Data Acqusion server.
#
# - Copies files from S3 buckets to /mnt
# - For any new file it encounters, it calls Flightpath processing to
#   acquire data from the new fileset.
#
#
function processFile {
    customer=$1
    target=$2
    file=$3
    echo "Processing File $file for $customer" >> /tmp/hourly-script.log
    mkdir $target/inprogress
    cd $target/inprogress
    ext=${file:(-3)}
    if [ "$ext" == ".gz" ]
    then
	echo "Untaring file"
        tar -zxf $file
    fi
    if [ "$ext" == "tar" ]
    then
	echo "Untaring file"
        tar -xf $file
    fi
    cd ..
    ls -r $target/inprogress
    echo "Calling FPProcessing for $file" >> /tmp/hourly-script.log
    /usr/local/bin/FPProcessing.py $customer $target/inprogress $file
    rm -rf $target/inprogress
    echo "done $file"
    #processedFile.py $customer $file
}

echo "-------------------" >> /tmp/hourly-script.log

while read line
do 
    customer=$line
    echo $customer >> /tmp/hourly-script.log
    targetdir="/mnt/volume1/$customer"
    echo $targetdir
    if [[ ! -d "${targetdir}" ]]
    then
        mkdir -p $targetdir
    fi
    echo "Going to copy files from S3" >> /tmp/hourly-script.log
    s3cmd sync --skip-existing s3://partner-logs/$customer/ $targetdir/
    echo "File copy complete for ${customer}" >> /tmp/hourly-script.log
    FILES=$targetdir/*
    for f in $FILES
    do
        if [[ ! -f "${f}" ]]
        then
                continue
        fi
        stat="0"
    	echo "Checking File ${f}" >> /tmp/hourly-script.log
        stat=`/usr/local/bin/isProcessed.py $customer $f`
        echo "Status is $stat" >> /tmp/hourly-script.log
        if [ $stat == 0 ]
        then
            processFile $customer $targetdir $f
        fi
    done 
done < /etc/Baaz/customerlist

