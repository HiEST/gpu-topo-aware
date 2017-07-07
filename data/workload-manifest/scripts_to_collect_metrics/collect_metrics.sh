#!/usr/bin/env bash

function gettime (){
    echo $@ | python -c 'from sys import stdin; from time import time; \
                        start = float(stdin.read().split()[0]); \
                        curr_time = float(time()); \
                        print "curr_time", curr_time, "elapsed", curr_time - start';

}
start_time=$1
interval=$2
folder=$3
dir="$folder"

mkdir -p $dir/nvlink

while [ $(ls $dir | grep finished | wc -l) -le 0 ]; do

  ps -ax -o pid,start_time,etime,%cpu,%mem,rss,cmd,euser | grep -v root | grep $(whoami) | grep -v ssh | \
                            grep -v grep | grep -v ps | grep -v bash | grep -v perf >> $dir/ps.out
  echo $(gettime $start_time) >> $dir/ps.out

  free -mh >> $dir/free.out
  echo $(gettime $start_time)  >> $dir/free.out

  vmstat | tail -n 1 | tr -s '[:space:]' | sed 's/ /;/g' | sed 's/^;//' >> $dir/vmstat-formatted.out
  echo $(gettime $start_time)  >> $dir/vmstat-formatted.out

  vmstat >> $dir/vmstat-raw.out
  echo $(gettime $start_time)  >> $dir/vmstat-raw.out

  nvidia-smi dmon -s pumetc -c 1 >> $dir/dmon.out
  echo $(gettime $start_time)  >> $dir/dmon.out

  for i in $(seq 0 3); do
    nvidia-smi nvlink -i $i -g 0 >> $dir/nvlink/gpu-"$i"
    echo $(gettime $start_time)  >> $dir/nvlink/gpu-"$i"
  done

  sleep $interval

done