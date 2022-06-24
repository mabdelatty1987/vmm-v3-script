#!/bin/sh
echo "
127.0.0.1 localhost
::1 ip6-localhost ip6-loopback
172.16.11.100 deployer
172.16.11.101 radius
172.16.11.110 node0
172.16.11.111 node1
172.16.11.112 node2
172.16.11.113 nfs
172.16.11.115 acs1
127.0.1.1 acs1 
" | sudo tee /etc/hosts
sudo hostname acs1
hostname | sudo tee /etc/hostname
mkdir ~/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC/+8rkgOc76z0m7Cierw4qUs6bahYgQP4/hyPZGmb/mukCSn7ZvbUM27fX1nRbbP8Z0t+ruF8A5kP5jHOXILCTe2K5+JE9aHbkae5ztSwhxZSYxcSPtN0r8G/B57/4cw5QV7yKjSlQiLXf2EMfIt27/ZGeE402Tntz5v41wsj8C9PtBZvSMcgBWYu/HfE94ShSqsUNvg+FzKaVGhPB4mOzsApPF7Y/zopk7ADB6VkBdqUSblauU0a4aDy/3cwGR2NwOGXcszGzNYU4H6AlIsribpQPXkVs/v6b4NRHzAuKVk2FLLneeWsEKIqCZIWjzJj2ck4aWCM3NkoE86ndbRNyFaaxs67KpzPvPlAOwHU8gINyhzDfVi68xeiN9p8ybj3fI/Vw1W70i4wN2rL1PSupnnPNAX0Ijd9ulmhbAJyO+cjuoURLUR56EjJUYfddzRRRjQO0IMKNPDw0BFFxbt4gc1OnC6bJh2odHb/xbXaVCo361kz2IBoeZ3yFVpTcJH8= irzan@irzan-mbp" | tee .ssh/authorized_keys
echo "-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----" | tee .ssh/id_rsa
chmod og-rwx .ssh/id_rsa
sudo rm /etc/network/interface
echo "
auto lo
interface lo inet loopback
auto eth0
interface eth0 inet static
  address 172.16.11.115/24
auto eth1
interface eth1 inet manual
  mtu 9000
auto eth2
interface eth2 inet manual
  mtu 9000
auto eth3
interface eth3 inet manual
  mtu 9000
auto eth4
interface eth4 inet manual
  mtu 9000
auto eth5
interface eth5 inet manual
  mtu 9000
auto eth6
interface eth6 inet manual
  mtu 9000
auto eth7
interface eth7 inet manual
  mtu 9000
auto eth8
interface eth8 inet manual
  mtu 9000
auto bracs
interface bracs inet manual
  post-up echo 0x4000 > /sys/class/net/bracs/bridge/group_fwd_mask
  bridge-ports eth1 eth2 eth3 eth4 eth5 eth6 eth7 eth8 
  bridge-stp 0
" | sudo tee /etc/network/interfaces
echo "Host *
   StrictHostKeyChecking no
"| tee ~/.ssh/config

sleep 2
sudo reboot
