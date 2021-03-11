import os 
import subprocess
import sys
import torch

import time
import datetime

class Checkpointer(object) : 
    def __init__(self, params, configFile) : 
    #{{{
        self.logfile = None
        self.configFile = configFile
        self.root = self.__get_root_dir(params)
        if params.resume == True : 
            self.created_dir = True
        else : 
            self.created_dir = False

        self.headers = ['Epoch','LR','Train_Loss',\
                        'Train_Top1','Train_Top5','Test_Loss',\
                        'Test_Top1','Test_Top5','Val_Loss',\
                        'Val_Top1','Val_Top5']
    #}}}
        
    def __ensure_last_epoch(self, cp_file, new_dir) : 
    #{{{
        cp_filename = cp_file.split('/')[-1]
        epoch = cp_filename[:cp_filename.index('-')]
        dir_list = os.listdir(new_dir)
        dir_list = [int(x[:x.index('-')]) for x in dir_list if x[0].isdigit()]
        dir_list.sort()
        if int(epoch) != dir_list[-1] : 
            raise ValueError('Resume epoch ({}) is not last epoch run ({}). If you want to run from here, use branch instead of resume'.format(epoch, dir_list[-1]))
    #}}}
    
    def __create_dir(self, new_dir):
    #{{{
        cmd = 'mkdir -p ' + new_dir 
        subprocess.check_call(cmd, shell=True)

        self.created_dir = True
    #}}}

    def __create_log(self, new_dir) :
    #{{{
        self.logfile = os.path.join(new_dir, 'log.csv')
        
        line = ',\t'.join(self.headers) + '\n'
        f = open(self.logfile, 'w+')
        f.write(line)
        f.close()
    #}}}

    def __create_copy_log(self, new_root, old_root, prev_epoch) : 
    #{{{
        self.logfile = os.path.join(new_root, 'log.csv')
        
        src = open(os.path.join(old_root, 'log.csv'), 'r') 
        dst = open(os.path.join(new_root, 'log.csv'), 'w+')

        for i in range(int(prev_epoch) + 2) : 
            line = src.readline()
            dst.write(line)
        dst.write('-----------------------------------------------\n')

        src.close()
        dst.close()
    #}}}
    
    def __get_root_dir(self, params) : 
    #{{{
        assert not (params.branch == True and params.resume == True), 'Cannot branch and resume at the same time. Check config file.'
        if params.printOnly:
            return ''

        # if branch, create new branch directory
        if params.branch == True : 
            cp_file = params.pretrained 
            cp_dir_list = cp_file.split('/')

            cp_dir = os.path.join('/', *cp_dir_list[:-2])
            pth_file = cp_dir_list[-1]
            last_epoch = ''.join(pth_file[:pth_file.index('-')])

            prev_resumes = os.listdir(cp_dir)
            prev_resumes = [x for x in prev_resumes if x != 'orig']
            prev_resumes = [i for i in prev_resumes if last_epoch in i]

            if prev_resumes == [] : 
                new_dir = os.path.join(cp_dir, last_epoch + '-0')
            else : 
                prev_resumes.sort()
                last_run = int(prev_resumes[-1][-1])
                curr_run = last_run + 1
                new_dir = os.path.join(cp_dir, last_epoch + '-' + str(curr_run))
            
            new_dir = os.path.join(new_dir, 'orig')

            return new_dir

        elif params.resume == True : 
            # extract log file and directory from pretrained model path
            cp_file = params.pretrained 
            cp_list = cp_file.split('/')
            new_dir = os.path.join('/', *cp_list[:-1])
            self.logfile = os.path.join(new_dir, 'log.csv')
            
            # check provided checkpoint is the last epoch that was run for that run 
            # raises exception causing program to stop 
            self.__ensure_last_epoch(cp_file, new_dir)
            
            return new_dir

        else :
            ts = time.time()
            timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
            new_dir = os.path.join(params.checkpoint, params.test_name, timeStamp, 'orig')
            return new_dir
    #}}}
    
    def setup_values(self, params):
    #{{{
        self.values = [params.curr_epoch, params.lr, params.train_loss, \
                       params.train_top1, params.train_top5, params.test_loss, \
                       params.test_top1, params.test_top5, params.val_loss, \
                       params.val_top1, params.val_top5]

    #}}}

    def save_checkpoint(self, model_dict, optimiser_dict, params) : 
    #{{{
        if params.printOnly == True:
            return

        # create directory if not done already, this way empty directory is never created
        if self.created_dir == False : 
            self.__create_dir(self.root)
            self.__create_log(self.root)
        
        # copy config file into root dir
        cmd = 'cp ' + self.configFile + ' ' + self.root
        subprocess.check_call(cmd, shell=True)         

        # write to log file
        self.setup_values(params)
        line = [str(x) for x in self.values]
        line = ',\t'.join(line)
        line += '\n'
        with open(self.logfile, 'a') as f :
            f.write(line)

        # create checkpoints to store
        modelpath = os.path.join(self.root, str(params.curr_epoch) + '-model' + '.pth.tar')
        statepath = os.path.join(self.root, str(params.curr_epoch) + '-state' + '.pth.tar')
        
        # store checkpoints
        torch.save(model_dict, modelpath) 
        torch.save(params.get_state(), statepath)
            
        # store best model separately 
        if params.test_top1 >= params.bestValidLoss:
            params.bestValidLoss = params.test_top1
            bestModelPath = os.path.join(self.root, 'best-model' + '.pth.tar')
            bestStatePath = os.path.join(self.root, 'best-state' + '.pth.tar')
            torch.save(model_dict, bestModelPath) 
            torch.save(params.get_state(), bestStatePath)
        #}}}

    def restore_state(self, params): 
    #{{{
        # get state to load from
        if params.resume == True or params.branch == True : 
            file_to_load = params.pretrained.replace('model', 'state')        
            device = 'cuda:' + str(params.gpuList[0])
            prev_state_dict = torch.load(file_to_load, map_location=device)
        
        # if resume, load from old state completely, ignore parameters in config file
        if params.resume == True : 
            # ensure path to pretrained has new path and new state know it is in resume 
            prev_state_dict['pretrained'] = params.pretrained
            prev_state_dict['resume'] = True
            prev_state_dict['gpu_id'] = params.gpu_id
            prev_state_dict['gpuList'] = [int(x) for x in params.gpu_id.split(',')]
            prev_state_dict['workers'] = params.workers
            prev_state_dict['printOnly'] = params.printOnly
            
            params.__dict__.update(**prev_state_dict)

            # update new start epoch as epoch after the epoch that was resumed from
            params.start_epoch = prev_state_dict['curr_epoch'] + 1

        # if there's a branch copy the save state files to new branch folder
        # ignore previous state and use parameters in config file directly
        elif params.branch == True:
            # copy epoch checkpoint from root of branch
            prev_epoch = str(prev_state_dict['curr_epoch'])
            old_root_list = params.pretrained.split('/')
            old_root = os.path.join('/', *old_root_list[:-1])
            
            if not params.printOnly:
                self.__create_dir(self.root)
                self.__create_copy_log(self.root, old_root, prev_epoch)
            
                cmd = 'cp ' + os.path.join(old_root, prev_epoch + '-*') + ' ' + self.root           
                subprocess.check_call(cmd, shell=True)

            params.start_epoch = prev_state_dict['curr_epoch'] + 1

        # if evaluate, use state as specified in config file
        elif params.evaluate == True : 
            pass 

        # if all false, start from epoch 0 and use config file 
        else : 
            params.start_epoch = 0                            

        return params
    #}}}
