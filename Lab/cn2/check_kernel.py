#!/usr/bin/env python3

import os
import requests

HUB_STAT=True
if 'HUB_USER' not in os.environ.keys():
	HUB_STAT=False
if 'HUB_PASSWD' not in os.environ.keys():
	HUB_STAT=False
if not HUB_STAT:
	print("HUB_USER or/and HUB_PASSWD are not set")
else:
	hub_user=os.environ['HUB_USER']
	hub_passwd=os.environ['HUB_PASSWD']
	HUB_URL='https://hub.juniper.net/v2/_catalog'
	r = requests.get(HUB_URL, auth=(hub_user, hub_passwd))
	if r.status_code == 200:
		d1=r.json()
		for i in d1['repositories']:
			if 'cn2' in i:
				if 'contrail-vrouter-kernel-init' in i:
					print(i)

	





