from dotenv import load_dotenv
from gradient import DatasetsClient
import os

class GradientDataset():
    def __init__(self):
        load_dotenv()
        self.dataset = None
        self.datasets_client = DatasetsClient(os.getenv("GRADIENT_SECRET"))
    
    def create(self, name, storage_provider_id):
        datasets_client.create(
        name=name,
        storage_provider_id=storage_provider_id
    )
    def read(self):
        ...
    def update(self):
        ...
    def delete(self):
        ...