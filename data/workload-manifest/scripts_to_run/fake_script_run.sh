#!/usr/bin/env bash

function waitcaffe (){
  pid=$1
  while true; do
      if [ $(ps -aux | grep -v root | grep $(whoami) | grep -v grep | grep "$pid" | wc -l ) -le 0 ]; then
        break;
      fi
      sleep 1
  done
}

export CUDA_DEVICE_ORDER=PCI_BUS_ID

export LD_LIBRARY_PATH=/home/$(whoami)/caffe_dir/protoc/lib/:/home/$(whoami)/caffe_dir/hdf5/lib/:/home/$(whoami)/caffe_dir/lmdb/lib/:/home/$(whoami)/caffe_dir/leveldb/out-shared/:/home/$(whoami)/caffe_dir/opencv_bin/lib:/home/$(whoami)/caffe_dir/cudnn/targets/ppc64le-linux/lib/:/home/$(whoami)/caffe_dir/nccl/lib:/home/$(whoami)/caffe_dir/boost/lib:/home/$(whoami)/caffe_dir/glog/lib

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

#cd /home/$(whoami)/caffe_dir/caffe-with-nccl
#
#rm models-variable/"$net"/solver_new.prototxt 2> /dev/null
#cp models-variable/"$net"/solver_tine.prototxt models-variable/"$net"/solver_new.prototxt
#sed -i -- 's/train_val_1.prototxt/train_val_new.prototxt/g' models-variable/"$net"/solver_new.prototxt


#echo $folder1 > "$dir"/tmp/last-exp
#/home/$(whoami)/experiments/varying-gpu-number/collect-metrics/collect.sh 5 $folder1/metrics &

## Configuring the workload
#rm models-variable/"$net"/train_val_new.prototxt 2> /dev/null
#cp models-variable/"$net"/train_val_1.prototxt models-variable/"$net"/train_val_new.prototxt
#sed -i -- "s/batch_size: train/batch_size: $size/g" models-variable/"$net"/train_val_new.prototxt
#test_size=$(echo "$size"/"$numgpus" | bc)
#if [ $test_size -lt 1 ]; then
#test_size=1
#fi
#sed -i -- "s/batch_size: test/batch_size: $test_size/g" models-variable/"$net"/train_val_new.prototxt

# Starting workload
echo starting caffe
export CUDA_VISIBLE_DEVICES="$gpus"
echo "perf stat -vd -o $folder1/metrics/perf-"$net"-"$gpus_name".out  /usr/bin/time --format="time= %e" $numactl ./build/tools/caffe train
            --solver=models-variable/"$net"/solver_new.prototxt -gpu all"  >> "$folder1"/"$net"-"$gpus_name".out

echo started
#pid1=$(ps -aux | grep -v root | grep "caffe train"| grep -v grep | grep -v perf | grep -v time | awk '{print $2}')
#pid1=$1
#echo caffe pid $pid1
#/home/$(whoami)/experiments/varying-gpu-number/collect-metrics/performance-counters.sh $pid1 >> $folder1/metrics/pmu-"$gpus_name".out  &

#waitcaffe $pid1
for i in $(seq 1 3); do
 echo sleeping $i
 sleep 1
done

echo The workload has finished >> "$folder1"/"$net"-"$gpus_name".out
echo finished