import os
import sys
import time
import random
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

sys.stdout.reconfigure(line_buffering=True)

# 12 Target Classes: 10 Fruits/Vegetables + Meat + Bakery
FOOD_CLASSES = [
    "apple",
    "banana",
    "bellpepper",
    "carrot",
    "cucumber",
    "mango",
    "meat",
    "orange",
    "potato",
    "strawberry",
    "tomato",
    "bakery",
]
CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(FOOD_CLASSES)}
IDX_TO_CLASS = {i: cls_name for i, cls_name in enumerate(FOOD_CLASSES)}

class FoodTypeDataset(Dataset):
    def __init__(self, samples: List[Tuple[Path, int]], transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            with open(path, "rb") as f:
                img = Image.open(f).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), (0, 0, 0))

        if self.transform:
            img = self.transform(img)

        return img, label

def collect_samples(dataset_root: Path, max_per_class: int = 300, seed: int = 42) -> Tuple[List, List]:
    random.seed(seed)
    fv_base = dataset_root / "dataset_raw" / "fruits_vegetables" / "Unified_Dataset"
    meat_base = dataset_root / "dataset_raw" / "meat" / "Meat Freshness.v1-new-dataset.multiclass"
    bread_base = dataset_root / "dataset_raw" / "bread"
    sample_uploads = dataset_root / "sample_uploads"

    all_samples_by_class = {cls_name: [] for cls_name in FOOD_CLASSES}

    # 1. Collect Fruits & Vegetables
    for cls_name in FOOD_CLASSES:
        if cls_name in ["meat", "bakery"]:
            continue
        cls_dir = fv_base / cls_name
        if cls_dir.exists():
            for subfolder in ["fresh", "rotten"]:
                sub_p = cls_dir / subfolder
                if sub_p.exists():
                    for f in sub_p.iterdir():
                        if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                            all_samples_by_class[cls_name].append((f, CLASS_TO_IDX[cls_name]))

    # 2. Collect Meat
    if meat_base.exists():
        for subfolder in ["train", "valid"]:
            sub_p = meat_base / subfolder
            if sub_p.exists():
                for f in sub_p.iterdir():
                    if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                        all_samples_by_class["meat"].append((f, CLASS_TO_IDX["meat"]))

    # 3. Collect Bakery (with 4x augmentation oversampling)
    bakery_files = []
    if bread_base.exists():
        bakery_files.extend([f for f in bread_base.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    if (sample_uploads / "bakery").exists():
        bakery_files.extend([f for f in (sample_uploads / "bakery").iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    
    if bakery_files:
        # Oversample 4x to create ~250-300 augmented training samples
        for f in bakery_files * 4:
            all_samples_by_class["bakery"].append((f, CLASS_TO_IDX["bakery"]))

    train_samples = []
    val_samples = []

    print("[Dataset Collection] Scanning and sampling balanced classes:")
    for cls_name in FOOD_CLASSES:
        pool = all_samples_by_class[cls_name]
        random.shuffle(pool)
        selected = pool[:max_per_class] if max_per_class > 0 else pool
        
        split_idx = int(len(selected) * 0.8)
        cls_train = selected[:split_idx]
        cls_val = selected[split_idx:]
        
        train_samples.extend(cls_train)
        val_samples.extend(cls_val)
        
        print(f"  • {cls_name:<12}: Total Pool = {len(pool):5d} | Selected = {len(selected):4d} (Train: {len(cls_train)}, Val: {len(cls_val)})")

    random.shuffle(train_samples)
    random.shuffle(val_samples)
    return train_samples, val_samples

def train_food_type_model(
    epochs: int = 3,
    batch_size: int = 32,
    lr: float = 1e-3,
    max_per_class: int = 300,
    save_path: str = "backend/ai/models/mobilenetv2_food_type_cnn.pt"
):
    project_root = Path(__file__).resolve().parent.parent.parent
    log_file_path = project_root / "food_type_training_log.txt"

    class Logger:
        def __init__(self, filepath):
            self.terminal = sys.stdout
            self.log = open(filepath, "w", encoding="utf-8")

        def write(self, message):
            self.terminal.write(message)
            self.terminal.flush()
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(log_file_path)

    print("=" * 80)
    print("  FRESHCO AI — MULTI-CLASS FOOD-TYPE CNN (12 CLASSES)")
    print("=" * 80)
    print(f"Start Time        : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Classes    : {len(FOOD_CLASSES)} classes -> {', '.join(FOOD_CLASSES)}")
    print(f"Target Epochs     : {epochs}")
    print(f"Batch Size        : {batch_size}")
    print(f"Learning Rate     : {lr}")
    print(f"Max Per Class     : {max_per_class}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute Device    : {device}")
    print("=" * 80)

    train_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_samples, val_samples = collect_samples(project_root, max_per_class=max_per_class)
    print(f"\n[Dataset Split] Total Training: {len(train_samples)} | Total Validation: {len(val_samples)}")

    train_loader = DataLoader(
        FoodTypeDataset(train_samples, transform=train_transforms),
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )
    val_loader = DataLoader(
        FoodTypeDataset(val_samples, transform=val_transforms),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )

    print("\n[Model Init] Loading MobileNetV2 pre-trained backbone...")
    weights = models.MobileNet_V2_Weights.DEFAULT
    model = models.mobilenet_v2(weights=weights)
    
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2),
        nn.Linear(in_features, len(FOOD_CLASSES))
    )
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_acc = 0.0
    total_start_time = time.time()

    print("\n" + "=" * 80)
    print("  STARTING TRAINING LOOP")
    print("=" * 80)

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for step, (images, labels) in enumerate(train_loader, 1):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()

            if step % 15 == 0 or step == len(train_loader):
                current_acc = (correct_train / total_train) * 100
                print(f"  [Epoch {epoch}/{epochs} | Step {step:3d}/{len(train_loader)}] Loss: {loss.item():.4f} | Train Acc: {current_acc:.1f}%")

        train_loss = running_loss / total_train
        train_acc = (correct_train / total_train) * 100

        # Validation Phase
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0
        per_class_correct = {i: 0 for i in range(len(FOOD_CLASSES))}
        per_class_total = {i: 0 for i in range(len(FOOD_CLASSES))}

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, predicted = torch.max(outputs, 1)
                total_val += labels.size(0)
                correct_val += (predicted == labels).sum().item()

                for label, pred in zip(labels, predicted):
                    lbl_idx = label.item()
                    per_class_total[lbl_idx] += 1
                    if pred.item() == lbl_idx:
                        per_class_correct[lbl_idx] += 1

        val_loss = val_loss / total_val
        val_acc = (correct_val / total_val) * 100
        epoch_time = time.time() - epoch_start

        print("-" * 80)
        print(f"  >>> EPOCH {epoch}/{epochs} SUMMARY ({epoch_time:.1f}s):")
        print(f"      Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"      Val Loss  : {val_loss:.4f} | Val Acc  : {val_acc:.2f}%")
        print("      Per-Class Validation Accuracy:")
        for idx, cls_name in enumerate(FOOD_CLASSES):
            c_tot = per_class_total[idx]
            c_cor = per_class_correct[idx]
            c_acc = (c_cor / c_tot * 100) if c_tot > 0 else 0
            print(f"        • {cls_name:<12}: {c_cor:2d}/{c_tot:2d} ({c_acc:5.1f}%)")
        print("-" * 80)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            out_p = project_root / save_path
            out_p.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "classes": FOOD_CLASSES,
                "val_acc": val_acc,
            }, str(out_p))
            print(f"  [Checkpoint] New best model saved to: {save_path} (Val Acc: {val_acc:.2f}%)")

    total_time = time.time() - total_start_time
    print("\n" + "=" * 80)
    print(f"  TRAINING COMPLETE ({total_time/60:.2f} minutes)")
    print(f"  Best Validation Accuracy: {best_val_acc:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    train_food_type_model(epochs=3, batch_size=32, max_per_class=300)
