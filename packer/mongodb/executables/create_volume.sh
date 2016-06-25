#!/bin/bash

set -e

source /usr/local/bin/navoptenv.sh

MAX_TRIES=60

grep="grep"
regex='s/.*\:[ \t]*"\{0,1\}\([^,"]*\)"\{0,1\},\{0,1\}/\1/'
sed="sed '${regex}'"

status="creating"
device="/dev/xvdf"
mount="/mnt/volume1"
new_volume="yes"

ctr=0
while [ ! -e "$device" ] ; do
    ctr=`expr $ctr + 1`
    if [ $ctr -eq $MAX_TRIES ]; then
        break
    fi
done

if [ ! -e "$device" ] ; then
	# ok, we are clean. now we need to figure out what to start with
	if [[ ${SET_SRC} == vol-* ]]; then
		volume_id=${SET_SRC}
	else
		if [[ ${SET_SRC} == snap-* ]]; then
			snapshot_id=${SET_SRC}
		fi
		echo "Creating the volume"
		if [[ ${snapshot_id} =~ snap-[[:alnum:]]{8} ]]; then
		        new_volume="no"
			volume_id=`eval "aws ec2 create-volume \
                                --volume-type io1 --iops 1000 \
				--size ${SET_SIZE} \
				--snapshot ${snapshot_id} \
				--availability-zone ${EC2_AVAILABILITY_ZONE} \
				--region ${AWS_DEFAULT_REGION} | ${grep} '\"VolumeId\"' | ${sed}"`
		else
			volume_id=`eval "aws ec2 create-volume \
                                --volume-type io1 --iops 1000 \
				--size ${SET_SIZE} \
				--availability-zone ${EC2_AVAILABILITY_ZONE} \
				--region ${AWS_DEFAULT_REGION} | ${grep} '\"VolumeId\"' | ${sed}"`
		fi
	fi
        echo "Volume created ${volume_id}"
	#echo ${volume_id} > ${file}
	echo "Testing the volume: ${status}"
	while [ $status != "available" ] ; do
		status=`eval "aws ec2 describe-volumes --volume-ids ${volume_id}  | ${grep} '\"State\"' | ${sed}"`
		/bin/sleep 1
		ctr=`expr $ctr + 1`
		if [ $ctr -eq $MAX_TRIES ]; then
			if [ $status -ne "available" ]; then
				/bin/echo "WARNING: Cannot create volume $volume_id -- Giving up after $MAX_TRIES seconds"
			fi
		fi
	done
	echo "Volume status: ${status}"
	if [ $status == "available" ]; then
                echo "Going to attach volume"
		aws ec2 attach-volume --volume-id ${volume_id} --instance-id ${EC2_INSTANCE_ID} --device $device 
		/bin/echo "Testing If Volume is Attached."
		while [ ! -e "$device" ] ; do
			/bin/sleep 1
			ctr=`expr $ctr + 1`
			if [ $ctr -eq $MAX_TRIES ]; then
				if [ ! -e "$device" ]; then
					/bin/echo "WARNING: Cannot attach volume $volume_id to $device -- Giving up after $MAX_TRIES seconds"
				fi
			fi
		done
	fi
fi

# ok, by now we should have a proper device
if [ "x$new_volume" = "xyes" ]; then
    echo "Making filesystem"
    mkfs -t ext3 ${device}
fi

echo "Mounting filesystem"
/bin/mount -t ext3 ${device} ${mount}

# and in case we start from a snapshot
rm -f /mnt/volume1/mongo/db/mongod.lock
/bin/echo "File system " ${device} " ready to be used at " ${mount}
