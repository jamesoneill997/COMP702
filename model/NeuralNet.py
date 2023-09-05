import torch
from torch import nn
import torch.nn.functional as TF
from torch.nn import Softmax

class NeuralNet(nn.Module):
    def __init__(self):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(90, (int(90*(2/3)//1) + 6))
        self.relu = nn.ReLU()
        self.l2 = nn.Linear((int(90*(2/3)//1) + 6), 6)
        self.softmax = Softmax(dim=1)
    def forward(self, x):
        output = self.l1(x)
        output = self.relu(output)
        output = self.l2(output)
        output = self.softmax(output)
        return output
