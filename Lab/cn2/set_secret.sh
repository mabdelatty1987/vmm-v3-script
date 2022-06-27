kubectl create ns contrail
kubectl create ns contrail-system
kubectl create ns contrail-deploy
kubectl create ns contrail-analytics
kubectl create secret docker-registry registrypullsecret --docker-server=hub.juniper.net --docker-username=${HUB_USER} --docker-password=${HUB_PASSWD} --docker-email=irzan@juniper.net -n contrail
kubectl create secret docker-registry registrypullsecret --docker-server=hub.juniper.net --docker-username=${HUB_USER} --docker-password=${HUB_PASSWD} --docker-email=irzan@juniper.net -n contrail-system
kubectl create secret docker-registry registrypullsecret --docker-server=hub.juniper.net --docker-username=${HUB_USER} --docker-password=${HUB_PASSWD} --docker-email=irzan@juniper.net -n contrail-deploy
kubectl create secret docker-registry registrypullsecret --docker-server=hub.juniper.net --docker-username=${HUB_USER} --docker-password=${HUB_PASSWD} --docker-email=irzan@juniper.net -n contrail-analytics

