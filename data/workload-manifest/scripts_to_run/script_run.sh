#!/usr/bin/env bash

export CUDA_DEVICE_ORDER=PCI_BUS_ID
PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/gpfs/gpfs_4mb/mamaral/caffe_dir/opencv/release/unix-install/
export PKG_CONFIG_PATH

#export LD_LIBRARY_PATH=/home/$(whoami)/caffe_dir/protoc/lib/:/home/$(whoami)/caffe_dir/hdf5/lib/:/home/$(whoami)/caffe_dir/lmdb/lib/:/home/$(whoami)/caffe_dir/leveldb/out-shared/:/home/$(whoami)/caffe_dir/opencv_bin/lib:/home/$(whoami)/caffe_dir/cudnn/targets/ppc64le-linux/lib/:/home/$(whoami)/caffe_dir/nccl/lib:/home/$(whoami)/caffe_dir/boost/lib:/home/$(whoami)/caffe_dir/glog/lib
export LD_LIBRARY_PATH=$HOME/softwares/OpenBLAS/build/lib/
dir=/gpfs/gpfs_4mb/mamaral
export LD_LIBRARY_PATH=LD_LIBRARY_PATH:$dir/caffe_dir/protoc/lib/:$dir/caffe_dir/hdf5/lib/:$dir/caffe_dir/lmdb/lib/:$dir/caffe_dir/leveldb/out-shared/:$dir/caffe_dir/opencv_bin/lib:$dir/caffe_dir/cudnn/targets/ppc64le-linux/lib/:$dir/caffe_dir/nccl/lib:$dir/caffe_dir/boost/lib:$dir/caffe_dir/glog/lib

all=$@
job_id=$1; shift;
net=$1; shift;
size=$1; shift;
numgpus=$1; shift;
gpus=$1; shift;
gpus_name=$1; shift;
dir=$1; shift;
numactl=$@

folder1=$dir/job_id-"$job_id"--"$net"--gpus-"$gpus"--batch_size-"$size"/
size=$(echo "$size * $numgpus" | bc)

mkdir -p $folder1/metrics
echo $folder1 $gpus

echo $all >> $folder1/config.out
echo parameters >> $folder1/config.out
echo jobId $job_id >> $folder1/config.out
echo net $net >> $folder1/config.out
echo size $size >> $folder1/config.out
echo gpus $gpus >> $folder1/config.out
echo num $numgpus >> $folder1/config.out
echo gpus_name $gpus_name >> $folder1/config.out
echo dir $dir >> $folder1/config.out
echo numactl $numactl >> $folder1/config.out

curr=$(pwd)

cd /home/`whoami`/data-dir/caffe
caffe=/gpfs/gpfs_4mb/mamaral/caffe_dir/caffe-with-nccl/build/tools/caffe

rm models-variable/"$net"/solver_new.prototxt 2> /dev/null
cp models-variable/"$net"/solver_tine.prototxt models-variable/"$net"/solver_new.prototxt
sed -i -- 's/train_val_1.prototxt/train_val_new.prototxt/g' models-variable/"$net"/solver_new.prototxt


#echo $folder1 > "$dir"/tmp/last-exp
#/home/$(whoami)/experiments/varying-gpu-number/collect-metrics/collect.sh 5 $folder1/metrics &
#pidmetrics=$!

## Configuring the workload
rm models-variable/"$net"/train_val_new.prototxt 2> /dev/null
cp models-variable/"$net"/train_val_1.prototxt models-variable/"$net"/train_val_new.prototxt
sed -i -- "s/batch_size: train/batch_size: $size/g" models-variable/"$net"/train_val_new.prototxt
test_size=$(echo "$size"/"$numgpus" | bc)
if [ $test_size -lt 1 ]; then
test_size=1
fi
sed -i -- "s/batch_size: test/batch_size: $test_size/g" models-variable/"$net"/train_val_new.prototxt

# Starting workload
echo starting caffe
export CUDA_VISIBLE_DEVICES="$gpus"
#(perf stat -vd -o $folder1/metrics/perf-"$net"-"$gpus_name".out  /usr/bin/time --format="time= %e" $numactl $caffe train \
(/usr/bin/time --format="time= %e" $numactl $caffe train \
            --solver=models-variable/"$net"/solver_new.prototxt -gpu \
            all)  &> "$folder1"/"$net"-"$gpus_name".out &

sleep 3
echo caffe has started
pidcaffe=$!

#echo caffe pid $pidcaffe
#"$curr"/performance-counters.sh $pidcaffe >> $folder1/metrics/pmu-"$gpus_name".out  &
#pidpmu=$!

echo waiting caffe pid $pidcaffe
echo waiting caffe pid $pidcaffe >> $folder1/config.out

while true; do
    if [ $(ps -aux | grep -v root | grep $(whoami) | grep -v grep  | grep "$pidcaffe" | wc -l ) -le 0 ]; then
        echo caffe terminated >> $folder1/config.out
        break
    fi
    echo waiting caffe pid $pidcaffe
    echo waiting caffe pid $pidcaffe >> $folder1/config.out
    sleep 1
done

# Kill the collect-metrics in case it hasn't terminated
#kill -9 $pidmetrics 2> /dev/null
#kill -9 $pidpmu 2> /dev/null

echo The workload has finished >> "$folder1"/"$net"-"$gpus_name".out
echo The workload has finished >> "$folder1"/config.out
echo The workload has finished