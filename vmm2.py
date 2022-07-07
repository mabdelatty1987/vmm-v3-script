#!/usr/bin/env python3

import argparse

def pget(args):
  print(f'pGet called with cmd {args.cmd}')

def pset(args):
  print(f'pSet called with dev {args.dev} with {args.ip}')

parser = argparse.ArgumentParser(description='Create VMM config files.', prog='vmm.py')
parser.add_argument('-f', '--config', type=ascii, default='lab.yaml')
subparsers = parser.add_subparsers(help='sub-command help')
p_upload = subparsers.add_parser('upload', help='upload help')
p_start = subparsers.add_parser('start', help='start VMM')
p_stop = subparsers.add_parser('stop', help='stop VMM')
p_get = subparsers.add_parser('get', help='get cmd')
p_get.add_argument('cmd', choices=['serial', 'vga', 'ip'])
p_get.set_defaults(func=pget)
p_list = subparsers.add_parser('list', help='list infrastructure')
p_set = subparsers.add_parser('set', help='set device')
p_set.set_defaults(func=pset)
p_set.add_argument('dev', choices=['gw','host'])
p_set.add_argument('ip', type=ascii, help='IP address')
args = parser.parse_args()
if hasattr(args, 'func'):
  args.func(args)

print(f'The config file is {args.config}')  