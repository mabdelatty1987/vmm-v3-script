# How to setup kubectl over ssh tunnel

Information on how to set kubectl over ssh, can be found here [reference](https://blog.scottlowe.org/2019/07/30/adding-a-name-to-kubernetes-api-server-certificate/)

1. on Master, run 

        kubectl -n kube-system get configmap kubeadm-config -o jsonpath='{.data.ClusterConfiguration}' > kubeadm.yaml

2. edit file kubeadmin, under **apiServer:** add the following:

        apiServer:
                certSANs:
                - "127.0.0.1"
                - "172.16.12.10"
                - "10.96.0.1"

3. Move the existing API server certificate to different directory

        mkdir ~/certs
        sudo mv /etc/kubernetes/pki/apiserver.{crt,key} ./certs

4. run kubedm to generate a new certificate

        sudo kubeadm init phase certs apiserver --config kubeadm.yaml

5. Restart the API server container :
    - run **sudo crictl ps | grep kube-apiserver | grep -v pause** to get the containerID of the kubernetes API server
    - run **sudo crictl update <containerID>** to restart it.

6. copy kubectl config from node **master** to your local workstation

        mkdir ~/.kube
        scp master:~/.kube/config ~/.kube/config
        
7. On your workstation, edit file ~/.kube/config. Change the URL from https://172.16.12.10:6443 to https://127.0.0.1:6443

        sed -i -e 's/172.16.12.10/127.0.0.1/' ~/.kube/config

7. Open ssh session with port forwarding on 6443 to node **master** (and keep the session alive)

        ssh -L 6443:127.0.0.1:6443 master

8. Install kubectl on your workstation, and test kubectl command

        kubectl get nodes
        kubectl get pods --all-namespaces

9. Now you can run kubectl on your workstation to access the kubernetes cluster in the lab.

10. For lab exercise, you can follow the following [this lab guide](lab_exercise/README.md)