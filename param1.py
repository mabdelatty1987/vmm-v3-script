#!/usr/bin/env python3
home_dir='/vmm/data/user_disks/'
kvm_dir='/disk2/vm/'
pc_type=['pctiny','pcsmall','pcmedium','pcbig','pcxbig','pchpv1','pchpv2','bridge','cpe','paagent','ssrc','ssrr']
junos_template='junos.j2'
vm_type={
   'gw': {'ncpus' : 2,'memory':4096},
   'paagent': {'ncpus' : 1,'memory':1024},
   'pctiny': {'ncpus' : 1,'memory':4096},
   'pcsmall': {'ncpus' : 2,'memory':8192},
   'pcmedium': {'ncpus' : 2,'memory':16384},
   'pcbig': {'ncpus' : 4,'memory':32768},
   'pchpv1': {'ncpus' : 8,'memory':32768},
   'pchpv2': {'ncpus' : 4,'memory':16384},
   'pcxbig': {'ncpus' : 8,'memory':65536},
   'esxi': {'ncpus' : 8,'memory':32768},
   'vcsa': {'ncpus' : 4,'memory':16384},
   'vapp': {'ncpus' : 4,'memory':32768},
   'ssrc': {'ncpus' : 4,'memory':8192},
   'ssrr': {'ncpus' : 4,'memory':4096},
   'junos': '',
   'vspirent': {'ncpus' : 2,'memory':1024},
   'bridge': {'ncpus' : 2,'memory':2048},
   'cpe': {'ncpus' : 1,'memory':256}
}
# vm_os=['centos','ubuntu','vmx','vqfx','vsrx','evo','mx960','mx480','mx240','wrt']
vm_os=['gw','alpine','centos','ubuntu','debian','desktop','vmx','vqfx','vsrx','vex','evo','mx960','mx480','mx240','vrr','jspace','sdi','vspirent','vcsa','esxi','aos','bridge','wrt','paagent','ssr']
tmp_dir="./tmp/"
vmm_group="-g vmm-default"
esxi_ds_size=100
jnpr_dns1="66.129.233.81"
jnpr_dns2="66.129.233.82"

# config for topology
# bit 0 : ipv4
# bit 1 : ipv6
# bit 2 : iso
# bit 3 : mpls
# bit 4 : isis
# bit 5 : rsvp
# bit 6 : ldp
# bit 7 : delay measurement using RPM
# bit 8 : large mtu
mask_ipv4 = 0b1
mask_ipv6 = 0b10
mask_iso  = 0b100
mask_mpls = 0b1000
mask_isis = 0b10000
mask_rsvp = 0b100000
mask_ldp  = 0b1000000
mask_rpm  = 0b10000000
mask_mtu  = 0b100000000
mtu= 9000

