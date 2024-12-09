import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os

# Sample reports with updated features
reports = [
    {
        "name": "John Doe",
        "phone_number": "123-456-7890",
        "email": "johndoe@example.com",
        "x_username": "@johndoe",
        "telegram_username": "johndoe_telegram",
        "hair_color": "black",
        "eye_color": "brown",
        "skin_color": "light",
        "ethnicity": "Hispanic",
        "height": 180,  # in cm
        "age": 34,
        "car_license_plate": "XYZ1234",
        "car_model_make": "Toyota Corolla",
        "location": "123 Main St",
        "city_state_country": "Los Angeles, CA, USA",
        "general_occupation": "Teacher",
        "job_title_position": "High School Math Teacher",
        "institution_organization": "Los Angeles Unified School District",
        "incident_details": "Harassed during parent-teacher meeting.",
        "additional_information": "Witnessed by other teachers.",
    },
    {
        "name": "John D.",
        "phone_number": "123-456-7890",
        "email": "johndoe@example.com",
        "x_username": "@johndoe",
        "telegram_username": "johndoe_telegram",
        "hair_color": "black",
        "eye_color": "brown",
        "skin_color": "light",
        "ethnicity": "Mexican",
        "height": 180,  # in cm
        "age": 34,
        "car_license_plate": "XYZ1234",
        "car_model_make": "Toyota Corolla",
        "location": "123 Main St",
        "city_state_country": "Los Angeles, California, USA",
        "general_occupation": "Teacher",
        "job_title_position": "High School Math Teacher",
        "institution_organization": "Los Angeles Unified School District",
        "incident_details": "I was harassed during a parent-teacher meeting.",
        "additional_information": "The incident was witnessed by other teachers.",
    },
    {
        "name": "Jane Smith",
        "phone_number": "987-654-3210",
        "email": "janesmith@example.com",
        "x_username": "@janesmith",
        "telegram_username": "janesmith_telegram",
        "hair_color": "blonde",
        "eye_color": "blue",
        "skin_color": "fair",
        "ethnicity": "Caucasian",
        "height": 165,  # in cm
        "age": 29,
        "car_license_plate": "ABC5678",
        "car_model_make": "Honda Civic",
        "location": "456 Elm St",
        "city_state_country": "New York, NY, USA",
        "general_occupation": "Software Engineer",
        "job_title_position": "Frontend Developer",
        "institution_organization": "TechCorp Inc.",
        "incident_details": "Inappropriate comments made during meeting.",
        "additional_information": "Incident occurred in a meeting room.",
    },
    {
        "name": "Jane S.",
        "phone_number": "987-654-3210",
        "email": "janesmith@example.com",
        "x_username": "@janesmith",
        "telegram_username": "janesmith_telegram",
        "hair_color": "blonde",
        "eye_color": "blue",
        "skin_color": "fair",
        "ethnicity": "White",
        "height": 165,  # in cm
        "age": 29,
        "car_license_plate": "ABC5678",
        "car_model_make": "Honda Civic",
        "location": "456 Elm St",
        "city_state_country": "NYC, NY, USA",
        "general_occupation": "Software Engineer",
        "job_title_position": "Frontend Developer",
        "institution_organization": "TechCorp Inc.",
        "incident_details": "She was making inappropriate comments made during a 1-on-1 meeting.",
        "additional_information": "The incident occurred in a meeting room in our office.",
    },
    {
        "name": "Alex W.",
        "phone_number": "555-567-8901",
        "email": "alexw_unique@example.com",
        "x_username": "@alexw_unq",
        "telegram_username": "alex_unique",
        "hair_color": "Black",
        "eye_color": "Brown",
        "skin_color": "Dark",
        "ethnicity": "African",
        "height": 173,
        "age": 42,
        "car_license_plate": "LMN-456",
        "car_model_make": "BMW 3 Series",
        "location": "789 Oak St, Metropolis",
        "city_state_country": "Metropolis, NY, USA",
        "general_occupation": "Consultant",
        "job_title_or_position": "IT Consultant",
        "specific_institutions_or_organizations": "Tech Solutions Ltd.",
        "incident_details": "The perpetrator behaved aggressively during a professional meetup, making unwanted advances and refusing to leave when asked.",
        "additional_information": "Incident occurred at a technology conference.",
    },
    # Add more reports
]

# Initialize encoders and scaler
hair_color_encoder = LabelEncoder()
eye_color_encoder = LabelEncoder()
skin_color_encoder = LabelEncoder()
ethnicity_encoder = LabelEncoder()
car_model_encoder = LabelEncoder()
occupation_encoder = LabelEncoder()

# Encode categorical features
hair_colors = hair_color_encoder.fit_transform([r["hair_color"] for r in reports])
eye_colors = eye_color_encoder.fit_transform([r["eye_color"] for r in reports])
skin_colors = skin_color_encoder.fit_transform([r["skin_color"] for r in reports])
ethnicities = ethnicity_encoder.fit_transform([r["ethnicity"] for r in reports])
car_models = car_model_encoder.fit_transform([r["car_model_make"] for r in reports])
occupations = occupation_encoder.fit_transform([r["general_occupation"] for r in reports])

# Standardize continuous features
scaler = StandardScaler()
heights = scaler.fit_transform(np.array([r["height"] for r in reports]).reshape(-1, 1))
ages = scaler.fit_transform(np.array([r["age"] for r in reports]).reshape(-1, 1))

# Text embeddings for incident details and additional information
model = SentenceTransformer('all-MiniLM-L6-v2')
incident_embeddings = model.encode([r["incident_details"] for r in reports])
additional_embeddings = model.encode([r["additional_information"] for r in reports])

# Combine all features into a single tensor
node_features = np.column_stack((
    hair_colors, eye_colors, skin_colors, ethnicities, car_models, occupations,
    heights.flatten(), ages.flatten(),
    incident_embeddings, additional_embeddings
))

node_features = torch.tensor(node_features, dtype=torch.float)

# Construct adjacency matrix based on feature similarity
num_reports = len(reports)
adj_matrix = torch.zeros((num_reports, num_reports))

for i in range(num_reports):
    for j in range(num_reports):
        if i != j:
            # Check for shared categorical features or similarity in embeddings
            if (reports[i]["car_license_plate"] == reports[j]["car_license_plate"] or
                reports[i]["email"] == reports[j]["email"] or
                reports[i]["phone_number"] == reports[j]["phone_number"] or
                cosine_similarity([incident_embeddings[i]], [incident_embeddings[j]])[0, 0] > 0.8):
                adj_matrix[i, j] = 1

# Convert adjacency matrix to edge list for PyTorch Geometric
edge_index = adj_matrix.nonzero(as_tuple=False).t()

# Create PyTorch Geometric Data object
data = Data(x=node_features, edge_index=edge_index)

# Define the GNN model
class GNNClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(GNNClassifier, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, output_dim)
        self.fc = nn.Linear(output_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = torch.relu(x)
        x = self.conv2(x, edge_index)
        x = self.fc(x)
        return self.sigmoid(x)

# Initialize model, loss, and optimizer
input_dim = node_features.shape[1]
hidden_dim = 16
output_dim = 8
model = GNNClassifier(input_dim, hidden_dim, output_dim)

criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Prepare labels (binary labels for this example, one for each node)
labels = torch.tensor([1 if i % 2 == 0 else 0 for i in range(len(node_features))], dtype=torch.float)

# Training loop
epochs = 100
for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()
    outputs = model(data.x, data.edge_index).squeeze()
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss.item():.4f}")

# Evaluate the model (optional)
model.eval()
with torch.no_grad():
    predictions = model(data.x, data.edge_index).squeeze()
    print(f"Predictions: {predictions}")

# Export the trained model to ONNX
num_nodes = node_features.shape[0]
dummy_data_x = torch.rand(num_nodes, input_dim, dtype=torch.float32)

# Instead of using nonzero operation, create a fixed edge index
# Make sure this matches your actual edge structure
num_edges = edge_index.shape[1]  # Get number of edges from your actual data
dummy_edge_index = edge_index.clone()  # Use the actual edge index structure

# Get current directory and create file paths
current_dir = os.path.dirname(os.path.abspath(__file__))
onnx_file_path = os.path.join(current_dir, "network.onnx")

# Export the trained model to ONNX
torch.onnx.export(
    model,                             
    (dummy_data_x, dummy_edge_index),  
    onnx_file_path,                    
    export_params=True,                
    opset_version=11,                  
    input_names=['node_features', 'edge_index'],  
    output_names=['output'],
    dynamic_axes=None,  # Force static shapes
    do_constant_folding=True,
    verbose=True
)

print(f"Model exported with:")
print(f"num_nodes: {num_nodes}")
print(f"input_dim: {input_dim}")
print(f"num_edges: {num_edges}")

# Verify the exported model
import onnx
model = onnx.load(onnx_file_path)
onnx.checker.check_model(model)

print(f"Trained model successfully exported to {onnx_file_path}")

# Create and save input.json in the same directory
input_data = {
    "input_data": {
        "node_features": dummy_data_x.tolist(),
        "edge_index": dummy_edge_index.tolist()
    }
}

input_file_path = os.path.join(current_dir, "input.json")
with open(input_file_path, 'w') as f:
    json.dump(input_data, f, indent=2)

print(f"Input data saved to {input_file_path}")

