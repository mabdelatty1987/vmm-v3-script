# Creating container image for the lab exercise

1. Upload  file [webserver.tgz](webserver.tgs) into node **registry**

        scp webserver.tgz registry:~/

3. open ssh session into node registry, and extract file webserver.tgz

        ssh registry
        tar xvpfz webserver.tgz 


4. Create container image using 

        cd webserver
        podman build -t 172.16.14.10:50000/webserver:0.1 .

5. Verify that container image has been create

        podman image ls

7. Push the container image into private registry

        podman push 172.16.14.10:5000/webserver:0.1
        
8. Verify that container image has been pushed into private registry

        curl -k https://172.16.14.10:5000/v2/_catalog
        curl -k https://172.16.14.10:5000/v2/webserver/tags/list