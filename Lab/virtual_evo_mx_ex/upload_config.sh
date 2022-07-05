#!/bin/bash
for i in ce1 ce2 p1 p2
do
  scp tmp/${i}.conf ${i}:~/
done
