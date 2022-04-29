#!/bin/bash
REGISTRY_USER=JNPR-FieldUser5
REGISTRY_PASSWORD=SjvBqx3ktFuWVC4REX7y
CONTAINER_TAG=21.3.1.98
docker login hub.juniper.net --username ${REGISTRY_USER} --password ${REGISTRY_PASSWORD}
docker pull hub.juniper.net/contrail/contrail-command-deployer:${CONTAINER_TAG}
