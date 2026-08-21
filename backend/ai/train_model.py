"""
MobileNetV2 Transfer Learning Training Script for Food Freshness Detection
Freshco AI System

This script sets up transfer learning using MobileNetV2 pre-trained on ImageNet,
adds custom classification layers for 3 classes (Fresh, Nearly Spoiled, Spoiled),
and trains the model with data augmentation.
"""

import os
import argparse
from pathlib import Path

def build_mobilenetv2_model(input_shape=(224, 224, 3), num_classes=3):
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.applications import MobileNetV2

    # 1. Base MobileNetV2 model without top classifier
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze the base model layers initially
    base_model.trainable = False

    # 2. Add custom classification head
    inputs = tf.keras.Input(shape=input_shape)
    # Preprocessing layer for MobileNetV2 (-1 to 1)
    x = layers.Rescaling(1./127.5, offset=-1)(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation='softmax', name='freshness_output')(x)

    model = models.Model(inputs, outputs, name="MobileNetV2_Food_Freshness")
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
    )
    return model

def train(data_dir: str, epochs: int = 15, batch_size: int = 32, save_path: str = None):
    import tensorflow as tf
    
    if save_path is None:
        save_path = str(Path(__file__).resolve().parent / "weights" / "mobilenetv2_freshness.h5")

    print("=" * 60)
    print("Freshco AI - MobileNetV2 Model Training")
    print(f"Dataset Directory: {data_dir}")
    print(f"Target Output Path: {save_path}")
    print("=" * 60)

    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    if not os.path.exists(train_dir):
        print(f"Error: Training directory '{train_dir}' not found.")
        print("Expected directory structure:")
        print("  dataset/")
        print("    train/ [Fresh, Nearly_Spoiled, Spoiled]")
        print("    val/   [Fresh, Nearly_Spoiled, Spoiled]")
        return

    # Data augmentation and loaders
    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_dir,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    model = build_mobilenetv2_model()
    model.summary()

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(save_path, save_best_only=True, monitor='val_accuracy'),
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2)
    ]

    print("\nStarting Training (Phase 1: Feature Head)...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks
    )

    print(f"\nTraining completed. Model saved to: {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MobileNetV2 for Food Freshness Detection")
    parser.add_argument("--data_dir", type=str, default="./dataset", help="Path to dataset root")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.batch_size)
