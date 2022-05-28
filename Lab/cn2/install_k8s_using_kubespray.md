# Installing kubernetes cluster using kubespray

Documentation on kubspray for kubernetes installation can be found [here](https://kubernetes.io/docs/setup/production-environment/tools/kubespray/) and [here](https://github.com/kubernetes-sigs/kubespray)

## preparing node registry for kubespray

1. open ssh session into node registry, and update system 

        ssh registry
        tmux
        sudo apt -y update && sudo apt -y upgrade

2. if pyhon-pip is not installed, then install it

        sudo apt -y  install python3-pip

3. Clone kubespray git

        git clone https://github.com/kubernetes-incubator/kubespray.git

4. Remove existing python3 package

        sudo apt -y remove python3-jinja2 python3-markupsafe python3-cryptograph && sudo apt autoremove -y 

4. Install the dependency module 

        cd kubespray
        sudo pip install -r requirements.txt

5. Create inventory file. you can copy the sample inventory. The following example is create inventory called mycluster from sample

        cp -rfp inventory/sample inventory/mycluster

6. Edit inventory.ini and change it to your cluster configuration (for example )

        vi inventory/mycluster/inventory.ini

        or 
        
        cat << EOF | tee inventory/mycluster/inventory.ini
        [all]
        master  ansible_host=172.16.11.10  ip=172.16.12.10  ## ip address 172.16.11.10 (eth0) is management IP and 172.16.12.10 (eth1) is used for kubernetes services 
        node1   ansible_host=172.16.11.11  ip=172.16.12.11  ## ip address 172.16.11.11 (eth0) is management IP and 172.16.12.11 (eth1) is used for kubernetes services 
        node2   ansible_host=172.16.11.12  ip=172.16.12.12  ## ip address 172.16.11.12 (eth0) is management IP and 172.16.12.12 (eth1) is used for kubernetes services 
        node3   ansible_host=172.16.11.13  ip=172.16.12.13  ## ip address 172.16.11.13 (eth0) is management IP and 172.16.12.13 (eth1) is used for kubernetes services 

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
        EOF


6. Verify that on file /etc/hosts, entries for kubernetes nodes are there.
7. Verify that from node registry, it can access master, node1, node2, and node3 without using password

        ssh master
        ssh node1

7. Edit file k8s-cluster.yml to change the default configuration

        vi inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml

        container_manager: crio                 ## default is containerd
        etcd_deployment_type: host              ## this line is not there on the original file
        kubelet_deployment_type: host           ## this line is not there on the original file
        enable_nodelocaldns: false              ## default is true
        enable_dual_stack_networks: true        ## default is false
        kube_network_plugin: cni                ## this is to set kubernetes cluster to generic CNI configuration, so CN2 can be installed later.
        kube_version: v1.23.2                   ## this is the latest stable version of kubelet that match with the latest version of crio
        cluster_name: k8s                       ## default cluster is cluster.local, you can change it to something else, i.e k8s

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
        master   NotReady   control-plane,master   3m20s   v1.23.2
        node1    NotReady   <none>                 2m12s   v1.23.2
        node2    NotReady   <none>                 2m12s   v1.23.2
        node3    NotReady   <none>                 2m12s   v1.23.2
        ubuntu@master:~$ kubectl get pods -A
        NAMESPACE     NAME                              READY   STATUS    RESTARTS      AGE
        kube-system   coredns-76b4fb4578-qmjjh          0/1     Pending   0             93s
        kube-system   dns-autoscaler-7979fb6659-hxplg   0/1     Pending   0             89s
        kube-system   kube-apiserver-master             1/1     Running   1             3m26s
        kube-system   kube-controller-manager-master    1/1     Running   2 (36s ago)   3m26s
        kube-system   kube-proxy-g7dsl                  1/1     Running   0             2m17s
        kube-system   kube-proxy-vpdr2                  1/1     Running   0             2m17s
        kube-system   kube-proxy-vxqk6                  1/1     Running   0             2m17s
        kube-system   kube-proxy-wdvth                  1/1     Running   0             2m17s
        kube-system   kube-scheduler-master             1/1     Running   2 (38s ago)   3m26s
        kube-system   nginx-proxy-node1                 1/1     Running   0             2m19s
        kube-system   nginx-proxy-node2                 1/1     Running   0             2m19s
        kube-system   nginx-proxy-node3                 1/1     Running   0             2m19s
        ubuntu@master:~$


4. Now you can continue with CN2 installation. You can follow [this document](cn2_installation.md)



