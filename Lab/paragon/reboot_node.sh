#!/bin/bash
for i in node{0..3}
do
ssh ${i} "sudo reboot"
done
