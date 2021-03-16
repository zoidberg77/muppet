import os
import random
import sys
import argparse
import getpass

# set python path so it points to directory that src is in



import src.app as applic

import tensorboardX as tbx

import torch
import torch.cuda

def parse_command_line_args() : 
    parser = argparse.ArgumentParser(description='PyTorch Pruning')
    parser.add_argument('--config-file', default='None', type=str, help='config file with training parameters')
    args = parser.parse_args()
    return args

def main() : 
    # parse config
    print('==> Parsing Config File')
    args = parse_command_line_args()
    
    username = getpass.getuser()

    if args.config_file != 'None' : 
        app = applic.Application(args.config_file)
    else : 
        raise ValueError('Need to specify config file with parameters')

    app.main()

main()
         
