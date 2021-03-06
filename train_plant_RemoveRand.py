import numpy as np
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim
import torch.nn.functional as F
import torch.optim.lr_scheduler as lr_scheduler
import time
import os
import glob
from itertools import combinations
import torchvision
import torch.optim as optim
import torch.backends.cudnn as cudnn


from datasets import miniImageNet_few_shot
import configs
import backbone
from methods.protonet import ProtoNet



from datasets import ISIC_few_shot, EuroSAT_few_shot, CropDisease_few_shot, Chest_few_shot




def clone_BN_affine(model):
    BN_statistics_list = []
    for layer in model.modules():
        if isinstance(layer, nn.BatchNorm2d):
            BN_statistics_list.append(
                {'weight': layer.weight.clone(),
                 'bias': layer.bias.clone()})
    return BN_statistics_list


def clone_BN_stat(model):
    BN_statistics_list = []
    for layer in model.modules():
        if isinstance(layer, nn.BatchNorm2d):
            BN_statistics_list.append(
                {'means': layer.running_mean.clone(),
                 'vars': layer.running_var.clone()})
    return BN_statistics_list


def regret_affine(source_affine, model):
    i = 0
    for layer in model.modules():
        if isinstance(layer, nn.BatchNorm2d):
            layer.bias = nn.Parameter(source_affine[i]['bias'])
            layer.weight = nn.Parameter(source_affine[i]['weight'])
            i += 1
    return model

def regret_stat(source_stat, model):
    i = 0
    for layer in model.modules():
        if isinstance(layer, nn.BatchNorm2d):
            layer.running_mean = nn.Parameter(source_stat[i]['means'])
            layer.running_var = nn.Parameter(source_stat[i]['vars'])
            i += 1
    return model

def shift_affine(source_stat, model):
    total_shift = 0
    i = 0
    for layer in model.modules():
        if isinstance(layer, nn.BatchNorm2d):
            target_mean = layer.running_mean.clone()  # source state
            source_mean = source_stat[i]['means']
            shift_value = (target_mean - source_mean)
            total_shift += torch.sum(shift_value)

            hb_value = 0.1
            # shift bias
            layer.bias = nn.Parameter((torch.ones_like(source_mean).cuda() * shift_value.cuda() * hb_value.cuda()).cuda() + layer.bias).cuda()
            i += 1
    return total_shift, model


def reset_last_block(model):
    last_layer_pos = -3 

    #Breakdown layers into blocks
    layers = [layer[1] for layer in model.named_children()]

    last_layer = layers[last_layer_pos]

    #Breakdown last layer into blocks
    blocks = [block[1] for block in last_layer.named_children()]

    #reset the last block of the last layer
    for name, layer in blocks[-1].named_children():

        if name != 'relu':
            layer.reset_parameters()
    
    return(model)


def sbm_finetune(source_loader, target_loader, target_name , num_epochs, ): 
    

    ###############################################################################################
    # load pretrained model on miniImageNet
    save_dir = './logs/remove_rand/eurosat/'    
    model = torchvision.models.resnet18(pretrained = False)
    model.load_state_dict(torch.load('./logs/resnet18_imgnet.tar'))

    model.fc = nn.Linear(512, 64)
    model.cuda()
    model.train()
    #classifier.cuda()

    for epoch in range(num_epochs):
        

        
        ###############################################################################################
       
        loss_MSE = nn.MSELoss()
        loss_CE = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr = 0.001, weight_decay = 0.0001)
        ###############################################################################################


        train_accuracy = 0.0
        train_loss = 0.0
        num_batches = 0

        for i, (images, labels) in enumerate(base_loader):
            
            source_images = Variable(images.cuda())
            source_labels = Variable(labels.cuda())

            optimizer.zero_grad()

            source_outputs = model(source_images)

            source_affine = clone_BN_affine(model)
            source_stat = clone_BN_stat(model)

            ###############################################
            
            target_batch, _ = next(iter(target_loader))
            target_batch = Variable(target_batch.cuda())

            model.eval()

            target_output = model(target_batch)
            model = shift_affine(source_stat, model)

            ###############################################

            shifted_scores = model(source_images)
            
            model.train()


            model = regret_affine(source_affine, model)

            ###############################################


            ce_loss = loss_CE(source_outputs, source_labels)
            mse_loss = loss_MSE(shifted_scores, source_outputs)

            loss = ce_loss + mse_loss

            loss.backward()
            optimizer.step()

            train_loss += loss.cpu().data*images.size(0)
            _, prediction = torch.max(source_outputs.data, 1)

            train_accuracy += int(torch.sum(prediction == source_labels.data))
            num_batches += 1
            print("Epoch{}__batch{}".format(epoch, num_batches))
            

        print("epoch: {}/{}".format(epoch, num_epochs))
        if (epoch % 25==0):
            #utfile = os.path.join(params.checkpoint_dir, '{:d}.tar'.format(epoch))
            torch.save(model.state_dict(), save_dir + '{}_epoch{}_eurosat_sbm_removeRand.pth'.format(target_name, epoch))



if __name__=='__main__':
    
    seed_ = 2021
    np.random.seed(seed_)
    torch.manual_seed(seed_)
    cudnn.deterministic = True
    ##################################################################
    epochs = 401
    image_size = 224
    
    #mini_imagenet_path = '/content/miniImagenet/'
    base_loader = miniImageNet_few_shot.get_data_loader(configs.miniImageNet_path, batch_size = 16)


    ##################################################################
    pretrained_dataset = "miniImageNet"

    dataset_names = [ "CropDisease"]
    unlabelled_loaders = []

    #print ("Loading ISIC")
    #datamgr             =  ISIC_few_shot.SetDataManager(image_size, n_eposide = iter_num, n_query = 15, **few_shot_params)
    #novel_loader        = datamgr.get_data_loader(aug =False)
    #novel_loaders.append(novel_loader)
    
    #print ("Loading EuroSAT")
    ##unlabelled_path = '/content/eurosat_unlabel'
    #unlabelled_loader = miniImageNet_few_shot.unlabelled_loader(configs.EuroSAT_unlabelled_path, batch_size = 16)
    #unlabelled_loaders.append(unlabelled_loader)
    
    print ("Loading CropDisease")
    unlabelled_loader = miniImageNet_few_shot.unlabelled_loader(configs.CropDisease_unlabelled_path, batch_size = 16)
    unlabelled_loaders.append(unlabelled_loader)
    
    #print ("Loading ChestX")
    #datamgr             =  Chest_few_shot.SetDataManager(image_size, n_eposide = iter_num, n_query = 15, **few_shot_params)
    #novel_loader        = datamgr.get_data_loader(aug =False)
    #novel_loaders.append(novel_loader)
    
    #########################################################################
    for idx, novel_loader in enumerate(unlabelled_loaders):
        print (dataset_names[idx])

        unlabelled_loader = unlabelled_loaders[idx]
        
        # replace finetine() with your own method
        sbm_finetune(base_loader, unlabelled_loader, dataset_names[idx], epochs)

