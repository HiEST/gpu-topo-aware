#!/usr/bin/env bash

out_folder=$1

echo kill exp
kill -9 $(ps -aux | grep -v root |  grep exp | grep -v kill | awk '{ print $2}') 2> /dev/null ;

echo kill run
kill -9 $(ps -aux | grep -v root | grep run | grep -v kill | awk '{ print $2}') 2> /dev/null ;

echo kill caffe
kill -9 $(ps -aux | grep -v root | grep caffe | awk '{ print $2}') 2> /dev/null ;

echo kill nvidia
kill -9 $(ps -aux | grep -v root | grep nvidia | awk '{ print $2}') 2> /dev/null ;

(echo finished > $out_folder/finished) 2> /dev/null
echo finished