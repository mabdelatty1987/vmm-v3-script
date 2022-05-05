# Installing kubernetes cluster using kubespray

## preparing registry node for kubespray

1. open ssh session into node registry, and update system 

        ssh registry
        tmux
        sudo apt -y update && sudo apt -y upgrade

2. if pyhon-pip is not installed, then install it

        sudo apt -y  install python3-pip

3. Clone kubespray git

        git clone https://github.com/kubernetes-incubator/kubespray.git

4. Remove existing python3 package

        sudo apt -y remove python3-jinja2 python3-markupsafe && sudo apt autoremove -y 

4. Install the dependency module 

        cd kubespray
        sudo pip install -r requirements.txt

5. Create inventory file. you can copy the sample inventory. The following example is create inventory called mycluster from sample

        cp -rfp inventory/sample inventory/mycluster

6. Edit inventory.ini and change it to your cluster configuration (for example )

        vi inventory/mycluster/inventory.ini

        [all]
        master  ansible_host=172.16.11.10 
        node1  ansible_host=172.16.11.11 
        node2  ansible_host=172.16.11.12
        node3  ansible_host=172.16.11.13

        # ## configure a bastion host if your nodes are not directly reachable
        # [bastion]
        # bastion ansible_host=x.x.x.x ansible_user=some_user

        [kube_control_plane]
        master

        [etcd]
        master

        [kube_node]
        node1
        node2
        node3

        [calico_rr]

        [k8s_cluster:children]
        kube_control_plane
        kube_node
        calico_rr

6. Verify that on file /etc/hosts, entries for kubernetes nodes are there.
7. Verify that from node registry, it can access master, node1, node2, and node3 without using password

        ssh master
        ssh node1

7. Edit file k8s-cluster.yml to change the default configuration

        vi inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml

        container_manager: crio
        etcd_deployment_type: host
        kubelet_deployment_type: host
        enable_nodelocaldns: false
        enable_dual_stack_networks: true
        kube_network_plugin: cni   ## this is to set kubernetes cluster to generic CNI configuration, so CN2 can be installed later.
        kube_version: v1.22.3

## install kubernetes cluster

1. On node registry, run the playbook to deploy k8s cluster. It may take up to 30-60 minutes to finish

        tmux
        ansible-playbook -b -v -i inventory/mycluster/inventory.ini cluster.yml

2. Open ssh session into master node, and copy the k8s configuration into the home directory

        ssh master
        mkdir -p $HOME/.kube
        sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
        sudo chown $(id -u):$(id -g) $HOME/.kube/config

3. On the master node, verify that k8s cluster is running, but the nodes status is NOTREADY

        ubuntu@master:~$ kubectl get nodes
        NAME     STATUS     ROLES                  AGE     VERSION
        master   NotReady   control-plane,master   3m59s   v1.22.3
        node1    NotReady   <none>                 2m52s   v1.22.3
        node2    NotReady   <none>                 2m52s   v1.22.3
        node3    NotReady   <none>                 2m52s   v1.22.3
        ubuntu@master:~$ kubectl get pods -A
        NAMESPACE     NAME                              READY   STATUS    RESTARTS      AGE
        kube-system   coredns-8474476ff8-nwglz          0/1     Pending   0             2m24s
        kube-system   dns-autoscaler-5ffdc7f89d-w675s   0/1     Pending   0             2m20s
        kube-system   kube-apiserver-master             1/1     Running   1             4m11s
        kube-system   kube-controller-manager-master    1/1     Running   2 (88s ago)   4m11s
        kube-system   kube-proxy-d9rn8                  1/1     Running   0             3m10s
        kube-system   kube-proxy-j97lz                  1/1     Running   0             3m10s
        kube-system   kube-proxy-mrz7j                  1/1     Running   0             3m10s
        kube-system   kube-proxy-wddwh                  1/1     Running   0             3m10s
        kube-system   kube-scheduler-master             1/1     Running   2 (88s ago)   4m11s
        kube-system   nginx-proxy-node1                 1/1     Running   0             3m12s
        kube-system   nginx-proxy-node2                 1/1     Running   0             3m12s
        kube-system   nginx-proxy-node3                 1/1     Running   0             3m12s
        kube-system   nodelocaldns-69j86                1/1     Running   0             2m19s
        kube-system   nodelocaldns-bblwq                1/1     Running   0             2m19s
        kube-system   nodelocaldns-cn5t9                1/1     Running   0             2m19s
        kube-system   nodelocaldns-qgj48                1/1     Running   0             2m19s
        ubuntu@master:~$ 


4. Now you can continue with CN2 installation. You can follow [this document](cn2_installation.md)



