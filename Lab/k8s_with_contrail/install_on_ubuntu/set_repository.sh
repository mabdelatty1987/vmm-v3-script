username=JNPR-FieldUser5
password=SjvBqx3ktFuWVC4REX7y
kubectl create secret docker-registry contrail-registry --docker-server=hub.juniper.net/contrail --docker-username=${username} --docker-password=${password} --docker-email=irzan@juniper.net -n kube-system

