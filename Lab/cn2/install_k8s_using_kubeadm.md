# Installing kubernetes using Kubeadm

## Kubernetes cluster installation

1. copy files in directory [installk8s/](installk8s/) to node master, node1, node2, and node3

        #!/usr/bin/env bash
        for i in master node{1..3}
        do
        scp install*.sh ${i}:~/
        done
        scp ./init_k8s.sh master:~/
        scp ./kube_init.yaml master:~/

2. open ssh session into node **master**
3. Run scripts install1.sh , install2.sh and install3.sh

        ./install1.sh && ./install2.sh && ./install3.sh

6. Repeat step 3 on node **node1**, **node2**, and **node3**
7. on node **master**, initialize kubernetes cluster using kubeadm, and wait until it finish

        sudo kubeadm init --config kube_init.yaml

8. edit /var/lib/kubelet/kubeadm-flags.env, and add --node-ip=172.16.12.10 to KUBELET_KUBEADM_ARGS.

        sudo vi /var/lib/kubelet/kubeadm-flags.env

9. Restart kubelet service and verify that the Internal-IP has been changed to 172.16.12.10 (ip address on interface eth1)
        
        sudo systemctl restart kubelet.service and 
        kubectl get nodes -A -o wide
        kubectl get pods -A -o wide


8. When the kubeadm is finish, at the end, there is kubeadm join script, copy it and run it on node1, node2 and node3
9. on Node1, node2, and node3, edit file /var/lib/kubelet/kubeadm-flags.env, and add --node-ip=172.16.12.11/12/13 to KUBELET_KUBEADM_ARGS. Set the ip address accordingly on each node, and restart the kubelet.service

10. On node **master** verify that the Internal-IP address has been set to ip address of eth1 for node1, node2 and node3

        kubectl get nodes -A -o wide
        kubectl get pods -A -o wide

11. Now kubernetes cluster has been setup
12. Please continue with [this](cn2_installation.md) to install CN2 on the kubernetes cluster
