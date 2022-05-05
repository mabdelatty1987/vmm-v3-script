# This document provide information on how to install CN2 on kubernetes cluster

## Steps
1. Download CN2 manifest from [juniper website](https://support.juniper.net/support/downloads/?p=contrail-networking) and save it to node master
2. extract the files

        tar xvfz contrail-manifests-k8s-22.1.0.93.tgz

3. if the kubernetes cluster only have one/single master node, then edit the deployer.yaml, and change count for replicas of contrail control plane from 3 to 1
4. if dpdk is not used, then delete entries for vrouter dpdk
5. for vrouter object, set the virtualHostInterface gateway to 172.16.12.1
