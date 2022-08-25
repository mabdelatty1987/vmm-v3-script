#!/usr/bin/env python3
# this library is used to create configuration files to run VM (Centos/Ubuntu) and Junos (VMX/VQFX) on VMM (juniper internal cloud)
# created by mochammad irzan irzan@juniper.net
# 20 october 2019

# 24 July 2021, updated for VMM 3.0 (not backward compatible with previous version of VMM)

#from re import L
import param1
#import sys
import os
import shutil
import paramiko
import time
import pathlib
from jinja2 import Template
import shutil
from pathlib import Path
import yaml
import pexpect
import pprint
from scp import SCPClient
#import json
 
# from jnpr.junos import Device
# from jnpr.junos.utils.config import Config

from passlib.hash import md5_crypt

def print_data(d1):
	print("printing data")
	print("-------------")
	print(yaml.dump(d1))

def read_config(config):
	d1={}
	config_file = config['config_file']
	try:
		f1=open(config_file)
		d1=yaml.load(f1,Loader=yaml.FullLoader)
		f1.close()
		add_ssh_key(d1)
		add_path(d1,config['path'])
		if 'fabric' in d1.keys():
			num_link = len(d1['fabric']['topology'])
			pref_len = 32 - int(d1['fabric']['subnet'].split('/')[1])
			num_subnet = int( (2 **  pref_len) / 2)		
			if num_link > num_subnet:
				print("not enough ip address for fabric link\nnum of link %d, num of subnet %d " %(num_link,num_subnet))
				d1={}
			elif check_ip(d1):
				print("wrong subnet allocation")
				print("subnet %s can't be used with prefix %s" %(d1['fabric']['subnet'].split('/')[0],d1['fabric']['subnet'].split('/')[1]))
			#elif not check_vm(d1):
			#	print("number of VM on topology doesn't match with on configuration")
			else:
				create_config_interfaces(d1)
		change_gateway4(d1)
		adpassword_env=os.getenv('ADPASSWORD')
		user_env=os.getenv('USER')
		if adpassword_env:
			d1['pod']['adpassword'] = adpassword_env
		if not d1['pod']['user']:
			d1['pod']['user']=user_env
		#if not d1['']
		
	except FileNotFoundError:
		print("where is the file")
	except PermissionError:
		print("Permission error")
	
	return(d1)

def change_gateway4(d1):
	for i in d1['vm'].keys():
		if d1['vm'][i]['os'] in ['ubuntu','ubuntu2','desktop']:
			for j in d1['vm'][i]['interfaces'].keys():
				if 'family' in d1['vm'][i]['interfaces'][j].keys():
					if 'inet' in d1['vm'][i]['interfaces'][j]['family'].keys():
						#print(f"host {i} {d1['vm'][i]['interfaces'][j]['family'].keys()}")
						#if 'gateway4' in d1['vm'][i]['interfaces'][j]['family']['inet'].keys():
						#if 'gateway4' in d1['vm'][i]['interfaces'][j].keys():
						if 'gateway4' in d1['vm'][i]['interfaces'][j]['family'].keys():
							if 'static' in d1['vm'][i]['interfaces'][j]['family'].keys():
								#d1['vm'][i]['interfaces'][j]['static'].append({'to':'default','via':j['gateway4']})
								d1['vm'][i]['interfaces'][j]['family']['static'].append({'to':'0.0.0.0/0','via':d1['vm'][i]['interfaces'][j]['gateway4']})
							else:
								#d1['vm'][i]['interfaces'][j]['static']=[{'to':'default','via': d1['vm'][i]['interfaces'][j]['gateway4']}]
								d1['vm'][i]['interfaces'][j]['family']['static']=[{'to':'0.0.0.0/0','via': d1['vm'][i]['interfaces'][j]['family']['gateway4']}]
							d1['vm'][i]['interfaces'][j]['family'].pop('gateway4')
							

def create_config_interfaces(d1):
	num_link = len(d1['fabric']['topology'])
	b1,b2,b3,b4 = d1['fabric']['subnet'].split('/')[0].split('.')
	start_ip = (int(b1) << 24) + (int(b2) << 16) + (int(b3) << 8) + int(b4)
	for i in range(num_link):
		br='ptp' + str(i)
		d1['fabric']['topology'][i].append(br)
		if d1['fabric']['topology'][i][0]:
			if d1['fabric']['topology'][i][0] & param1.mask_ipv4:
				d1['fabric']['topology'][i].append(bin2ip(start_ip))
				start_ip += 1
				d1['fabric']['topology'][i].append(bin2ip(start_ip))
				start_ip += 1
			else:
				d1['fabric']['topology'][i].append('0')
				d1['fabric']['topology'][i].append('0')
	list_vm = list_vm_from_fabric(d1)
	#print(list_vm)
	d2={'vm': {} }
	for i in list_vm:
		d2['vm'].update({i : {'interfaces': {}}})
		for j in d1['fabric']['topology']:
			if j[1] == i:
				d2['vm'][i]['interfaces'].update( {j[2]: {'bridge' : j[5]} })
				if j[0] & param1.mask_ipv4:
					if 'family' not in d2['vm'][i]['interfaces'][j[2]].keys():
						d2['vm'][i]['interfaces'][j[2]].update({'family' : {'inet': j[6]}})
					else:
						d2['vm'][i]['interfaces'][j[2]]['family'].update({'inet': j[6]})
					if j[0] & param1.mask_iso:
						if 'family' not in d2['vm'][i]['interfaces'][j[2]].keys():
							d2['vm'][i]['interfaces'][j[2]].update({'family' : {'iso':None}})
						else:
							d2['vm'][i]['interfaces'][j[2]]['family'].update({'iso':None})
						if j[0] & param1.mask_isis:
							if 'protocol' not in d2['vm'][i]['interfaces'][j[2]].keys():
								d2['vm'][i]['interfaces'][j[2]].update({'protocol' : {'isis':'ptp'}})
							else:
								d2['vm'][i]['interfaces'][j[2]]['protocol'].update({'isis':'ptp'})
					if j[0] & param1.mask_mpls:
						if 'family' not in d2['vm'][i]['interfaces'][j[2]].keys():
							d2['vm'][i]['interfaces'][j[2]].update({'family' : {'mpls':None}})
						else:
							d2['vm'][i]['interfaces'][j[2]]['family'].update({'mpls':None})
						if j[0] & param1.mask_rsvp:
							if 'protocol' not in d2['vm'][i]['interfaces'][j[2]].keys():
								d2['vm'][i]['interfaces'][j[2]].update({'protocol' : {'rsvp':None}})
							else:
								d2['vm'][i]['interfaces'][j[2]]['protocol'].update({'rsvp':None})
						if j[0] & param1.mask_ldp:
							if 'protocol' not in d2['vm'][i]['interfaces'][j[2]].keys():
								d2['vm'][i]['interfaces'][j[2]].update({'protocol' : {'ldp':None}})
							else:
								d2['vm'][i]['interfaces'][j[2]]['protocol'].update({'ldp':None})
					if j[0] & param1.mask_rpm:
						src = d2['vm'][i]['interfaces'][j[2]]['family']['inet'].split('/')[0]
						dst = calc_target(src)
						if 'rpm' not in d2['vm'][i]['interfaces'][j[2]].keys():
							d2['vm'][i]['interfaces'][j[2]].update({'rpm' : {'source': src, 'destination': dst } })
						else:
							d2['vm'][i]['interfaces'][j[2]]['rpm'] = {'source': src, 'destination': dst }
				if j[0] & param1.mtu:
					if 'mtu' not in d2['vm'][i]['interfaces'][j[2]].keys():
						d2['vm'][i]['interfaces'][j[2]].update({'mtu' : param1.mtu  })
					else:
						d2['vm'][i]['interfaces'][j[2]]['mtu'] = param1.mtu
			elif j[3] == i:
				d2['vm'][i]['interfaces'].update({j[4]: {'bridge' : j[5]} })
				if j[0] & param1.mask_ipv4:
					if 'family' not in d2['vm'][i]['interfaces'][j[4]].keys():
						d2['vm'][i]['interfaces'][j[4]].update({'family' : {'inet': j[7]}})
					else:
						d2['vm'][i]['interfaces'][j[4]]['family'].update({'inet': j[7]})
					if j[0] & param1.mask_iso:
						if 'family' not in d2['vm'][i]['interfaces'][j[4]].keys():
							d2['vm'][i]['interfaces'][j[4]].update({'family' : {'iso':None}})
						else:
							d2['vm'][i]['interfaces'][j[4]]['family'].update({'iso':None})
						if j[0] & param1.mask_isis:
							if 'protocol' not in d2['vm'][i]['interfaces'][j[4]].keys():
								d2['vm'][i]['interfaces'][j[4]].update({'protocol' : {'isis':'ptp'}})
							else:
								d2['vm'][i]['interfaces'][j[4]]['protocol'].update({'isis':'ptp'})

					if j[0] & param1.mask_mpls:
						if 'family' not in d2['vm'][i]['interfaces'][j[4]].keys():
							d2['vm'][i]['interfaces'][j[4]].update({'family' : {'mpls':None}})
						else:
							d2['vm'][i]['interfaces'][j[4]]['family'].update({'mpls':None})
					
						if j[0] & param1.mask_rsvp:
							if 'protocol' not in d2['vm'][i]['interfaces'][j[4]].keys():
								d2['vm'][i]['interfaces'][j[4]].update({'protocol' : {'rsvp':None}})
							else:
								d2['vm'][i]['interfaces'][j[4]]['protocol'].update({'rsvp':None})
						if j[0] & param1.mask_ldp:
							if 'protocol' not in d2['vm'][i]['interfaces'][j[4]].keys():
								d2['vm'][i]['interfaces'][j[4]].update({'protocol' : {'ldp':None}})
							else:
								d2['vm'][i]['interfaces'][j[4]]['protocol'].update({'ldp':None})
					if j[0] & param1.mask_rpm:
						src = d2['vm'][i]['interfaces'][j[4]]['family']['inet'].split('/')[0]
						dst = calc_target(src)
						if 'rpm' not in d2['vm'][i]['interfaces'][j[4]].keys():
							d2['vm'][i]['interfaces'][j[4]].update({'rpm' : {'source': src, 'destination': dst } })
						else:
							d2['vm'][i]['interfaces'][j[4]]['rpm'] = {'source': src, 'destination': dst }
				if j[0] & param1.mtu:
					if 'mtu' not in d2['vm'][i]['interfaces'][j[4]].keys():
						d2['vm'][i]['interfaces'][j[4]].update({'mtu' : param1.mtu  })
					else:
						d2['vm'][i]['interfaces'][j[4]]['mtu'] = param1.mtu

	for i in d2['vm'].keys():
		intf = d2['vm'][i]['interfaces']
		d1['vm'][i]['interfaces'].update(intf)	
	#print(d2)
	for i in d1['vm'].keys():
		if d1['vm'][i]['type']=='bridge':
			list_intf=list(d1['vm'][i]['interfaces'].keys())
			#print(list_intf)
			_ = list_intf.pop(0)
			#print(list_intf)
			for j in list_intf:
				node_tmp1 = d1['vm'][i]['interfaces'][j]['node']
				#print(node_tmp1)
				n1 = d1['vm'][i]['interfaces'][j]['node'][0]
				n1_intf = d1['vm'][i]['interfaces'][j]['node'][1]
				d1['vm'][i]['interfaces'][j] = {'bridge' : i + j}
				d1['vm'][n1]['interfaces'][n1_intf]['bridge']=d1['vm'][i]['interfaces'][j]['bridge']
				d1['vm'][i]['interfaces'][j]['node'] = node_tmp1


def calc_target(src_ip):
	ip_byte = src_ip.split('.')
	if int(ip_byte[3]) % 2:
		ip_byte[3]=str(int(ip_byte[3])-1)
	else:
		ip_byte[3]=str(int(ip_byte[3])+1)
	return '.'.join(ip_byte)

def list_vm_from_fabric(d1):
	junos_vm_f1= []
	for i in d1['fabric']['topology']:
		if i[1] not in junos_vm_f1:
			junos_vm_f1.append(i[1])
		if i[3] not in junos_vm_f1:
			junos_vm_f1.append(i[3])
	return junos_vm_f1

def bin2ip(ipbin):
	m1 = 255<<24
	m2 = 255<<16
	m3 = 255 << 8
	m4 = 255
	b1=str((ipbin & m1) >> 24)
	b2=str((ipbin & m2) >> 16)
	b3=str((ipbin & m3) >> 8)
	b4=str(ipbin & m4)
	retval = '.'.join((b1,b2,b3,b4)) + "/31"
	#print(retval)
	return retval


def check_ip(d1):
	preflen = 32 - int(d1['fabric']['subnet'].split('/')[1])
	mask_ip = int(2** preflen - 1) 
	b1,b2,b3,b4 = d1['fabric']['subnet'].split('/')[0].split('.')
	ip_int = (int(b1) << 24) + (int(b2) << 16) + (int(b3) << 8) + int(b4)
	#print("ip int : ",bin(ip_int))
	#print("mask   : ",bin(mask_ip))
	retval = ip_int & mask_ip
	#print("retval = ",retval)
	return retval

def check_vm(d1):
	junos_vm_d1 = []
	for i in d1['vm'].keys():
		if d1['vm'][i]['type'] in ['junos','veos']:
			if i not in junos_vm_d1:
				junos_vm_d1.append(i)
	junos_vm_f1= list_vm_from_fabric(d1)
	return set(junos_vm_f1).issubset(set(junos_vm_d1))

def add_ssh_key(d1):
	if 'ssh_key_name' in d1['pod'].keys():
		key_file = str(pathlib.Path.home()) + "/.ssh/" + d1['pod']['ssh_key_name'] + ".pub"
		key_file_priv = str(pathlib.Path.home()) + "/.ssh/" + d1['pod']['ssh_key_name']
	else:
		key_file = str(pathlib.Path.home()) + "/.ssh/id_rsa.pub"
		key_file_priv = str(pathlib.Path.home()) + "/.ssh/id_rsa"
	f=open(key_file)
	ssh_key = f.read()
	f.close()
	d1['pod']['ssh_key']=ssh_key.strip()
	f=open(key_file_priv)
	ssh_key_priv = f.read()
	f.close()
	d1['pod']['ssh_key_priv']=ssh_key_priv.strip()

def add_path(d1,path):
	d1['pod']['path']=path

def get_private_ip_gw(d1):
	for i in d1['vm'].keys():
		if d1['vm'][i]['type']=="gw":
			for j in d1['vm'][i]['interfaces'].keys():
				if d1['vm'][i]['interfaces'][j]['bridge']=="mgmt":
					retval= d1['vm'][i]['interfaces'][j]['family']['inet'].split("/")[0]
	return retval

def print_syntax():
	print("usage : vmm.py <command>")
	print("commands are : ")
	print("  upload : to upload configuration to vmm pod ")
	print("  start  : to start VM in the vmm pod")
	print("  stop   : to stop in the vmm pod")
	print("  list   : list of running VM")
	#print("  get_serial : get serial information of the vm")
	#print("  get_vga : get vga information of the vm (for vnc)")
	#print("  get_ip  : get IP information of the vm")
	print("  set_gw  : setting gateway configuration")
	print("  set_host  : setting ubuntu/centos configuration")
	print("  init_junos  : initial configuration for vEX and vEVO")
	#print("  config_junos  : push configuration for vEX and vEVO")
	print("if configuration file is not specified, then file lab.yaml must be present")

def check_argv(argv):
	retval={}
	cmd_list=['upload','start','stop','get_serial','get_vga','get_ip','list','config','test','init_junos','config_junos']
	if len(argv) == 1:
		print_syntax()
	else:
		if not os.path.isfile("./lab.yaml"):
			print("file lab.conf doesn't exist, please create one or define another file for configuration")
		else:
			retval['config_file']="lab.yaml"
			retval['cmd']=argv[1]
			t1 = argv[0].split("/")
			path=""
			for i in list(range(2)):
				path += t1[i] + "/"
			#print("path ",path)
			retval['path']=path
			if retval['cmd'] == 'get_ip':
				if len(argv)==2:
					print("get_ip requires VM information")
					retval={}
				elif len(argv)==3:
					retval['vm'] = argv[2]
			elif retval['cmd'] == 'get_vga': 
				if len(argv)==3:
					retval['vm'] = argv[2]
				else:
					retval['vm'] = ""
			elif retval['cmd'] == 'get_serial': 
				if len(argv)==3:
					retval['vm'] = argv[2]
				else:
					retval['vm'] = ""
			elif retval['cmd'] == 'init_junos': 
				#print(f"len {len(argv)}")
				if len(argv)==3:
					retval['vm'] = argv[2]
				else:
					retval['vm']= False

	return retval

def checking_config_syntax(d1):
	retval=1
	# checking type and os
	for i in d1['vm'].keys():
		# checking vm type
		if not d1['vm'][i]['type'] in param1.vm_type:
			print("ERROR for VM ",i)
			print("this type of VM, " + d1['vm'][i]['type'] + " is not supported yet")
			return 0
		if not d1['vm'][i]['os'] in param1.vm_os:
			print("ERROR for VM ",i)
			print("this OS " + d1['vm'][i]['os'] + " is not supported yet")
			return 0
	# checking interface
	for i in d1['vm'].keys():
		if (d1['vm'][i]['type'] in param1.vm_type.keys()) and (d1['vm'][i]['type'] not in ['junos','veos']):
			for j in d1['vm'][i]['interfaces'].keys():
				if 'em' not in j:
					print("ERROR for VM ",i)
					print("interface " + j + " is not supported")
					return 0
			for j in d1['vm'][i]['interfaces'].keys():
				if list(d1['vm'][i]['interfaces'].keys()).count(j) > 1:
					print("ERROR for VM ",i)
					print("duplicate interfaces " + j + " is found")
					return 0
	return retval

def get_ip(d1,vm):
	if d1['pod']['type'] == 'vmm':
		ssh=ƒ(d1)
		#print('-----')
		#print(" of VM")
		cmd1="vmm list"
		s1,s2,s3=ssh.exec_command(cmd1)
		vm_list=[]
		for i in s2.readlines():
			vm_list.append(i.rstrip().split()[0])
		if vm not in vm_list:
			print(" VM {} does not exists ".format(vm))	
		else:
			print("VM %s %s " %(vm,get_ip_vm(d1,vm)))
		ssh.close()
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")



def sshconnect(d1):
	if 'jumpserver' in d1['pod'].keys():
		jumphost=paramiko.SSHClient()
		jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		jumphost.connect(hostname=d1['pod']['jumpserver'],username=d1['pod']['user'],password=d1['pod']['adpassword'])
		jumphost_transport=jumphost.get_transport()
		src_addr=(d1['pod']['jumpserver'],22)
		dest_addr=(d1['pod']['vmmserver'],22)
		jumphost_channel = jumphost_transport.open_channel("direct-tcpip", dest_addr, src_addr)
		ssh=paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		# ssh.connect(hostname=d1['pod']['vmmserver'],username=d1['pod']['user'],password=d1['pod']['unixpassword'],sock=jumphost_channel)
		ssh.connect(hostname=d1['pod']['vmmserver'],username=d1['pod']['user'],password=d1['pod']['adpassword'],sock=jumphost_channel)
	else:
		ssh=paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(hostname=d1['pod']['vmmserver'],username=d1['pod']['user'],password=d1['pod']['adpassword'])
	return ssh

def connect_to_gw(d1):
	if not 'gw_ip' in d1.keys():
		d1['gw_ip'] = get_ip_vm(d1,'gw')
	user_id = get_ssh_user(d1,'gw').strip().split()[1]
	passwd='pass01'
	if 'jumpserver' in d1['pod'].keys():
		jumphost=paramiko.SSHClient()
		jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		jumphost.connect(hostname=d1['pod']['jumpserver'],username=d1['pod']['user'],password=d1['pod']['adpassword'])
		jumphost_transport=jumphost.get_transport()
		src_addr=(d1['pod']['jumpserver'],22)
		dest_addr=(d1['gw_ip'],22)
		jumphost_channel = jumphost_transport.open_channel("direct-tcpip", dest_addr, src_addr)
		ssh=paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		# ssh.connect(hostname=d1['pod']['vmmserver'],username=d1['pod']['user'],password=d1['pod']['unixpassword'],sock=jumphost_channel)
		ssh.connect(hostname=d1['gw_ip'],username=user_id,password=passwd,sock=jumphost_channel)
	else:
		ssh=paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(hostname=d1['gw_ip'],username=user_id,password=passwd)
	return ssh

def get_mgmt_ip(d1,i):
	if d1['vm'][i]['type']=='junos':
		ip_vm = d1['vm'][i]['interfaces']['mgmt']['family']['inet'].split('/')[0]
	else:
		ip_vm = d1['vm'][i]['interfaces']['em0']['family']['inet'].split('/')[0]
	return ip_vm

def get_user(d1,i):
	if d1['vm'][i]['type']=='junos':
		user_id = d1['junos_login']['login']
		passwd = d1['junos_login']['password']
	elif d1['vm'][i]['os'] in ['ubuntu','ubuntu2']:
		user_id = 'ubuntu'
		passwd = 'pass01'
	elif d1['vm'][i]['os']=='desktop':
		user_id = 'ubuntu'
		passwd = 'pass01'
	elif d1['vm'][i]['os']=='centos':
		user_id = 'centos'
		passwd = 'pass01'
	elif d1['vm'][i]['os']=='debian':
		user_id = 'debian'
		passwd = 'pass01'
	elif d1['vm'][i]['os']=='alpine':
		user_id = 'alpine'
		passwd = 'pass01'
	elif d1['vm'][i]['os']=='bridge':
		user_id = 'alpine'
		passwd = 'pass01'
	else:
		user_id = 'admin'
		passwd = 'pass01'

	return user_id,passwd

def get_vga(d1,vm=""):
	if d1['pod']['type'] == 'vmm':
		print("get_vga , vm ",vm)
		print('-----')
		ssh=sshconnect(d1)
		cmd1="vmm list"
		s1,s2,s3=ssh.exec_command(cmd1)
		vm_list=[]
		for i in s2.readlines():
			vm_list.append(i.rstrip().split()[0])	
		ssh.close()
		if vm != "":
			if vm not in vm_list:
				print("VM %s does not exist " %(vm))
			else:
				print_vga(d1,vm)
		else:
			for i in vm_list:
				print_vga(d1,i)
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")
			

def get_vncinfo(d1,vm):
	ssh=sshconnect(d1)
	cmd1="vmm args " + vm + " | grep \" vnc \""
	s1,s2,s3=ssh.exec_command(cmd1)
	#print("host ",vm)
	vnc_server = "VGA port is disabled "
	for j in s2.readlines():
		if j.strip().split()[1] == 'none':
			vnc_server = "VGA port is disabled "
		else:
			vnc_server =  j.strip().split()[1]
			# vnc_port = int(j.rstrip().split()[1].split(':')[1]) + 5900 
	ssh.close()
	return vnc_server

def print_vga(d1,vm):
	print("VGA port of " + vm + " -> " + get_vncinfo(d1,vm))


def get_ip_vm(d1,i):
	if d1['pod']['type'] == 'vmm':
		ssh=sshconnect(d1)
		cmd1="vmm args " + i + " | grep \" ip \""
		xxx=''''''
		stdin,stdout,sstderr=ssh.exec_command(cmd1)
		j = stdout.readlines()
		ssh.close()
		_,retval= j[0].rstrip().split()
		if retval == 'None':
			retval = "No External IP"
		return retval
	elif d1['pod']['type'] == 'kvm':
		print("not implemented for this type")
		return ""

def get_hosts_config(d1):
	host_yes=['centos','ubuntu','ubuntu2','debian','esxi','aos','aos_ztp','bridge','desktop']
	host_config=['127.0.0.1 localhost','::1 ip6-localhost ip6-loopback']
	for i in d1['vm'].keys():
		if d1['vm'][i]['os'] in host_yes:
			for j in d1['vm'][i]['interfaces'].keys():
				#print(f"HOST {i}, Interfaces {j}")
				if 'family' in d1['vm'][i]['interfaces'][j].keys():
					if 'inet' in d1['vm'][i]['interfaces'][j]['family'].keys():
						ipaddr=d1['vm'][i]['interfaces'][j]['family']['inet'].split('/')[0]
						host_config.append("{} {}".format(ipaddr,i))
	return host_config

def get_dhcp_config(d1):
	dhcp_yes=['centos','ubuntu','ubuntu2','debian','esxi','aos','aos_ztp','bridge','desktop','paagent']
	ssh=sshconnect(d1)
	cmd1="vmm args "
	stdin,stdout,sstderr=ssh.exec_command(cmd1)
	j = stdout.readlines()
	ssh.close()
	k=[]
	k_item=[]
	c1=0
	for i in j:
		if i.strip() !="":
			k.append(i.strip())
	for i in k:
		if '==' in i:
			k_item.append(c1)
		c1+=1
	#print("daftar ",k_item)
	vm_mac={}
	for i in k_item:
		_,h1,_=k[i].split()
		j=i
		while True:
			j+=1
			if 'mac' in k[j]:
				break

		# print("host ",h1,k[j].split()[1])
		vm_mac[h1]={'mac': k[j].split()[1]}
	#print(vm_mac)
	vm_mac2={}
	for i in vm_mac.keys():
		if i in d1['vm'].keys():
			if d1['vm'][i]['os'] in dhcp_yes:
				if 'family' in d1['vm'][i]['interfaces']['em0'].keys():
					if 'inet' in d1['vm'][i]['interfaces']['em0']['family'].keys():
						vm_mac2[i]={'mac' : vm_mac[i]['mac'],'ip':d1['vm'][i]['interfaces']['em0']['family']['inet'].split('/')[0]}
	#print(vm_mac2)
	dhcp_config=[]
	# host_config=['127.0.0.1 localhost','::1 ip6-localhost ip6-loopback']
	gw_net_config={}
	static_config={}
	mtu_config={}
	dhcp_config=['default-lease-time 600;','max-lease-time 7200;','ddns-update-style none;','option space ZTP;','option ZTP.server-image code 0 = text;','option ZTP.server-file code 1 = text;',
	'option ZTP.image-file-type code 2 = text;','option ZTP.transfer-mode code 3 = text;','option ZTP.symlink-server-image code 4 = text;','option ZTP.http-port code 5 = text;',
	'option ZTP-encapsulation code 43 = encapsulate ZTP;']
	for i in d1['vm']['gw']['interfaces'].keys():
		if 'dhcp_range' in d1['vm']['gw']['interfaces'][i].keys():
			ip_subnet, subnet_mask = get_subnet(d1['vm']['gw']['interfaces'][i]['family']['inet'])
			dhcp_config.append("subnet {} netmask {} {}".format(ip_subnet, subnet_mask,"{"))
			dhcp_range=d1['vm']['gw']['interfaces'][i]['dhcp_range']
			dhcp_config.append("   range {} {};".format(dhcp_range.split("-")[0],dhcp_range.split("-")[1]))
			dhcp_config.append("   option routers {};".format(d1['vm']['gw']['interfaces'][i]['family']['inet'].split('/')[0]))
			dhcp_config.append("   option domain-name-servers {};".format(param1.jnpr_dns1))
			dhcp_config.append("}")
		if 'family' in d1['vm']['gw']['interfaces'][i].keys():
			if 'inet' in d1['vm']['gw']['interfaces'][i]['family'].keys():
				gw_net_config[i.replace('em','eth')]=d1['vm']['gw']['interfaces'][i]['family']['inet']
				if 'static' in d1['vm']['gw']['interfaces'][i]['family'].keys():
					static_config[i.replace('em','eth')]=d1['vm']['gw']['interfaces'][i]['family']['static']
		if 'mtu' in d1['vm']['gw']['interfaces'][i].keys():
			mtu_config[i.replace('em','eth')]=d1['vm']['gw']['interfaces'][i]['mtu']

	for i in vm_mac2.keys():
		dhcp_config.append("host {} {}".format(i,"{"))
		dhcp_config.append("   hardware ethernet {};".format(vm_mac2[i]['mac']))
		dhcp_config.append("   fixed-address {};".format(vm_mac2[i]['ip']))
		dhcp_config.append("}")
		# host_config.append("{} {}".format(ipaddr,i))

	net_config =['network:','  ethernets:']
	for i in gw_net_config.keys():
		net_config.append('    {}:'.format(i))
		net_config.append('       addresses: [ {} ]'.format((gw_net_config[i])))
		if i in mtu_config.keys():
			net_config.append('       mtu: {}'.format(mtu_config[i]))
		if i in static_config.keys():
			net_config.append('       routes:')
			for j in static_config[i]:
				net_config.append('         - to: {}'.format(j['to']))
				net_config.append('           via: {}'.format(j['via']))
				net_config.append('           metric: 1')
	return dhcp_config, net_config

def get_subnet(ipv4):
	mask_full = (0xFF << 24 ) + (0xFF << 16) + (0xFF << 8) + 0xFF
	b1,b2,b3,b4 = ipv4.split('/')[0].split('.')
	ip_bin= (int(b1) << 24) + (int(b2) << 16) + (int(b3) << 8) + int(b4)
	mask_bin = mask_full << (32 - int(ipv4.split('/')[1]))
	subnet_bin = ip_bin & mask_bin
	subnet = bin2quad(subnet_bin)
	netmask = bin2quad(mask_bin)
	return subnet, netmask 

def bin2quad(binvalue):
	m1 = 255<<24
	m2 = 255<<16
	m3 = 255 << 8
	m4 = 255
	b1=str((binvalue & m1) >> 24)
	b2=str((binvalue & m2) >> 16)
	b3=str((binvalue & m3) >> 8)
	b4=str(binvalue & m4)
	retval = '.'.join((b1,b2,b3,b4))
	#print(retval)
	return retval

def test(d1):
	print("this is a test")
	dhcp_config,net_config = get_dhcp_server_config(d1)
	print("dhcp_config")
	print(dhcp_config)

def set_gw(d1):
	dhcp_config, net_config = get_dhcp_config(d1)
	host_config = get_hosts_config(d1)
	print("setting configuration for node gw")
	line_to_file = ['#!/bin/bash','echo "']
	line_to_file += host_config
	line_to_file += ['127.0.1.1 gw']
	line_to_file += ['" | sudo tee /etc/hosts' ]
	line_to_file += ['echo "']
	line_to_file += dhcp_config
	line_to_file += ['" | sudo tee /etc/dhcp/dhcpd.conf' ]
	line_to_file +=['rm -f ~/.ssh/*']
	line_to_file +=['echo "' + d1['pod']['ssh_key'] + '" | tee .ssh/authorized_keys']
	line_to_file +=['echo "' + d1['pod']['ssh_key_priv'] + '" | tee .ssh/id_rsa']
	line_to_file +=['chmod og-rwx .ssh/id_rsa']
	line_to_file += ['echo "']
	line_to_file += net_config
	line_to_file += ['" | sudo tee /etc/netplan/02_net.yaml' ]
	line_to_file += ['sudo rm /etc/resolv.conf']
	line_to_file += ['echo "']
	line_to_file += ['nameserver {}'.format(param1.jnpr_dns1)]
	line_to_file += ['nameserver {}'.format(param1.jnpr_dns2)]
	line_to_file += ['" | sudo tee /etc/resolv.conf' ]
	line_to_file += ['echo "Host *']
	line_to_file += ['   StrictHostKeyChecking no']
	line_to_file += ['" | tee ~/.ssh/config']
	line_to_file += ['']
	t1,t2 = create_novnc(d1)
	line_to_file += t1
	line_to_file += ['echo "/usr/local/bin/startup.sh" | sudo tee -a /etc/rc.local']
	line_to_file += ['']
	line_to_file +=	['sudo sed -i -e "s/#DNS=/DNS={}/" /etc/systemd/resolved.conf'.format(param1.jnpr_dns1)]
	line_to_file +=	['sudo sed -i -e "s/#FallbackDNS=/FallbackDNS={}/" /etc/systemd/resolved.conf'.format(param1.jnpr_dns2)]
	line_to_file += ['']
	line_to_file += ['sleep 2']
	line_to_file += ['sudo netplan apply' ]
	line_to_file += ['sudo systemctl restart rc-local.service']
	line_to_file += ['sudo systemctl restart isc-dhcp-server']
	line_to_file += ['sudo systemctl restart systemd-resolved.service']
	#line_to_file += ['sudo reboot']
	f1=param1.tmp_dir + 'set_gw.sh'
	write_to_file(f1,line_to_file)
	ssh=connect_to_gw(d1)
	sftp=ssh.open_sftp()
	print("uploading file to gw")
	sftp.put(f1,'set_gw.sh')
	print("Executing script on gw")
	print("chmod +x set_gw.sh")
	cmd1="chmod +x /home/ubuntu/set_gw.sh"
	cmd1='ls -la'
	s0,s1,s2=ssh.exec_command(cmd1)
	cmd1="bash /home/ubuntu/set_gw.sh"
	print("executing set_gw.sh")
	ssh.exec_command(cmd1)
	sftp.close()
	ssh.close()

def create_novnc(d1):
	novnc_port = 6081
	websock=[]
	retval=[]
	novnc_url=[]
	ip_gw = d1['vm']['gw']['interfaces']['em1']['family']['inet'].split('/')[0]
	for i in d1['vm'].keys():
		if 'vnc' in d1['vm'][i].keys():
			if d1['vm'][i]['vnc'] != "no":
				vnc_server = get_vncinfo(d1,i)
				# websock.append("websockify -D --web=/usr/share/novnc/ --cert=/home/ubuntu/novnc.pem {} {}".format(novnc_port,vnc_server))
				websock.append("websockify -D --web=/usr/share/novnc/ {} {}".format(novnc_port,vnc_server))
				# websock.append("nohup novnc --listen {} --vnc {} & ".format(novnc_port,vnc_server))
				novnc_url.append("console {} : http://{}:{}/vnc.html".format(i,ip_gw,novnc_port))
				novnc_port +=1
	if websock:
		retval.append('echo \'#!/bin/bash')
		for i in websock:
			retval.append('{}'.format(i))
		retval.append('\' | sudo tee  /usr/local/bin/startup.sh')
		retval.append('sudo chmod +x /usr/local/bin/startup.sh')
		retval.append('echo "#!/bin/bash')
		retval.append('echo \"-------------------------\"')
		retval.append('echo "URL access to VNC: "')
		print("URL access to VNC: ")
		for i in novnc_url:
			print(i)
			retval.append('echo \"{}\"'.format(i))
		retval.append('echo \"-------------------------\"" | sudo tee /etc/update-motd.d/99-update')
		retval.append('sudo chmod +x /etc/update-motd.d/99-update')
	return retval,websock

def set_host(d1):
	host_yes=['centos','ubuntu','ubuntu2','debian','bridge','desktop']
	list_hosts=[]
	f1=param1.tmp_dir + 'set_host.sh'
	for i in d1['vm'].keys():
		if d1['vm'][i]['os'] in host_yes:
			if  'family' in d1['vm'][i]['interfaces']['em0'].keys():
				if  'inet' in d1['vm'][i]['interfaces']['em0']['family'].keys():
					list_hosts.append(i)
	# open connection to gw
	host='gw'
	host_ip = get_ip_vm(d1,host)
	user_id = get_ssh_user(d1,host).strip().split()[1]
	gw_ip = host_ip
	ssh = connect_to_gw(d1)
	host_config = get_hosts_config(d1)
	print("list of host ",list_hosts)
	for i in list_hosts:
		print("configuring host %s" %(i))
		intf=d1['vm'][i]['interfaces']
		if d1['vm'][i]['os'] == 'bridge' or d1['vm'][i]['os'] == 'alpine':
			line_to_file = ['#!/bin/sh','echo "']
		else:
			line_to_file = ['#!/bin/bash','echo "']
		line_to_file += host_config
		line_to_file += ['127.0.1.1 {} '.format(i)]
		line_to_file += ['" | sudo tee /etc/hosts' ]
		line_to_file += ['sudo hostname %s' %(i)]
		line_to_file += ['hostname | sudo tee /etc/hostname']
		line_to_file += ['mkdir ~/.ssh']
		line_to_file +=	['echo "' + d1['pod']['ssh_key'] + '" | tee .ssh/authorized_keys']
		line_to_file +=	['echo "' + d1['pod']['ssh_key_priv'] + '" | tee .ssh/id_rsa']
		line_to_file +=	['chmod og-rwx .ssh/id_rsa']
		if d1['vm'][i]['os'] in  ['ubuntu','ubuntu2']:
			line_to_file +=	['sudo rm /etc/netplan/*']
			line_to_file +=	['echo "']
			line_to_file +=	['network:']
			line_to_file +=	['  ethernets:']
			br_intf={}
			for j in intf.keys():
				line_to_file +=	['    {}:'.format(j.replace("em","eth"))]
				line_to_file +=	['      dhcp4: false']
				if 'mtu' in intf[j].keys():
					line_to_file +=	['      mtu: {}'.format(intf[j]['mtu'])]
				if 'as_bridge' in intf[j].keys():
					bridge_name = intf[j]['as_bridge']
					br_intf[bridge_name] = intf[j]
					br_intf[bridge_name]['intf'] = format(j.replace("em","eth"))
				else:
				#if 'as_bridge' in intf[j].keys():
				#	tmp_br = intf[j]
				#	#print(f"tmp_br {tmp_br}")
				#	tmp_br['intf']=j.replace("em","eth")
				#	#print(f"tmp_br {tmp_br}")
				#	br_intf.append(tmp_br)
				#	#print(f"tmp_br {tmp_br}")
				#else:
					if 'family' in intf[j].keys():
						if 'inet' in intf[j]['family'].keys():
							line_to_file +=	['      addresses: [ {} ]'.format(intf[j]['family']['inet'])]
							if 'static' in intf[j]['family'].keys():
								for k in intf[j]['family']['static']:
									if k['to'] == '0.0.0.0/0':
										line_to_file += ['      nameservers:']
										line_to_file += ['         addresses: [ {} , {}]'.format(param1.jnpr_dns1,param1.jnpr_dns2)]
										break
								line_to_file += ['      routes:']
								for k in intf[j]['family']['static']:
									line_to_file += ['        - to: {}'.format(k['to'])]
									line_to_file += ['          via: {}'.format(k['via'])]
									line_to_file += ['          metric: 1']
			if br_intf:
				#print(f"br_intf{br_intf}")
				line_to_file +=	['  bridges:']
				for j in br_intf.keys():
					line_to_file +=	[f"    {j}:"]
					line_to_file +=	['      dhcp4: false']
					line_to_file +=	['      interfaces: [{}]'.format(br_intf[j]['intf'])]
					if 'family' in br_intf[j].keys():
						if 'inet' in br_intf[j]['family'].keys():
							line_to_file +=	['      addresses: [ {} ]'.format(br_intf[j]['family']['inet'])]
						#print(f"j  {j}")
						if 'static' in br_intf[j]['family'].keys():
							for k in br_intf[j]['family']['static']:
								if k['to'] == '0.0.0.0/0':
									line_to_file += ['      nameservers:']
									line_to_file += ['         addresses: [ {} , {}]'.format(param1.jnpr_dns1,param1.jnpr_dns2)]
									break
							line_to_file += ['      routes:']
							for k in br_intf[j]['family']['static']:
								line_to_file += ['        - to: {}'.format(k['to'])]
								line_to_file += ['          via: {}'.format(k['via'])]
								line_to_file += ['          metric: 1']
			line_to_file += ['" | sudo tee /etc/netplan/01_net.yaml']
			line_to_file += ['uuidgen  | sed -e \'s/-//g\' | sudo tee /etc/machine-id']
		elif d1['vm'][i]['os'] == 'desktop':
			status=False
			for j in intf.keys():
				if 'family' in intf[j].keys():
					if 'inet' in intf[j]['family'].keys():
						status=True
						break
			if status:
				line_to_file +=	['sudo rm /etc/netplan/*']
				line_to_file +=	['echo "']
				line_to_file +=	['network:']
				line_to_file +=	['  ethernets:']
				for j in intf.keys():
					line_to_file +=	['    {}:'.format(j.replace("em","eth"))]
					line_to_file +=	['      dhcp4: false']
					if 'mtu' in intf[j].keys():
							line_to_file +=	['      mtu: {}'.format(intf[j]['mtu'])]
					if 'family' in intf[j].keys():
						if 'inet' in intf[j]['family'].keys():
							line_to_file +=	['      addresses: [ {} ]'.format(intf[j]['family']['inet'])]
							line_to_file += ['      nameservers:']
							line_to_file += ['         addresses: [ {} , {}]'.format(param1.jnpr_dns1,param1.jnpr_dns2)]
							if 'static' in intf[j]['family'].keys():
								line_to_file += ['      routes:']
								for k in intf[j]['family']['static']:
									line_to_file += ['        - to: {}'.format(k['to'])]
									line_to_file += ['          via: {}'.format(k['via'])]
									line_to_file += ['          metric: 1']
				line_to_file += ['" | sudo tee /etc/netplan/01_net.yaml']
				line_to_file += ['uuidgen  | sed -e \'s/-//g\' | sudo tee /etc/machine-id']
		elif d1['vm'][i]['os'] == 'centos':
			for j in intf.keys():
				line_to_file +=	['echo "DEVICE={}'.format(j.replace("em","eth"))]
				line_to_file +=	['TYPE=ETHERNET']
				if 'family' in intf[j].keys():
					if 'inet' in intf[j]['family'].keys():
						line_to_file +=	['BOOTPROTO=static']
						line_to_file +=	['IPADDR={}'.format(intf[j]['family']['inet'].split('/')[0]) ]
						line_to_file +=	['PREFIX={}'.format(intf[j]['family']['inet'].split('/')[1]) ]
						if 'mtu' in intf[j].keys():
							line_to_file +=	['MTU={}'.format(intf[j]['mtu'])]
						if 'gateway4' in intf[j]['family'].keys():
							line_to_file +=	['GATEWAY={}'.format(intf[j]['gateway4'])]
						#if 'dns' in intf[j].keys():
							line_to_file +=	['DNS1={}'.format(param1.jnpr_dns1)]
						line_to_file += ['" | sudo tee /etc/sysconfig/network-scripts/ifcfg-{}'.format(j.replace("em","eth"))]
						if 'static' in intf[j]['family'].keys():
							list_of_static = intf[j]['family']['static']
							line_to_file +=	['echo "']
							for k in list_of_static:
								line_to_file +=	['{} via {} dev {}'.format(k['to'],k['via'],j.replace("em","eth"))]
							line_to_file += ['" | sudo tee /etc/sysconfig/network-scripts/route-{}'.format(j.replace("em","eth"))]
		elif d1['vm'][i]['os'] == 'debian':
			line_to_file +=	['sudo rm /etc/network/interfaces.d/*']
			line_to_file +=	['sudo rm /run/network/interfaces.d/*']
			line_to_file +=	['echo "']
			line_to_file +=	['auto lo']
			line_to_file +=	['iface lo inet loopback']
			for j in intf.keys():
				line_to_file +=	['auto {}'.format(j.replace("em","eth"))]
				if 'family' in intf[j].keys():
					if 'inet' in intf[j]['family'].keys():
						line_to_file +=	['iface {} inet static'.format(j.replace("em","eth"))]
						# line_to_file +=	['iface {} inet static'.format(j.replace("em","eth"))]
						line_to_file +=	['  address {}'.format(intf[j]['family']['inet'])]
						if 'mtu' in intf[j].keys():
							line_to_file +=	['  mtu {}'.format(intf[j]['mtu'])]	
						if 'gateway4' in intf[j]['family'].keys():
							line_to_file +=	['  gateway {}'.format(intf[j]['family']['gateway4'])]
							line_to_file +=	['  dns-nameservers {}'.format(param1.jnpr_dns1)]
						if 'static' in intf[j]['family'].keys():
							list_of_static = intf[j]['family']['static']
							for k in list_of_static:
								line_to_file +=	['  up ip route add {} via {} dev {}'.format(k['to'],k['via'],j.replace("em","eth"))]
					
				else:
					line_to_file +=	['iface {} inet manual'.format(j.replace("em","eth"))]
			line_to_file += ['" | sudo tee /etc/network/interfaces.d/01_net']
		elif d1['vm'][i]['os'] == 'alpine':
			line_to_file +=	['sudo rm /etc/network/interface']
			line_to_file +=	['echo "']
			line_to_file +=	['auto lo']
			line_to_file +=	['interface lo inet loopback']
			line_to_file +=	['auto eth0']
			line_to_file +=	['interface eth0 inet static']
			line_to_file +=	['  address {}'.format(intf['em0']['family']['inet'])]
			if 'gateway4' in intf['em0']['family'].keys():
				line_to_file +=	['  gateway {}'.format(intf['em0']['family']['gateway4'])]
			#if 'dns' in intf['em0'].keys():
				line_to_file +=	['  dns-nameservers {}'.format(param1.jnpr_dns1)]
			intf_list = d1['vm'][i]['interfaces']
		elif d1['vm'][i]['os'] == 'bridge':
			line_to_file +=	['sudo rm /etc/network/interface']
			line_to_file +=	['echo "']
			line_to_file +=	['auto lo']
			line_to_file +=	['interface lo inet loopback']
			line_to_file +=	['auto eth0']
			line_to_file +=	['interface eth0 inet static']
			line_to_file +=	['  address {}'.format(intf['em0']['family']['inet'])]
			if 'gateway4' in intf['em0']['family'].keys():
				line_to_file +=	['  gateway {}'.format(intf['em0']['family']['gateway4'])]
			#if 'dns' in intf['em0'].keys():
				line_to_file +=	['  dns-nameservers {}'.format(param1.jnpr_dns1)]
			intf_list = d1['vm'][i]['interfaces']
			brtmp1={}
			for x in intf_list.keys():
				if x != 'em0':
					if intf_list[x]['node'][2] not in brtmp1.keys():
						brtmp1[intf_list[x]['node'][2]]=[]
						brtmp1[intf_list[x]['node'][2]].append(x.replace('em','eth'))
					else:
						brtmp1[intf_list[x]['node'][2]].append(x.replace('em','eth'))
					line_to_file += ['auto {}'.format(x.replace('em','eth'))]
					line_to_file += ['interface {} inet manual'.format(x.replace('em','eth'))]
					line_to_file += ['  mtu 9000']			
			for x in brtmp1.keys():
				line_to_file += ['auto {}'.format(x)]
				line_to_file += ['interface {} inet manual'.format(x)]
				line_to_file += ['  post-up echo 0x4000 > /sys/class/net/{}/bridge/group_fwd_mask'.format(x)]
				tmp1=""
				for y in brtmp1[x]:
					tmp1+='{} '.format(y)
				line_to_file += ['  bridge-ports {}'.format(tmp1)]
				line_to_file += ['  bridge-stp 0']
			line_to_file +=['" | sudo tee /etc/network/interfaces']
		line_to_file += ['echo "Host *']
		line_to_file += ['   StrictHostKeyChecking no']
		line_to_file += ['"| tee ~/.ssh/config']
		line_to_file += ['']
		line_to_file += ['sleep 2']
		line_to_file += ['sudo reboot']
		write_to_file(f1,line_to_file)
		ssh2host=connect_to_vm(d1,i)
		sftp=ssh2host.open_sftp()
		print("uploading file to %s" %(i))
		sftp.put(f1,'set_host.sh')
		print("Executing script on %s" %(i))
		#cmd1="chmod +x /home/ubuntu/set_host.sh"
		cmd1="chmod +x ~/set_host.sh"
		ssh2host.exec_command(cmd1)
		#cmd1="bash /home/ubuntu/set_host.sh"
		cmd1="sh ~/set_host.sh"
		ssh2host.exec_command(cmd1)
		sftp.close()
		ssh2host.close()

	ssh.close()
	if 'jumpserver' in d1['pod'].keys():
		jumphost.close()
	

def get_gateway(d1,i):
	retval=''
	bridge1 = d1['vm'][i]['interfaces']['em0']['bridge']
	for j in d1['vm']['gw']['interfaces'].keys():
		if bridge1 == d1['vm']['gw']['interfaces'][j]['bridge']:
			retval=d1['vm']['gw']['interfaces'][j]['family']['inet'].split('/')[0]
	return retval
	
def get_mac(d1):
	for i in d1['vm'].keys():
		if d1['vm'][i]['os'] == 'vex':
			print(f"mac of {i} is {get_mac_vm(d1,i)}")

def get_mac_vm(d1,i):
	if d1['pod']['type'] == 'vmm':
		ssh=sshconnect(d1)
		cmd1="vmm args " + i + " | grep \" mac \""
		stdin,stdout,sstderr=ssh.exec_command(cmd1)
		j = stdout.readlines()
		ssh.close()
		_,retval= j[0].rstrip().split()
		return retval

	elif d1['pod']['type'] == 'kvm':
		print("not implemented for this type")
		return ""

def get_serial(d1,vm=""):
	if d1['pod']['type'] == 'vmm':
		ssh=sshconnect(d1)
		print('-----')
		print("serial port of VM")
		cmd1="vmm list"
		s1,s2,s3=ssh.exec_command(cmd1)
		vm_list=[]
		for i in s2.readlines():
			vm_list.append(i.rstrip().split()[0])	
		if vm=="":
			print("vm list", vm_list)
			for i in vm_list:
				print("serial of " + i + " : " + get_serial_vm(d1,i).replace(":"," "))
		elif vm not in vm_list:
			print("VM %s does not exist " %(vm))
		else:
			print("serial of " + vm + " : " + get_serial_vm(d1,vm).replace(":"," "))
		ssh.close()
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")


def get_serial_vm(d1,i):
	ssh=sshconnect(d1)
	cmd1="vmm args " + i + " | grep \"serial \""
	s1,s2,s3=ssh.exec_command(cmd1)
	j=s2.readlines()[0]
	return j.rstrip().split()[1]

def list_vm(d1):
	if d1['pod']['type'] == 'vmm':
		print('list of running VM')
		ssh=sshconnect(d1)
		print('-----')
		cmd1="vmm list"
		s1,s2,s3=ssh.exec_command(cmd1)
		for i in s2.readlines():
			print(i.rstrip())
		ssh.close()
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")

def stop(d1):
	if d1['pod']['type'] == 'vmm':
		ssh=sshconnect(d1)
		print('-----')
		print("stop the existing topology")
		cmd1="vmm stop && vmm unbind"
		s1,s2,s3=ssh.exec_command(cmd1)
		for i in s2.readlines():
			print(i.rstrip())
		ssh.close()
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")

def check_vsan_status(d1):
	retval = False
	for i in d1['vm'].keys():
		if d1['vm'][i]['type'] == 'vcsa':
			if 'vsan' in d1['vm'][i].keys():
				if d1['vm'][i]['vsan'] == 'yes' or d1['vm'][i]['vsan']:
					retval = True
			break
	return retval

def create_esxi_disk(d1,ssh):
	# print("create esxi disk")
	# vsan_disk = check_vsan_status(d1)
	if check_vsan_status(d1):
		for i in d1['vm'].keys():
			if d1['vm'][i]['os'] == 'esxi':
				disk_name = 'esxi' + str(d1['vm'][i]['disk']) + ".vmdk"
				# str1= d1['pod']['home_dir'] + "/" + d1['images'][disk_name]
				str1 = d1['pod']['home_dir'] +'/vm/' + d1['name'] + "/" + disk_name
				# str1= d1['pod']['home_dir'] +'/vm/' + d1['name'] + "/" + d1['images'][disk_name]
				cmd2 = "qemu-img create -f vmdk " + str1.replace(".vmdk","disk2.vmdk") + " " + str(param1.esxi_ds_size) + "G"
				cmd3 = "qemu-img create -f vmdk " + str1.replace(".vmdk","disk3.vmdk") + " " + str(param1.esxi_ds_size) + "G"
				s1,s2,s3=ssh.exec_command(cmd2)
				for i in s2.readlines():
					print(i.rstrip())
				s1,s2,s3=ssh.exec_command(cmd3)
				for i in s2.readlines():
					print(i.rstrip())

def create_hd2(d1):
	os_type=['ubuntu','ubuntu2','centos','debian']
	dest_dir=d1['pod']['home_dir'] +'/vm/' + d1['name'] + "/"
	vm_with_hd2 = {}
	retval=""
	for i in d1['vm'].keys():
		if d1['vm'][i]['os'] in os_type:
			if 'hd2' in d1['vm'][i].keys():
				vm_with_hd2[i]=d1['vm'][i]['hd2']
	if vm_with_hd2:
		cmd_list=""
		for i in vm_with_hd2.keys():
			ds=vm_with_hd2[i]
			str_tmp1 = "qemu-img create -f vmdk {}{}-disk1.img {}".format(dest_dir,i,ds)
			cmd_list += "{};".format(str_tmp1)
		retval=cmd_list
	return retval


		
def start(d1):
	if d1['pod']['type'] == 'vmm':
		print('starting topology on vmm')
		lab_conf=d1['pod']['home_dir'] +'/vm/' + d1['name'] + "/lab.conf"
		ssh=sshconnect(d1)
		print('-----')
		print("stop and unbind the existing topology")
		cmd1=create_hd2(d1)
		if cmd1:
			s1,s2,s3=ssh.exec_command(cmd1)
			for i in s2.readlines():
				print(i.rstrip())
		cmd1="vmm stop"
		s1,s2,s3=ssh.exec_command(cmd1)
		for i in s2.readlines():
			print(i.rstrip())
		cmd1="vmm unbind"
		s1,s2,s3=ssh.exec_command(cmd1)
		for i in s2.readlines():
			print(i.rstrip())
		print("start configuration ")
		create_esxi_disk(d1,ssh)
		cmd1="vmm config " + lab_conf  + " " + param1.vmm_group
		s1,s2,s3=ssh.exec_command(cmd1)
		for i in s2.readlines():
			print(i.rstrip())
		print("start topology ")
		cmd1="vmm start"
		s1,s2,s3=ssh.exec_command(cmd1)
		for i in s2.readlines():
			print(i.rstrip())
		write_ssh_config(d1)
		ssh.close()
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")

def upload(d1,upload_status=1):
# creating lab.conf
	if d1['pod']['type'] == 'vmm':
		if upload_status:
			print('starting topology on vmm')
		else:
			print('creating topology for  vmm')
		if not checking_config_syntax(d1):
			return
		# print("still continue")
		#config_dir=d1['pod']['home_dir'] + d1['pod']['user'] + '/vm/' + d1['name'] + "/"
		config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
		# home_dir=param1.home_dir + d1['pod']['user'] + "/"
		lab_conf=[]
		lab_conf.append('#include "/vmm/bin/common.defs"')
		lab_conf.append('#include "/vmm/data/user_disks/vmxc/common.vmx.p3.defs"')
		#lab_conf.append('#include "/vmm/data/user_disks/vptxc/common.brackla.defs"')
		#lab_conf.append('#include "/vmm/data/user_disks/vptxc/common.evovptx.defs"')
		lab_conf.append('#include "/vmm/data/user_disks/vptxc/common.evovptx.ardbeg.defs"')
		lab_conf.append('#include "/vmm/data/user_disks/vptxc/common.ardbeg.defs"')
		vm_os_d1=[]
		for i in d1['vm'].keys():
			if 'disk' in d1['vm'][i].keys():
				# temp_s1=d1['vm'][i]['os'] + "_" + d1['vm'][i]['disk']	
				temp_s1=d1['vm'][i]['os'] + str(d1['vm'][i]['disk'])
			else:
				temp_s1=d1['vm'][i]['os']
			if temp_s1 not in vm_os_d1:
				vm_os_d1.append(temp_s1)
		for i in vm_os_d1:
			if i=='vmx' or i=='mx960' or i=='mx480' or i=='mx240':
				str1="#undef VMX_DISK0"
				lab_conf.append(str1)
				# str1='#define VMX_DISK0  basedisk "' +  home_dir + d1['images']['vmx_re'] + '";'
				str1='#define VMX_DISK0  basedisk "' +  d1['pod']['home_dir'] + "/" + d1['images']['vmx_re'] + '";'
				lab_conf.append(str1)
				# str1="#undef PFE_DISK"
				#str1="#undef VMX_DISK1"
				#lab_conf.append(str1)
				# str1='#define PFE_DISK  basedisk "' + home_dir + d1['images']['vmx_mpc'] + '";'
				# str1='#define PFE_DISK  basedisk "' + d1['pod']['home_dir'] + "/"+ d1['images']['vmx_mpc'] + '";'
				#str1='#define VMX_DISK1  basedisk "' + d1['pod']['home_dir'] + "/"+ d1['images']['vmx_mpc'] + '";'
				#lab_conf.append(str1)
				#str1="#undef VIRTUAL_MPC_DISK"
				#lab_conf.append(str1)
				# str1='#define PFE_DISK  basedisk "' + home_dir + d1['images']['vmx_mpc'] + '";'
				# str1='#define PFE_DISK  basedisk "' + d1['pod']['home_dir'] + "/"+ d1['images']['vmx_mpc'] + '";'
				#str1='#define VIR TUAL_MPC_DISK  basedisk "' + d1['pod']['home_dir'] + "/"+ d1['images']['vmx_mpc'] + '";'
				#lab_conf.append(str1)
			elif i=='evo':
				str1="#undef EVOVPTX_DISK1"
				lab_conf.append(str1)
				str1='#define EVOVPTX_DISK1 "' +  d1['pod']['home_dir'] + "/" + d1['images']['evo'] + '"'
				lab_conf.append(str1)
				str1='#undef EVOVPTX_FPC_CSPP_IMG'
				lab_conf.append(str1)
				str1='#define EVOVPTX_FPC_CSPP_IMG "/vmm/data/base_disks/junos/vevo/ubuntu_vm_evo.qcow2"'
				lab_conf.append(str1)
				str1='#undef VMM_ENV_CSPP_CFG_DIR'
				lab_conf.append(str1)
				str1='#define VMM_ENV_CSPP_CFG_DIR /vmm/data/user_disks/evo_test/EVOvSCAPA/'
				lab_conf.append(str1)
				if 'evo' in d1['pod']:
					lab_conf.extend(add_evo1(d1))
			elif i=='vqfx':
				str1="#undef VQFX_RE"
				lab_conf.append(str1)
				str1='#define VQFX_RE  basedisk "' + d1['pod']['home_dir'] + "/" + d1['images']['vqfx_re'] + '";'
				lab_conf.append(str1)
				str1="#undef VQFX_COSIM"
				lab_conf.append(str1)
				str1='#define VQFX_COSIM  basedisk "' + d1['pod']['home_dir']  + "/" + d1['images']['vqfx_cosim'] + '";'
				lab_conf.append(str1)
			elif i=='vsrx':
				str1="#undef VSRXDISK"
				lab_conf.append(str1)
				str1='#define VSRXDISK basedisk "' + d1['pod']['home_dir']  + "/" + d1['images']['vsrx'] + '";'
				lab_conf.append(str1)
			elif i=='vex':
				str1="#undef VEXDISK"
				lab_conf.append(str1)
				str1='#define VEXDISK basedisk "' + d1['pod']['home_dir']  + "/" + d1['images']['vex'] + '";'
				lab_conf.append(str1)
			elif i=='vrr':
				str1="#undef VRRDISK"
				lab_conf.append(str1)
				str1='#define VRRDISK basedisk "' + d1['pod']['home_dir']  + "/" + d1['images']['vrr'] + '";'
				lab_conf.append(str1)
			elif i=='vcsa':
				temp_s1=i.upper() + "_DISK"
				str1="#undef " + temp_s1
				lab_conf.append(str1)
				str1='#define ' + temp_s1 + ' basedisk "' + d1['pod']['home_dir'] + "/" + d1['images'][i] + '";'
				lab_conf.append(str1)
				#temp_s1=i.upper() + "DISK2_DISK"
				#str1="#undef " + temp_s1
				#lab_conf.append(str1)
				#str1='#define ' + temp_s1 + ' disk "sdb" "' + d1['pod']['home_dir'] + "/" + d1['images']['vcsadisk2'] + '";'
				#lab_conf.append(str1)
			elif 'esxi' in i:
				temp_s1=i.upper() + "_DISK"
				str1="#undef " + temp_s1
				lab_conf.append(str1)
				str1='#define ' + temp_s1 + ' basedisk "' + d1['pod']['home_dir'] + "/" + d1['images'][i] + '";'
				lab_conf.append(str1)
			elif 'veos' in i:
				str1="#undef VEOSDISK "
				lab_conf.append(str1)
				str1='#define VEOSDISK basedisk "' + d1['pod']['home_dir'] + "/" + d1['images'][i] + '";'
				lab_conf.append(str1)
				str1="#undef VEOS_CDROM"
				lab_conf.append(str1)
				str1='#define VEOS_CDROM cdrom_boot "' + d1['pod']['home_dir'] + "/" + d1['images']['veos_cdrom'] + '";'
				lab_conf.append(str1)
			else:
				temp_s1=i.upper() + "_DISK"
				str1="#undef " + temp_s1
				lab_conf.append(str1)
				str1='#define ' + temp_s1 + ' basedisk "' + d1['pod']['home_dir'] + "/" + d1['images'][i] + '";'
				lab_conf.append(str1)
		str1='config "' +d1['name'] + '"{'
		lab_conf.append(str1)
		lab_conf.extend(list_bridge(d1))

	# creating VM configuration
		for i in d1['vm'].keys():
			if d1['vm'][i]['type'] == 'gw':
				lab_conf.extend(make_gw_config(d1,i))
			elif d1['vm'][i]['type'] in param1.pc_type:
				lab_conf.extend(make_pc_config(d1,i))
			elif d1['vm'][i]['type'] in [ 'vapp','vapp_s']:
				lab_conf.extend(make_pc_config(d1,i))
			elif d1['vm'][i]['type'] == 'junos':
				lab_conf.extend(make_junos_config(d1,i))
			elif d1['vm'][i]['type'] == 'vspirent':
				lab_conf.extend(make_pc_config(d1,i))
			elif d1['vm'][i]['type'] in  ['vcsa','esxi']:
				lab_conf.extend(make_vmware_config(d1,i))
			elif d1['vm'][i]['type'] == 'veos':
				lab_conf.extend(make_veos_config(d1,i))
		lab_conf.append('};')

		if os.path.exists(param1.tmp_dir):
			print("directory exist ")
			shutil.rmtree(param1.tmp_dir)
		os.mkdir(param1.tmp_dir)
		f1=param1.tmp_dir + "lab.conf"
		write_to_file(f1,lab_conf)
		write_junos_config(d1)
		write_inventory(d1)
		if upload_status:
			upload_file_to_server(d1)
	elif d1['pod']['type'] == 'kvm':
		print("not yet implemented")

def add_evo1(d1):
	retval=[]
	retval.append('#undef EVOvArdbegRE')
	retval.append('#define EVOvArdbegRE(CHAS_NAME,BOOT_DISK) \\')
	retval.append('    bridge XCAT(CHAS_NAME, _FPC1_RPIO_BRG) {};\\')
	retval.append('    bridge XCAT(CHAS_NAME, _FPC1_PFE_BRG) {};\\')
	retval.append('    vm STRINGIZE (CATENATE3 (CHAS_NAME, _RE, EVOVPTX_RE0)) {\\')
	retval.append('    hostname XCAT(CHAS_NAME, _node0);\\')
	retval.append('    cdrom_boot BOOT_DISK;\\')
	retval.append('    memory EVOvArdbeg_RE_MEMORY;\\')
	retval.append('    ncpus EVOvArdbeg_RE_NCPU;\\')
	retval.append('    REsetvar(CHAS_NAME)\\')
	retval.append('    REinstall\\')
	retval.append('    interface "em0" {\\')
	retval.append('        bridge "{}";\\'.format(d1['pod']['evo']))
	retval.append('        ext_vlanid 0;\\')
	retval.append('    };\\')
	retval.append('    interface "em1" {\\')
	retval.append('        bridge XCAT(CHAS_NAME, _FPC1_PFE_BRG);\\')
	retval.append('        ext_vlanid 0;\\')
	retval.append('    };\\')
	retval.append('    interface "em2" {\\')
	retval.append('        bridge XCAT(CHAS_NAME, _FPC1_RPIO_BRG);\\')
	retval.append('            ext_vlanid 0;\\')
	retval.append('    };\\')
	retval.append('    interface "em3" {\\')
	retval.append('        bridge XCAT(CHAS_NAME, _FPC1_RPIO_BRG);\\')
	retval.append('            ext_vlanid 0;\\')
	retval.append('    };\\')
	retval.append('    interface "em4" {\\')
	retval.append('        bridge "{}";\\'.format(d1['pod']['evo']))
	retval.append('            ext_vlanid 0;\\')
	retval.append('    };\\')
	retval.append('}; ')
	return retval 

def write_inventory(d1):
	print("writing inventory for ansible")
	f1=param1.tmp_dir + "inventory"
	line1=["[all]"]
	for i in d1['vm'].keys():
		if d1['vm'][i]['type'] == 'junos':
			line1.append(i)
	# line1.append("[all:vars]")
	# line1.append("ansible_python_interpreter=/usr/bin/python3")
	write_to_file(f1,line1)

def write_ssh_config(d1):
	file1=[]
	print("writing file ssh_config")
	for i in d1['vm'].keys():
		if d1['vm'][i]['type']=='gw':
			gw_name = i
			break
	file1.append('### by vmm-v3-script ###')
	#file1.append('### the following lines are added by vmm-v3-script')
	file1.append("""Host *
    StrictHostKeyChecking no
	
	""")
	if 'ssh_key_name' in d1['pod'].keys():
		identity_file = "	IdentityFile ~/.ssh/" + d1['pod']['ssh_key_name']
	else:
		identity_file = "   IdentityFile ~/.ssh/id_rsa"
	# creating entry for Jump Server
	if 'jumpserver' in d1['pod'].keys():
		file1.append("host %s" %('jumphost'))
		file1.append("   hostname %s" %(d1['pod']['jumpserver']))
		file1.append("   user %s" %(d1['pod']['user']))
		file1.append(identity_file)
		file1.append("   ")
		# creating entry for VMM server
		file1.append("host %s" %('vmm'))
		file1.append("    ProxyCommand ssh -W %s:22 jumphost " %(d1['pod']['vmmserver']))
		file1.append("    user %s" %(d1['pod']['user']))
		file1.append(identity_file)
		file1.append("   ")
		
		for i in d1['vm'].keys():
			if d1['vm'][i]['type']=='gw':
				file1.append("host %s" %(i))
				# file1.append("   hostname %s" %(get_ip_vm(d1,i)))
				file1.append("    ProxyCommand ssh -W %s:22 jumphost " %(get_ip_vm(d1,i)))
				file1.append(get_ssh_user(d1,i))
				file1.append(identity_file)
				file1.append("   ")
				file1.append("host %s" %('proxy'))
				# file1.append("   hostname %s" %(get_ip_vm(d1,i)))
				file1.append("    ProxyCommand ssh -W %s:22 jumphost " %(get_ip_vm(d1,i)))
				file1.append(get_ssh_user(d1,i))
				file1.append(identity_file)
				
				if 'proxy' in d1.keys():
					if 'DynForward' in d1['proxy'].keys():
						file1.append("   DynamicForward {}".format(d1['proxy']['DynForward']))
					else:
						file1.append("   DynamicForward 1080")
					if 'forward' in d1['proxy'].keys():
						list_forward = d1['proxy']['forward']
						for j in list_forward:
							file1.append("   LocalForward {} {}:{}".format(j['localPort'],j['destIP'],j['destPort']))
				else:
					file1.append("   DynamicForward 1080")
			else:
				#if get_ip_mgmt(d1,i):
				#	file1.append("host %s" %(i))
				#	file1.append(get_ssh_user(d1,i))
				#	file1.append(identity_file)
				#	file1.append("   ProxyCommand ssh -W %s:22 %s " %(get_ip_mgmt(d1,i),gw_name))
				if 'app' in d1['vm'][i].keys():
					if d1['vm'][i]['app'] == 'crpd':
						file1.append(f"host {i}")
						file1.append("user admin")
						file1.append(identity_file)
						file1.append(f"   ProxyCommand ssh -W {get_ip_mgmt(d1,i)}:22 {gw_name} ")
						file1.append(f"host {i}os")
						file1.append(get_ssh_user(d1,i))
						file1.append(identity_file)
						file1.append(f"   ProxyCommand ssh -W {get_ip_mgmt(d1,i)}:8022 {gw_name} ")
				else:
					file1.append(f"host {i}")
					file1.append(get_ssh_user(d1,i))
					file1.append(identity_file)
					file1.append(f"   ProxyCommand ssh -W {get_ip_mgmt(d1,i)}:22 {gw_name} ")
	else:
		# creating entry for VMM server
		file1.append("host %s" %('vmm'))
		file1.append("    hostname %s" %(d1['pod']['vmmserver']))
		file1.append("    user %s" %(d1['pod']['user']))
		file1.append(identity_file)
		file1.append("   ")
		
		for i in d1['vm'].keys():
			if d1['vm'][i]['type']=='gw':
				file1.append("host %s" %(i))
				file1.append("   hostname %s" %(get_ip_vm(d1,i)))
				#file1.append("    ProxyCommand ssh -W %s:22 jumphost " %(get_ip_vm(d1,i)))
				file1.append(get_ssh_user(d1,i))
				file1.append(identity_file)
				file1.append("   ")
				file1.append("host %s" %('proxy'))
				file1.append("   hostname %s" %(get_ip_vm(d1,i)))
				#file1.append("    ProxyCommand ssh -W %s:22 jumphost " %(get_ip_vm(d1,i)))
				file1.append(get_ssh_user(d1,i))
				file1.append(identity_file)
				
				if 'proxy' in d1.keys():
					if 'DynForward' in d1['proxy'].keys():
						file1.append("   DynamicForward {}".format(d1['proxy']['DynForward']))
					else:
						file1.append("   DynamicForward 1080")
					if 'forward' in d1['proxy'].keys():
						list_forward = d1['proxy']['forward']
						for j in list_forward:
							file1.append("   LocalForward {} {}:{}".format(j['localPort'],j['destIP'],j['destPort']))
				else:
					file1.append("   DynamicForward 1080")
			else:
				if get_ip_mgmt(d1,i):
					if 'app' in d1['vm'][i].keys():
						if d1['vm'][i]['app'] == 'crpd':
							file1.append(f"host {i}")
							file1.append("user admin")
							file1.append(identity_file)
							file1.append(f"   ProxyCommand ssh -W {get_ip_mgmt(d1,i)}:22 {gw_name} ")
							file1.append(f"host {i}os")
							file1.append(get_ssh_user(d1,i))
							file1.append(identity_file)
							file1.append(f"   ProxyCommand ssh -W {get_ip_mgmt(d1,i)}:8022 {gw_name} ")
					else:
						file1.append(f"host {i}")
						file1.append(get_ssh_user(d1,i))
						file1.append(identity_file)
						file1.append(f"   ProxyCommand ssh -W {get_ip_mgmt(d1,i)}:22 {gw_name} ")
	print("write ssh_config")
	f1=param1.tmp_dir + "ssh_config"
	write_to_file(f1,file1)
	add_to_ssh_config(file1)
	# for i in file1:
	#	print(i)

def add_to_ssh_config(file1):
	ssh_config = os.path.expanduser('~') + "/.ssh/config"
	orig1 = []
	if os.path.exists(ssh_config):
		with open(ssh_config) as f_config:
			for line in f_config:
				if '### by vmm-v3-script ###' in line:
					print("found entry with ### by vmm-v3-script ###")
					break
				else:
					orig1.append(line.rstrip())
		new_config = orig1 + file1
		write_to_file(ssh_config,new_config)
	else:
		write_to_file(ssh_config,file1)

				
def get_ip_mgmt(d1,i):
	retval=""	
	if d1['vm'][i]['type'] not in ['gw','vspirent']:
		for j in d1['vm'][i]['interfaces'].keys():
			if j == 'em0' or j=='fxp0' or j=='mgmt':
			# if d1['vm'][i]['interfaces'][j]['bridge']=='mgmt':
				if 'family' in d1['vm'][i]['interfaces'][j].keys():
					if 'inet' in d1['vm'][i]['interfaces'][j]['family'].keys():
						retval = d1['vm'][i]['interfaces'][j]['family']['inet'].split("/")[0]
	return retval

def get_ssh_user(d1,i):
	retval=""
	if d1['vm'][i]['type'] == 'junos':
		retval="   user admin"
	else:
		# if d1['vm'][i]['os'] == 'centos' or d1['vm'][i]['os'] == 'centosx':
		if 'centos' in d1['vm'][i]['os']:
			retval="   user centos"
		# elif d1['vm'][i]['os'] == 'ubuntu' or d1['vm'][i]['os'] == 'ubuntu1804':
		elif d1['vm'][i]['os'] in ['ubuntu','ubuntu2']:
			retval="   user ubuntu"
		elif 'desktop' in d1['vm'][i]['os']:
			retval="   user ubuntu"
		elif 'debian' in d1['vm'][i]['os']:
			retval="   user debian"
		elif 'gw' in d1['vm'][i]['os']:
			retval="   user ubuntu"
		elif 'jspace' in d1['vm'][i]['os']:
			retval="   user admin"
		elif d1['vm'][i]['os'] in ['aos','aos_ztp']:
			retval="   user admin"
		elif 'esxi' in d1['vm'][i]['os']:
			retval="   user root"
		elif 'vcsa' in d1['vm'][i]['os']:
			retval="   user admin"
		elif 'bridge' in d1['vm'][i]['os']:
			retval="   user alpine"
		elif 'alpine' in d1['vm'][i]['os']:
			retval="   user alpine"
		elif 'veos' in d1['vm'][i]['os']:
			retval="   user admin"
	return retval


def upload_file_to_server(d1):
	vm_dir=d1['pod']['home_dir'] + '/vm/'
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	#check_dir="if [ ! -d " + vm_dir + " ]; then mkdir " + vm_dir +"; fi"
	check_dir="mkdir " + vm_dir
	#ssh=paramiko.SSHClient()
	#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# ssh.connect(hostname=d1['pod']['server'],username=d1['pod']['user'])
	#ssh.connect(hostname=d1['pod']['server'],username=d1['pod']['user'],password=d1['pod']['password'])
	ssh=sshconnect(d1)
	sftp=ssh.open_sftp()
	cmd1="rm -rf " + config_dir
	#print("check directory ",vm_dir)
	#print("command ",check_dir)
	ssh.exec_command(check_dir)
	print("deleting config_dir " , config_dir)
	ssh.exec_command(cmd1)
	sftp.mkdir(config_dir)
	file1=os.listdir("tmp")
	for i in file1: 
		local1='tmp/' + i
		remote1=config_dir + i
		print("upload file " + local1 + " to " + remote1)
		sftp.put(local1,remote1)
	sftp.close()
	ssh.close()

def get_gateway4(d1,i):
	vm_bridge = d1['vm'][i]['interfaces']['mgmt']['bridge']
	gateway4 = '0.0.0.0'
	for i in d1['vm']['gw']['interfaces'].keys():
		if d1['vm']['gw']['interfaces'][i]['bridge'] == vm_bridge:
			gateway4 = d1['vm']['gw']['interfaces'][i]['family']['inet'].split('/')[0]
	return gateway4

def create_junos_config(d1,i):
	dummy1={}
	dummy1['hostname']=i
	dummy1['username']=d1['junos_login']['login']
	dummy1['password']=md5_crypt.hash(d1['junos_login']['password'])
	dummy1['ssh_key']=d1['pod']['ssh_key']
	#dummy1['ntpserver']=d1['pod']['ntp']
	if d1['vm'][i]['os'] == 'vmx' or d1['vm'][i]['os'] == 'mx960' or d1['vm'][i]['os'] == 'mx480' or d1['vm'][i]['os'] == 'mx240':
		dummy1['type']='vmx'
	elif d1['vm'][i]['os'] == 'vqfx':
		dummy1['type']='vqfx'
	elif d1['vm'][i]['os'] == 'vsrx':
		dummy1['type']='vsrx'
	elif d1['vm'][i]['os'] == 'vrr':
		dummy1['type']='vrr'
	elif d1['vm'][i]['os'] == 'vex':
		dummy1['type']='vex'
	elif d1['vm'][i]['os'] == 'evo':
		dummy1['type']='evo'
	# dummy1['gateway4']=d1['vm']['gw']['interfaces']['em1']['family']['inet'].split('/')[0]
	dummy1['gateway4'] = get_gateway4(d1,i)
	dummy1['mgmt_ip']=d1['vm'][i]['interfaces']['mgmt']['family']['inet']
	dummy1['interfaces']=None
	dummy1['protocols']=None
	#dummy1['static']=[]
	dummy1['rpm']={}
	if 'bgpls' in d1['vm'][i].keys():
		dummy1['bgpls']={'as' : d1['vm'][i]['bgpls']['as'],'local' : d1['vm'][i]['bgpls']['local']}
	if 'pcep' in d1['vm'][i].keys():
		if d1['vm'][i]['pcep']=='yes' or d1['vm'][i]['pcep']==True:
			if 'pcep_server' in d1.keys():
				dummy1['pcep']={'server': d1['pcep_server'],'local': d1['vm'][i]['interfaces']['lo0']['family']['inet'].split('/')[0] }
	if 'paragon_ingest' in d1.keys():
		dummy1['ingest']={'ip' : d1['paragon_ingest'],'source': d1['vm'][i]['interfaces']['lo0']['family']['inet'].split('/')[0]}
	for j in d1['vm'][i]['interfaces'].keys():
		if j != 'mgmt':
			#if 'mtu' in  d1['vm'][i]['interfaces'][j].keys():
			#	add_mtu(dummy1,j,d1['vm'][i]['interfaces'][j]['mtu'])
			add_into_protocols(dummy1,'lldp',j,"")
			if 'mtu' in d1['vm'][i]['interfaces'][j].keys():
				add_mtu(dummy1,j,d1['vm'][i]['interfaces'][j]['mtu'])
			if 'family' in d1['vm'][i]['interfaces'][j].keys():
				if 'mpls' in d1['vm'][i]['interfaces'][j]['family'].keys():
					add_into_protocols(dummy1,'mpls',j,"")
				for k in d1['vm'][i]['interfaces'][j]['family'].keys():
					if d1['vm'][i]['interfaces'][j]['family'][k]:
						add_into_interfaces(dummy1,j,k,d1['vm'][i]['interfaces'][j]['family'][k])
					else:
						add_into_interfaces(dummy1,j,k,True)
			if 'protocol' in d1['vm'][i]['interfaces'][j].keys():
				#print("protocol found")
				for k in d1['vm'][i]['interfaces'][j]['protocol'].keys():
					if k == 'mpls':
						pass
					elif k == 'isis':
						if d1['vm'][i]['interfaces'][j]['protocol'][k] == 'ptp':
							option = 'point-to-point'
						elif d1['vm'][i]['interfaces'][j]['protocol'][k] == 'passive':
							option = 'passive'
						else:
							option = ""
					else:
						option = ""
					#print("interface %s protocol %s option %s" %(j,k,option))
					add_into_protocols(dummy1,k,j,option)
			if 'rpm' in d1['vm'][i]['interfaces'][j].keys():
				intf = j + ".0"
				src = d1['vm'][i]['interfaces'][j]['rpm']['source']
				dst = d1['vm'][i]['interfaces'][j]['rpm']['destination']
				dummy1['rpm'].update({intf : { 'src': src, 'dst': dst }})
			#if 'static' in d1['vm'][i]['interfaces'][j].keys():
			#	for k in d1['vm'][i]['interfaces'][j]['static']:
			#		d1['vm'][i]['interfaces'][j]['static'].append(
			#			{'to': k['to'], 'via':k['via']}
			#		)
			#	add_into_route_options_static(dummy1,)
	return dummy1


def write_junos_config(d1):
	data1=[]
	#print("Junos config write")
	#ssh_key = read_ssh_key(d1)
	#print("ssh key ",ssh_key)
	try:
		#print("template ",param1.junos_template)
		f1=open(d1['pod']['path'] + param1.junos_template)
		jt=f1.read()
		f1.close()
		for i in d1['vm'].keys():
			if d1['vm'][i]['type'] == 'junos':
				dummy1 = create_junos_config(d1,i)
				config1=Template(jt).render(dummy1)
				f1=param1.tmp_dir + i + ".conf"
				write_to_file_config(f1,config1)
	except PermissionError:
		print("permission error")

def add_mtu(dt,intf,mtu):
	if not dt['interfaces']:
		dt['interfaces']={intf:None}
	if intf not in dt['interfaces'].keys():
		dt['interfaces'][intf]=None
	dt['interfaces'][intf]={'mtu':mtu}
	#return dt

def add_into_interfaces(dt,intf,family,family_address):
	if not dt['interfaces']:
		dt['interfaces']={intf:None}
	if intf not in dt['interfaces'].keys():
		dt['interfaces'][intf]=None
	if not dt['interfaces'][intf]:
		dt['interfaces'][intf]={family:None}
	if family not in dt['interfaces'].keys():
		dt['interfaces'][intf][family]=family_address
	#return dt

def add_into_protocols(dt,prot,intf,option):
	if not dt['protocols']:
		dt['protocols']={prot:None}
	if prot not in dt['protocols'].keys():
		dt['protocols'][prot]=None
	if not dt['protocols'][prot]:
		dt['protocols'][prot]={intf:None}
	if intf not in dt['protocols'][prot].keys():
		dt['protocols'][prot][intf]=None
	if option:
		dt['protocols'][prot][intf]=option
	#return dt

def prefix2netmask(prefs):
	i=0
	b=[]
	pref = int(prefs)
	for i in range(4):
		# print("pref ",pref)
		if pref >= 8:
			b.append(255)
		elif pref >= 0:
			b1=0
			f1=7
			for j in list(range(pref)):
				b1 +=  2 ** f1
				f1 -= 1
			b.append(b1)
		else:
			b.append(0)
		pref -= 8
	return str(b[0]) + "." + str(b[1]) + "." + str(b[2]) + "." + str(b[3])

def write_to_file(f1,line1):
	print("writing " + f1)
	try:
		of=open(f1,"w")
		for i in line1:
			of.write(i + "\n")
		of.close()
	except PermissionError:
		print("permission error")

def write_to_file_config(f1,config):
	print("writing " + f1)
	try:
		of=open(f1,"w")
		of.write(config)
		of.close()
	except PermissionError:
		print("permission error")

def list_bridge(d1):
	vm_list=list(d1['vm'].keys())
	retval=[]
	bridge1=[]
	for i in vm_list:
		#print("host ",i)
		for j in d1['vm'][i]['interfaces'].keys():
			if j not in ["lo0","irb"]:
				if d1['vm'][i]['interfaces'][j]['bridge'] != 'external': 
					if d1['vm'][i]['interfaces'][j]['bridge'] not in bridge1:
						bridge1.append(d1['vm'][i]['interfaces'][j]['bridge'])
	for i in bridge1:
		retval.append('  bridge "' + i + '"{};')
	retval.append('  bridge "reserved_bridge"{};')
	for i in d1['vm'].keys():
		if d1['vm'][i]['os']=='vqfx':
			retval.append('  bridge "' + i + 'INT"{};')
	retval.append('  PRIVATE_BRIDGES')
	return retval

def get_bridge_name(intf):
	if isinstance(intf,list):
		return intf[0]
	elif isinstance(intf,str):
		return intf

def change_intf(intf):
	return intf.replace('em','eth')
# def change_intfx(intf):
#	return intf.replace('em','ens3f')

def make_config_generic_pc(d1,i):
	retval=[]
	#config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# print("Make config for GW for vm ",i)
	retval.append('vm "'+i+'" {')
	retval.append('   hostname "'+i+'";')
	if 'disk' in d1['vm'][i].keys():
		temp_s1="    " + d1['vm'][i]['os'].upper() + "_" + d1['vm'][i]['disk'].upper() +  "_DISK"
	else:
		temp_s1="    " + d1['vm'][i]['os'].upper() +  "_DISK"
	retval.append(temp_s1)
	if 'hd2' in d1['vm'][i].keys():
		# disk "hdb" "/vmm/data/user_disks/irzan/vm/vmware/esxi3disk2.vmdk";
		retval.append(("     disk \"hdb\" \"{}{}-disk2.img\";").format(config_dir,i))
	if d1['vm'][i]['type'] in ['pchpv1','pchpv2','ssrr']:
		retval.append('   setvar "+qemu_args" "-cpu host,+vmx";')
	else:
		retval.append('   setvar "+qemu_args" "-cpu qemu64,+vmx";')
	retval.append('   ncpus ' + str(param1.vm_type[d1['vm'][i]['type']]['ncpus']) + ';')
	retval.append('   memory ' + str(param1.vm_type[d1['vm'][i]['type']]['memory']) + ';')
	if 'vnc' in d1['vm'][i]:
		if (d1['vm'][i]['vnc']):
			retval.append('   setvar "enable_vnc" "1";')
	for j in d1['vm'][i]['interfaces'].keys():
		retval.append('   interface "' +  j + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')
	return retval

def make_gw_config(d1,i):
	retval=[]
	# config_dir=param1.home_dir + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	retval.extend(make_config_generic_pc(d1,i))
	retval.append('};')
	return retval

def make_pc_config(d1,i):
	retval=[]
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	retval.extend(make_config_generic_pc(d1,i))
	retval.append('   install "' + config_dir + 'lab.conf" "/lab.conf";' )
	retval.append('};')
	return retval

def make_vmware_config(d1,i):
	retval=[]
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	retval.append('vm "'+i+'" {')
	retval.append('   hostname "'+i+'";')
	if d1['vm'][i]['os'] == 'vcsa':
		temp_s1="   " + d1['vm'][i]['os'].upper() +  "_DISK"
		retval.append(temp_s1)
		temp_s0= d1['pod']['home_dir'] + "/" + d1['images'][i] + '";'
		temp_s1='   disk "hdb" "' + temp_s0.replace(".","disk2.")
		retval.append(temp_s1)
		# temp_s1="    " + d1['vm'][i]['os'].upper() +  "DISK2_DISK"
		# retval.append(temp_s1)

	elif d1['vm'][i]['os'] == 'esxi':
		temp_s1="   " + d1['vm'][i]['os'].upper() + str(d1['vm'][i]['disk']) +  "_DISK"
		retval.append(temp_s1)
		if check_vsan_status(d1):
			disk_name = 'esxi' + str(d1['vm'][i]['disk']) + ".vmdk\";"
			temp_s0= d1['pod']['home_dir'] +'/vm/' + d1['name'] + "/" + disk_name
			temp_s1='   disk "hdb" "' + temp_s0.replace(".","disk2.")
			retval.append(temp_s1)
			temp_s1='   disk "hdc" "' + temp_s0.replace(".","disk3.")
			retval.append(temp_s1)

	if d1['vm'][i]['type'] == 'esxi':
		retval.append('   setvar "+qemu_args" "-cpu host,+vmx";')
	else:
		retval.append('   setvar "+qemu_args" "-cpu qemu64,+vmx";')
	retval.append('   ncpus ' + str(param1.vm_type[d1['vm'][i]['type']]['ncpus']) + ';')
	retval.append('   memory ' + str(param1.vm_type[d1['vm'][i]['type']]['memory']) + ';')
	if 'vnc' in d1['vm'][i]:
		if (d1['vm'][i]['vnc']):
			retval.append('   setvar "enable_vnc" "1";')
	for j in d1['vm'][i]['interfaces'].keys():

		#retval.append('   interface "' +  j.replace('em','vio') + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')
		retval.append('   interface "' +  j + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')

	retval.append('   install "' + config_dir + "hostname." + i + '" "/hostname";')
	retval.append('};')
	return retval

def make_junos_config(d1,i):
	retval=[]
	# print("Make config for Junos for vm ",i)
	if d1['vm'][i]['os']=='vmx' or d1['vm'][i]['os']=='mx960' or d1['vm'][i]['os']=='mx480' or d1['vm'][i]['os']=='mx240':
		retval=make_vmx_config(d1,i)
	elif d1['vm'][i]['os']=='vqfx':
		retval=make_vqfx_config(d1,i)
	elif d1['vm'][i]['os']=='vsrx':
		 retval=make_vsrx_config(d1,i)
	elif d1['vm'][i]['os']=='vex':
		 retval=make_vex_config(d1,i)
	elif d1['vm'][i]['os']=='vrr':
		 retval=make_vrr_config(d1,i)
	elif d1['vm'][i]['os']=='evo':
		 retval=make_evo_config(d1,i)
	return retval

def evo_get_intf(d1,i):
	retval=[]
	intf_list= list(d1['vm'][i]['interfaces'].keys())
	intf_list.sort()
	#print(intf_list)
	for j in intf_list:
		if 'et' in j:
			retval.append("            EVOVPTX_CONNECT(IF_ET("+ j.split('-')[1].replace('/',',') + "), " + d1['vm'][i]['interfaces'][j]['bridge'] + ")")
	return retval

def vmx_get_intf(d1,i):
	retval=[]
	intf_list= list(d1['vm'][i]['interfaces'].keys())
	intf_list.sort()
	#print(intf_list)
	for j in intf_list:
		if 'ge' in j:
			retval.append("            VMX_CONNECT(GE("+ j.split('-')[1].replace('/',',') + "), " + d1['vm'][i]['interfaces'][j]['bridge'] + ")")
	return retval

def make_evo_config(d1,i):
	retval=[]
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	if 'inet' not in d1['vm'][i]['interfaces']['mgmt']['family'].keys():
		print("where is the ip address ? ")
		exit
	else:
		retval.append("   ")
		# retval.append("   #undef EM_IPADDR")
		# retval.append("   #define EM_IPADDR interface \"em0\" { bridge \"" + d1['vm'][i]['interfaces']['mgmt']['bridge'] + "\";};")
		#retval.append("   #undef EVOVPTX_RE_MGMT_BRIDGE_NAME")
		#retval.append("   #define EVOVPTX_RE_MGMT_BRIDGE_NAME {}".format(d1['vm'][i]['interfaces']['mgmt']['bridge']))
		retval.append("   #undef    PTX_CHAS_NAME")
		retval.append("   #undef    EVOvArdbeg_RE_MEMORY")
		retval.append("   #define PTX_CHAS_NAME  {}".format(i))
		retval.append("   #define EVOvArdbeg_RE_MEMORY 8192")
		retval.append("       EVOVPTX_CHASSIS_START_ (PTX_CHAS_NAME)")
		retval.append("          EVOvArdbegRE(PTX_CHAS_NAME,EVOVPTX_DISK1)")
		retval.append("          EVOvArdbeg_CSPP_START(PTX_CHAS_NAME,EVOVPTX_FPC_CSPP_IMG)")
		retval.append("             EVOVPTX_CONNECT(IF_ET (0, 0, 0), {})".format(d1['vm'][i]['interfaces']['mgmt']['bridge']))
		retval.extend(evo_get_intf(d1,i))
		retval.append("          EVOvArdbeg_CSPP_END")
		retval.append("       EVOVPTX_CHASSIS_END_")
	return retval

def make_vmx_config(d1,i):
	retval=[]
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	#print(f"Host {i}")
	
	if 'inet' not in d1['vm'][i]['interfaces']['mgmt']['family'].keys():
		print("where is the ip address ? ")
		exit
	else:
		retval.append("   ")
		retval.append("   #undef EM_IPADDR")
		retval.append("   #define EM_IPADDR interface \"em0\" { bridge \"" + d1['vm'][i]['interfaces']['mgmt']['bridge'] + "\";};")
		if d1['vm'][i]['os'] == 'vmx': 
			retval.append("   #define VMX_CHASSIS_I2CID 161")
		elif d1['vm'][i]['os'] == 'mx960': 
			retval.append("   #define VMX_CHASSIS_I2CID 21")
		elif d1['vm'][i]['os'] == 'mx480': 
			retval.append("   #define VMX_CHASSIS_I2CID 33")
		elif d1['vm'][i]['os'] == 'mx240': 
			retval.append("   #define VMX_CHASSIS_I2CID 48")
		retval.append("   #define VMX_CHASSIS_NAME " + i)
		retval.append("   VMX_CHASSIS_START() ")
		retval.append("      VMX_RE_START("+i+"_re,0)")
		retval.append("         VMX_RE_INSTANCE("+i+"_re0, VMX_DISK0, VMX_RE_I2CID,0)")
		retval.append("         install \"" + config_dir + i + ".conf\" \"/root/junos.base.conf\";")
		retval.append("      VMX_RE_END");
		retval.append("      VMX_MPC_START("+i+"_MP,0)")
		#retval.append("        VMX_MPC_INSTANCE("+i+"_MPC, VMX_DISK1, VMX_MPC_I2CID, 0)")
		retval.append("        VMX_MPC_INSTANCE("+i+"_MPC, VMX_DISK0, VMX_MPC_I2CID, 0)")
		# retval.append("        VMX_MPC_INSTANCE("+i+"_MPC, PFE_DISK, VMX_MPC_I2CID, 0)")
		retval.extend(vmx_get_intf(d1,i))
		retval.append("      VMX_MPC_END");
		retval.append("   VMX_CHASSIS_END");
		retval.append("   #undef VMX_CHASSIS_I2CID")
		retval.append("   #undef VMX_CHASSIS_NAME")
	return retval

def make_vqfx_config(d1,i):
	# creating config for RE of VQFX
	retval=[]
	# print("make config for VQFX ",i)
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	retval.append('')
	retval.append('   vm "'+i +'_re" {')
	retval.append('      hostname "'+i+'_re";')
	retval.append('      VQFX_RE')
	#retval.append('      memory 4096;')
	#retval.append('      ncpus 2;')
	retval.append('      setvar "boot_noveriexec" "YES";')
	retval.append('      setvar "qemu_args" "-smbios type=1,product=QFX10K-11";')
	retval.append("      install \"" + config_dir + i + ".conf\" \"/root/junos.base.conf\";")
	# mgmt_bridge=get_bridge_name(d1['vm'][i]['interfaces']['em0'])
	mgmt_bridge=d1['vm'][i]['interfaces']['mgmt']['bridge']
	retval.append('      interface "em0" { bridge "' + mgmt_bridge + '"; };')
	retval.append('      interface "em1" { bridge "' + i + "INT" + '"; ipaddr "169.254.0.2"; };')
	retval.append('      interface "em2" { bridge "reserved_bridge"; };')
	intf_list=[]
	for j in d1['vm'][i]['interfaces'].keys():
		if 'xe' in j:
			intf_list.append(j)	
	intf_list.sort()
	print(intf_list)
	for j in intf_list:
		intf_name = "em" + str(int(j.split("/")[2]) + 3)
		retval.append('      interface "' +  intf_name + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')
	retval.append('   };')

	# creating config for COSIM of VQFX
	retval.append('   vm "'+i +'_cosim" {')
	retval.append('      hostname "'+i+'_cosim";')
	retval.append('      VQFX_COSIM')
	retval.append('      memory 4096;')
	retval.append('      ncpus 2;')
	retval.append('      interface "em0" { bridge "' + mgmt_bridge + '"; };')
	retval.append('      interface "em1" { bridge "' + i + "INT" + '"; ipaddr "169.254.0.1"; };')
	retval.append('   };')
	retval.append('')
	return retval

def make_vsrx_config(d1,i):
	retval=[]
	mgmt_bridge=d1['vm'][i]['interfaces']['mgmt']['bridge']
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	intf_list=[]
	# print("make config for srx ",i)
	retval.append('vm "'+i+'" {')
	retval.append('   hostname "'+i+'";')
	retval.append('      VSRXDISK')
	retval.append('      memory 4096;')
	retval.append('      ncpus 2;')
	retval.append('      setvar "qemu_args" "-cpu qemu64,+vmx,+ssse3,+sse4_1,+sse4_2,+aes,+avx,+pat,+pclmulqdq,+rdtscp,+syscall,+tsc-deadline,+x2apic,+xsave";')
	retval.append("         install \"" + config_dir + i + ".conf\" \"/root/junos.base.conf\";")
	retval.append('      interface "vio0" { bridge "' + mgmt_bridge + '"; };')
	# print(intf_list)
	for j in d1['vm'][i]['interfaces'].keys():
		if 'ge' in j:
			intf_list.append(j)	
	intf_list.sort()
	for j in intf_list:
		intf_name = "vio" + str(int(j.split("/")[2]) + 1)
		retval.append('      interface "' +  intf_name + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')
	retval.append('};')
	return retval

def make_vex_config(d1,i):
	retval=[]
	mgmt_bridge=d1['vm'][i]['interfaces']['mgmt']['bridge']
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	intf_list=[]
	# print("make config for srx ",i)
	retval.append(f"vm \"{i}\" {{")
	retval.append(f"   hostname \"{i}\";")
	retval.append('      VEXDISK')
	retval.append('      memory 16384;')
	retval.append('      ncpus 4;')
	retval.append('      setvar "+qemu_args" "-cpu host,+vmx";')
	# retval.append('      setvar "qemu_args" "-cpu qemu64,+vmx,+ssse3,+sse4_1,+sse4_2,+aes,+avx,+pat,+pclmulqdq,+rdtscp,+syscall,+tsc-deadline,+x2apic,+xsave";')
	#retval.append("         install \"" + config_dir + i + ".conf\" \"/root/junos.base.conf\";")
	retval.append(f"         install \"{config_dir}{i}.conf\" \"/root/junos.base.conf\";")
	#retval.append('      interface "vio0" { bridge "' + mgmt_bridge + '"; };')
	retval.append(f"      interface \"vio0\" {{ bridge \"{mgmt_bridge}\"; }};")
	# print(intf_list)
	for j in d1['vm'][i]['interfaces'].keys():
		if 'ge' in j:
			intf_list.append(j)	
	intf_list.sort()
	for j in intf_list:
		intf_name = "vio" + str(int(j.split("/")[2]) + 1)
		#retval.append('      interface "' +  intf_name + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')
		retval.append(f"      interface \"{intf_name}\" {{ bridge \"{d1['vm'][i]['interfaces'][j]['bridge']}\";}};")
	retval.append('};')
	return retval

def make_veos_config(d1,i):
	#print("creating veos_config")
	retval=[]
	mgmt_bridge=d1['vm'][i]['interfaces']['mgmt']['bridge']
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	intf_list=[]
	# print("make config for srx ",i)
	retval.append(f"vm \"{i}\" {{")
	retval.append(f"   hostname \"{i}\";")
	retval.append('      VEOS_CDROM')
	retval.append('      VEOSDISK')
	retval.append('      memory 4096;')
	retval.append('      ncpus 2;')
	retval.append('      setvar "+qemu_args" "-cpu host,+vmx";')
	# retval.append('      setvar "qemu_args" "-cpu qemu64,+vmx,+ssse3,+sse4_1,+sse4_2,+aes,+avx,+pat,+pclmulqdq,+rdtscp,+syscall,+tsc-deadline,+x2apic,+xsave";')
	#retval.append("         install \"" + config_dir + i + ".conf\" \"/root/junos.base.conf\";")
	retval.append(f"         install \"{config_dir}lab.conf\" \"/lab.conf\";")
	#retval.append('      interface "vio0" { bridge "' + mgmt_bridge + '"; };')
	retval.append(f"      interface \"em0\" {{ bridge \"{mgmt_bridge}\"; }};")
	# print(intf_list)
	for j in d1['vm'][i]['interfaces'].keys():
		if 'ge' in j:
			intf_list.append(j)	
	intf_list.sort()
	for j in intf_list:
		intf_name = "em" + str(int(j.split("/")[2]) + 1)
		#retval.append('      interface "' +  intf_name + '" { bridge "' + d1['vm'][i]['interfaces'][j]['bridge'] + '";};')
		retval.append(f"      interface \"{intf_name}\" {{ bridge \"{d1['vm'][i]['interfaces'][j]['bridge']}\";}};")
	retval.append('};')
	return retval

def make_vrr_config(d1,i):
	retval=[]
	mgmt_bridge=d1['vm'][i]['interfaces']['mgmt']['bridge']
	em1_bridge=d1['vm'][i]['interfaces']['em1']['bridge']
	config_dir=d1['pod']['home_dir'] + '/vm/' + d1['name'] + "/"
	# config_dir=param1.home_dir + d1['pod']['user'] + '/' + d1['name'] + "/"
	intf_list=[]
	print("make config for vrr ",i)
	retval.append('vm "'+i+'" {')
	retval.append('   hostname "'+i+'";')
	retval.append('      VRRDISK')
	retval.append('      memory 4096;')
	retval.append('      ncpus 2;')
	retval.append('      setvar "qemu_args" "-cpu qemu64,+vmx,+ssse3,+sse4_1,+sse4_2,+aes,+avx,+pat,+pclmulqdq,+rdtscp,+syscall,+tsc-deadline,+x2apic,+xsave";')
	# retval.append('      setvar "qemu_args" "-cpu qemu64";')
	retval.append("         install \"" + config_dir + i + ".conf\" \"/root/junos.base.conf\";")
	retval.append('      interface "em0" { bridge "' + mgmt_bridge + '"; };')
	retval.append('      interface "em1" { bridge "' + em1_bridge + '"; };')
	retval.append('};')
	return retval

def init_junos(d1,vm=""):
	print("this is for init junos")
	list_of_jvm=[]
	for i in d1['vm'].keys():
		if d1['vm'][i]['os'] in ['vex','evo']:
			list_of_jvm.append(i)
	if list_of_jvm:
		if vm:
			#print(f"VM is {vm}")
			if vm not in list_of_jvm:
				print(f"VM {vm} is not configured in this topology")
			else:
				send_init(d1,vm)
				config_junos(d1,vm)
		else:
			print("list of virtual junos ",list_of_jvm)
			for i in list_of_jvm:
				send_init(d1,i)
			config_junos(d1)


def connect_to_vm(d1,i):
	ssh_gw = connect_to_gw(d1)
	host_ip = get_mgmt_ip(d1,i)
	user_id, passwd = get_user(d1,i)
	jumphost_transport=ssh_gw.get_transport()
	src_addr=(d1['gw_ip'],22)
	if d1['vm'][i]['type']=='junos':
		dest_addr=(d1['vm'][i]['interfaces']['mgmt']['family']['inet'].split('/')[0],22)
	else:
		dest_addr=(d1['vm'][i]['interfaces']['em0']['family']['inet'].split('/')[0],22)
	#print(f"source address {src_addr[0]}, destination address {dest_addr[0]}")
	jumphost_channel = jumphost_transport.open_channel("direct-tcpip", dest_addr, src_addr)
	ssh=paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# ssh.connect(hostname=d1['pod']['vmmserver'],username=d1['pod']['user'],password=d1['pod']['unixpassword'],sock=jumphost_channel)
	ssh.connect(hostname=host_ip,username=user_id,password=passwd,sock=jumphost_channel)
	return ssh

def config_junos(d1,vm=""):
	if not vm:
		print("this is put configuration into vEX and vEVO")
		list_of_jvm=[]
		for i in d1['vm'].keys():
			if d1['vm'][i]['os'] in ['vex','evo']:
				list_of_jvm.append(i)
		if list_of_jvm:
			print("list of virtual junos ",list_of_jvm)
			#d1['gw_ip']=get_ip_vm(d1,'gw')
			for i in list_of_jvm:
				#print(f"To vm {i}")
				upload_to_vm(d1,i)
	else:
		upload_to_vm(d1,vm)

def upload_to_vm(d1,i):
	local1 = f"./tmp/{i}.conf"
	remote1= f"~/{i}.conf"
	print(f"uploading file {local1} to {i}")
	ssh2host=connect_to_vm(d1,i)
	scp = SCPClient(ssh2host.get_transport())
	scp.put(local1,remote1)
	scp.close()
	cmd1 = f"edit ; load merge relative {i}.conf ; commit"
	print(f"executing {cmd1}")
	s1,s2,s3=ssh2host.exec_command(cmd1)
	for i in s2.readlines():
		print(i)
	ssh2host.close()

def send_init(d1,i):
	status=0
	my_hash_root = md5_crypt.hash(d1['junos_login']['password'])
	my_hash = md5_crypt.hash(d1['junos_login']['password'])
	#cmd1="vmm serial -t " + i
	ip_mgmt = d1['vm'][i]['interfaces']['mgmt']['family']['inet']
	br_mgmt = d1['vm'][i]['interfaces']['mgmt']['bridge']
	gateway4 = get_gateway4(d1,i)
	junos_status=0
	print("configuring ",i)
	if d1['vm'][i]['os'] == 'vex':
		junos_status=1
		c1=f"ssh vmm 'vmm serial -t {i}'"
		print(f"COMMAND {c1}")
		s_e = [
				["","login:"],
				["root","root@"],
				["cli","root>"],
				["configure","root#"],
				["delete interfaces fxp0","root#"],
				["delete chassis","root#"],
				["delete protocols","root#"],
				["delete system processes dhcp-service","root#"],
				["set system host-name " + i,"root#"],
				[f"set system root-authentication encrypted-password \"{my_hash_root}\"","root#"],
				["set system services ssh","root#"],
				["set system services netconf ssh","root#"],
				[f"set system login user {d1['junos_login']['login']} class super-user authentication encrypted-password \"{my_hash}\"","root#"],
				[f"set interfaces fxp0 unit 0 family inet address {ip_mgmt}","root#"],
				["set system management-instance","root#"],
				[f"set routing-instances mgmt_junos routing-options static route 0.0.0.0/0 next-hop {gateway4}", "root#"],
				["set chassis network-services enhanced-ip","root#"],
				["set snmp community public authorization read-only","root#"],
				["commit",f"root@{i}#"],
				["exit",f"root@{i}>"],
				["exit","root@:~ #"],
				["exit","login:"]
			] 
			## [f"set system login user {d1['junos_login']['login']} authentication ssh-rsa \"{d1['pod']['ssh_key']}\"","root#"],
	elif d1['vm'][i]['os'] == 'evo':
		junos_status=1
		c1=f"ssh vmm 'vmm serial -t {i}_RE0'"
		print(f"COMMAND {c1}")
		s_e = [
				["","login:"],
				["root","root@re0:~#"],
				["cli","root@re0>"],
				["configure","root@re0#"],
				["delete system commit","root@re0#"],
				["delete chassis","root@re0#"],
				["set system host-name " + i,"root@re0#"],
				[f"set system root-authentication encrypted-password \"{my_hash_root}\"","root@re0#"],
				["set system services ssh","root@re0#"],
				["set system services netconf ssh","root@re0#"],
				[f"set system login user {d1['junos_login']['login']} class super-user authentication encrypted-password \"{my_hash}\"","root@re0#"],
				[f"set interfaces re0:mgmt-0 unit 0 family inet address {ip_mgmt}","root@re0#"],
				["set system management-instance","root@re0#"],
				[f"set routing-instances mgmt_junos routing-options static route 0.0.0.0/0 next-hop {gateway4}", "root@re0#"],
				["set snmp community public authorization read-only","root@re0#"],
				[f"commit",f"root@{i}#"],
				[f"exit",f"root@{i}>"],
				["exit","root@re0:~#"],
				["exit","login:"]
			]
			## [f"set system login user {d1['junos_login']['login']} authentication ssh-rsa \"{d1['pod']['ssh_key']}\"","root@re0#"],
	if junos_status:
		p1=pexpect.spawn(c1)
		for j in s_e:
			print(f"send :{j[0]}")
			p1.sendline(j[0])
			print(f"expect : {j[1]}")
			p1.expect(j[1], timeout=240)
		p1.close()

