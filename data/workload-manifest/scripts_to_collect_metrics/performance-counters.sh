#!/bin/bash

pid=$1

/gpfs/gpfs_4mb/mamaral/perfmon2-libpfm4/perf_examples/task \
  -e PM_DATA_ALL_FROM_L2,PM_DATA_ALL_FROM_L3 \
  -e PM_DATA_ALL_FROM_LL4,PM_DATA_ALL_FROM_RL4 \
  -e PM_DATA_ALL_FROM_DL4,PM_DATA_ALL_FROM_LMEM \
  -e PM_DATA_ALL_FROM_RMEM,PM_DATA_ALL_FROM_DMEM \
  -e PM_L3_ST_PREF,PM_L3_LD_PREF \
  -e PM_L3_CO_MEM \
  -e PM_DATA_FROM_L2MISS \
  -e PM_DATA_FROM_L3MISS -p -i -t $pid
