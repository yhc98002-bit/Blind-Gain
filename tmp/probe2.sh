#!/bin/bash
for N in an12 an29; do
  echo "############ $N"
  ssh -o ConnectTimeout=20 $N 'hostname; date -u; echo "--- verl trainers ---"; ps -eo pid,ppid,etime,user,args | grep -E "verl.trainer.mai[n]" | sed -e "s/--/\n    --/g" | head -80; echo "--- compute apps ---"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader; echo "--- uuid map ---"; nvidia-smi --query-gpu=index,uuid --format=csv,noheader'
done
