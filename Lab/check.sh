#!/bin/bash
for i in `find *`
do 
	if [ ! -d ${i} ]
	then
		stat1=`cat $i | grep irzan`
		if [ ! -z "$stat1" ]
		then
	   		echo "found on file $i"
		fi
	fi
done
