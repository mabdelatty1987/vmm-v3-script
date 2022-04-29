sudo apt -y update 
sudo apt -y install isc-dhcp-server

cat << EOF | sudo tee /etc/dhcp/dhcpd.conf
default-lease-time 600;
max-lease-time 7200;
ddns-update-style none;
subnet 172.16.111.0 netmask 255.255.255.0 {
   range 172.16.111.11 172.16.111.100;
   option routers 172.16.111.1;
   option domain-name-servers 66.129.233.81;
}
subnet 172.16.112.0 netmask 255.255.255.0 {
   range 172.16.112.11 172.16.112.100;
   option routers 172.16.112.1;
   option domain-name-servers 66.129.233.81;
}
subnet 172.16.110.0 netmask 255.255.255.0 {
   range 172.16.110.11 172.16.110.100;
   option routers 172.16.110.1;
   option domain-name-servers 66.129.233.81;
}
EOF

sudo systemctl restart isc-dhcp-server
sudo sed -i -e '/forward/ d' /etc/sysctl.conf
cat << EOF | sudo tee -a /etc/sysctl.conf
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF

sudo sysctl -f /etc/sysctl.conf

