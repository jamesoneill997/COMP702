#custom imports
from model.NeuralNet import NeuralNet
import pandas as pd
import torch
import numpy as np
from torch import nn
from torch.utils.data import Dataset
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler
from torch.utils.data.sampler import SubsetRandomSampler
from datetime import datetime
import torchvision.transforms as transforms

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
class HorseDataset(Dataset):
    def __init__(self, file_name):
        super().__init__()
        file_out = pd.read_csv(file_name, float_precision='round_trip').fillna(value=0)
        x = file_out.iloc[0:1116, 0:54]
        y = file_out.iloc[0:1116, 54]
        x_train = torch.Tensor(x.values)
        y_train = y
        self.X_train = torch.tensor(x_train, dtype=torch.float32)
        self.Y_train = torch.tensor(y_train).type(torch.LongTensor)

    def __len__(self):
        return len(self.Y_train)
    
    def __getitem__(self, idx):
        x = self.X_train[idx]
        y = self.Y_train[idx]
        return x, y
    
dataset = HorseDataset('./reduced_export.csv')
batch_size = 8
testing_split = .2
loss_fn = torch.nn.CrossEntropyLoss()

dataset_size = len(dataset)
print(f'dataset size {dataset_size}')
indices = list(range(dataset_size))
split = int(np.floor(testing_split * dataset_size))

train_indices, test_indices = indices[split:], indices[:split]
neural_net = NeuralNet()
neural_net = neural_net.to(device)

train_sampler = SubsetRandomSampler(train_indices)
test_sampler = SubsetRandomSampler(test_indices)
train_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, 
                                           sampler=train_sampler)
test_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                                                sampler=test_sampler)
optimizer = torch.optim.SGD(neural_net.parameters(), lr=0.001, momentum=0.8)
scheduler = ReduceLROnPlateau(optimizer, 'min')

def train_one_epoch(epoch_index, tb_writer):
    running_loss = 0.
    last_loss = 0.
    
    #for each batch in the training set
    for i, data in enumerate(train_loader):
        inputs, labels = data
        inputs = inputs.to(device)
        labels = labels.to(device)
        neural_net.to(device)
        optimizer.zero_grad()

        outputs = neural_net(inputs)
        loss = loss_fn(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(neural_net.parameters(), 5)
        optimizer.step()
        running_loss += loss.item()
        if i % 112 == 111:
            last_loss = running_loss / 111
            tb_x = epoch_index * len(train_loader) + i + 1
            tb_writer.add_scalar('Loss/train', last_loss, tb_x)
            running_loss = 0.

    return last_loss


timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
writer = SummaryWriter('runs/oddsgenie_trainer_{}'.format(timestamp))
epoch_number = 0

EPOCHS = 2500

best_vloss = 1_000_000.

for epoch in range(EPOCHS):
    print('EPOCH {}:'.format(epoch_number + 1))

    # Make sure gradient tracking is on, and do a pass over the data
    neural_net.train(True)
    avg_loss = train_one_epoch(epoch_number, writer)

    running_vloss = 0.0
    neural_net.eval()

    with torch.no_grad():
        for i, vdata in enumerate(test_loader):
            vinputs, vlabels = vdata
            vinputs = vinputs.to(device)
            vlabels = vlabels.to(device)
            voutputs = neural_net(vinputs)
            vloss = loss_fn(voutputs, vlabels)
            scheduler.step(vloss)
            running_vloss += vloss                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    
    avg_vloss = running_vloss / (i + 1)
    print('LOSS train {} valid {}'.format(avg_loss, avg_vloss))

    writer.add_scalars('Training vs. Validation Loss',
                    { 'Training' : avg_loss, 'Validation' : avg_vloss },
                    epoch_number + 1)
    writer.flush()

    if avg_vloss < best_vloss:
        best_vloss = avg_vloss
        model_path = 'optimal_model'
        torch.save(neural_net.state_dict(), model_path)

    epoch_number += 1