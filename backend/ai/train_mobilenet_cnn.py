import os
import sys
import time
import math
from pathlib import Path
from PIL import Image
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
import torchvision.transforms as transforms
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

root_dir = Path(__file__).resolve().parent.parent.parent
dataset_dir = root_dir / "dataset"
model_dir = root_dir / "backend" / "ai" / "models"
model_dir.mkdir(parents=True, exist_ok=True)
log_file_path = root_dir / "training_log.txt"

def log(msg: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

class FreshnessImageDataset(Dataset):
    def __init__(self, file_paths, labels, transform=None):
        self.file_paths = file_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        path = self.file_paths[idx]
        label = self.labels[idx]
        try:
            # PIL open handles unicode paths safely
            with open(path, 'rb') as f:
                img = Image.open(f).convert('RGB')
        except Exception as e:
            # Fallback black image if corrupted
            img = Image.new('RGB', (224, 224), (0, 0, 0))

        if self.transform:
            img = self.transform(img)

        return img, torch.tensor(label, dtype=torch.long)

def get_balanced_subset(samples_per_class=1000):
    """
    Collects a balanced subset of images across produce and meat categories.
    """
    tier_map = {'fresh': 0, 'nearly_spoiled': 1, 'spoiled': 2}
    class_files = {0: [], 1: [], 2: []}

    for cat in ['fruits_vegetables', 'meat']:
        for tier_name, label in tier_map.items():
            p = dataset_dir / cat / tier_name
            if p.exists():
                files = [f for f in p.glob('*') if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
                class_files[label].extend(files)

    selected_paths = []
    selected_labels = []

    np.random.seed(42)
    for label in [0, 1, 2]:
        files = class_files[label]
        np.random.shuffle(files)
        chosen = files[:samples_per_class]
        selected_paths.extend(chosen)
        selected_labels.extend([label] * len(chosen))
        log(f"Class {label} ({['Fresh', 'Nearly Spoiled', 'Spoiled'][label]}): Selected {len(chosen)} images (from {len(files)} total available)")

    return selected_paths, selected_labels

def run_training_subset(samples_per_class=1000, epochs=3, batch_size=32):
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("=== Freshco AI: MobileNetV2 CNN PyTorch Training Run ===\n")

    log("=" * 70)
    log(f"STARTING MOBILENETV2 CNN TRAINING PIPELINE")
    log(f"Hardware Device: {device} ({'GPU' if device.type == 'cuda' else 'CPU - Intel/AMD Core'})")
    log(f"Architecture: torchvision.models.mobilenet_v2 (Transfer Learning)")
    log(f"Classification Head: nn.Sequential(nn.Dropout(0.2), nn.Linear(1280, 3))")
    log(f"Loss Function: CrossEntropyLoss (Weighted: Fresh=1.0, Nearly=1.0, Spoiled=1.30)")
    log(f"Batch Size: {batch_size}, Target Epochs: {epochs}")
    log("=" * 70)

    # 1. Dataset Collection
    paths, labels = get_balanced_subset(samples_per_class=samples_per_class)
    total_samples = len(paths)
    log(f"Total Dataset Size: {total_samples} images ({samples_per_class} per class)")

    # 2. Train / Val Split (80/20 Stratified)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        paths, labels, test_size=0.20, random_state=42, stratify=labels
    )
    log(f"Train Set: {len(train_paths)} images | Validation Set: {len(val_paths)} images")

    # 3. Data Transforms
    train_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = FreshnessImageDataset(train_paths, train_labels, transform=train_transforms)
    val_dataset = FreshnessImageDataset(val_paths, val_labels, transform=val_transforms)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # 4. Model Setup
    log("Loading pretrained MobileNetV2 weights...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    
    # Freeze feature backbone for faster training and stability on head initialization
    for param in model.features.parameters():
        param.requires_grad = False
    # Unfreeze the last inverted residual block for fine-tuning
    for param in model.features[-2:].parameters():
        param.requires_grad = True

    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2),
        nn.Linear(1280, 3)
    )
    model = model.to(device)

    # 5. Loss & Optimizer (Prioritize Recall on Spoiled with weight 1.30)
    class_weights = torch.tensor([1.0, 1.0, 1.30], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    optimizer = optim.Adam([
        {'params': model.features[-2:].parameters(), 'lr': 1e-4},
        {'params': model.classifier.parameters(), 'lr': 1e-3}
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=2, gamma=0.5)

    # 6. Training Loop
    log("\nStarting Epoch Training Loop...")
    epoch_durations = []

    for epoch in range(1, epochs + 1):
        t_epoch_start = time.time()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        total_batches = len(train_loader)
        for b_idx, (inputs, targets) in enumerate(train_loader):
            t_batch_start = time.time()
            inputs, targets = inputs.to(device), targets.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == targets.data).item()
            total += inputs.size(0)

            if (b_idx + 1) % 15 == 0 or (b_idx + 1) == total_batches:
                b_acc = (correct / total) * 100.0
                b_loss = running_loss / total
                elapsed = time.time() - t_epoch_start
                log(f"  Epoch [{epoch}/{epochs}] Batch [{b_idx + 1}/{total_batches}] - Loss: {b_loss:.4f}, Train Acc: {b_acc:.2f}% ({elapsed:.1f}s)")

        scheduler.step()
        epoch_time = time.time() - t_epoch_start
        epoch_durations.append(epoch_time)
        train_loss = running_loss / total
        train_acc = (correct / total) * 100.0

        # Validation Phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)

                val_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == targets.data).item()
                val_total += inputs.size(0)

                all_preds.extend(preds.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())

        val_loss = val_loss / val_total
        val_acc = (val_correct / val_total) * 100.0

        log(f"--> EPOCH {epoch} COMPLETE: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}% (Duration: {epoch_time:.1f}s)")

    # 7. Final Validation Evaluation & Confusion Matrix
    log("\n" + "=" * 70)
    log("  SUBSET VALIDATION RESULTS (N = " + str(len(all_targets)) + " held-out images)  ")
    log("=" * 70)
    
    cm = confusion_matrix(all_targets, all_preds, labels=[0, 1, 2])
    log("Confusion Matrix (Rows: Ground Truth, Columns: Prediction):")
    log(f"{'':>22} | {'Pred: Fresh':>13} | {'Pred: Nearly':>13} | {'Pred: Spoiled':>13}")
    log("-" * 70)
    log(f"{'Actual: Fresh':>22} | {cm[0, 0]:>13} | {cm[0, 1]:>13} | {cm[0, 2]:>13}")
    log(f"{'Actual: Nearly Spoiled':>22} | {cm[1, 0]:>13} | {cm[1, 1]:>13} | {cm[1, 2]:>13}")
    log(f"{'Actual: Spoiled':>22} | {cm[2, 0]:>13} | {cm[2, 1]:>13} | {cm[2, 2]:>13}")

    class_names = ["Fresh", "Nearly Spoiled", "Spoiled"]
    report = classification_report(all_targets, all_preds, target_names=class_names, digits=4)
    log("\nClassification Report:\n" + report)

    # Save Model Weights
    save_pt_path = model_dir / "mobilenetv2_freshness_cnn.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'architecture': 'mobilenet_v2',
        'trained_samples': total_samples,
        'trained_epochs': epochs,
        'val_acc': val_acc
    }, save_pt_path)
    log(f"\n[Model Saved] PyTorch CNN state dict saved to: {save_pt_path.name}")

    # Full Dataset Time Estimation
    avg_sec_per_image = np.mean(epoch_durations) / len(train_paths)
    full_dataset_images = 31557
    full_train_images = int(full_dataset_images * 0.8)
    est_full_epoch_sec = avg_sec_per_image * full_train_images
    est_full_3epochs_min = (est_full_epoch_sec * 3) / 60.0
    est_full_5epochs_min = (est_full_epoch_sec * 5) / 60.0

    log("\n" + "=" * 70)
    log("  FULL DATASET (31,557 IMAGES) TIME ESTIMATION  ")
    log("=" * 70)
    log(f"Average CPU processing speed: {avg_sec_per_image*1000:.2f} ms per image")
    log(f"Estimated time for 1 full epoch on all {full_train_images} training images: {est_full_epoch_sec/60.0:.1f} minutes")
    log(f"Estimated time for 3 full epochs: {est_full_3epochs_min:.1f} minutes ({est_full_3epochs_min/60.0:.2f} hours)")
    log(f"Estimated time for 5 full epochs: {est_full_5epochs_min:.1f} minutes ({est_full_5epochs_min/60.0:.2f} hours)")
    log("=" * 70)

if __name__ == '__main__':
    run_training_subset(samples_per_class=1000, epochs=3, batch_size=32)
