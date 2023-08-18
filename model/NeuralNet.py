import torch
from torch import nn

class NeuralNet(nn.Module):
    def __init__(self):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(54, (int(54*(2/3)//1) + 6))
        self.relu = nn.ReLU()
        self.l2 = nn.Linear((int(54*(2/3)//1) + 6), 6)
    def forward(self, x):
        output = self.l1(x)
        output = self.relu(output)
        output = self.l2(output)
        return output