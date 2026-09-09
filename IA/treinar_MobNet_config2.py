import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ----------------------------
# Configurações
# ----------------------------
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15
DATASET_DIR = r"D:\Users\0081864\Downloads\SicraiIA\SicraiIA\dataset"

# ----------------------------
# 1. Preparar os dados com augmentation
# ----------------------------
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    rotation_range=25,
    width_shift_range=0.15,
    height_shift_range=0.15,
    shear_range=0.15,
    zoom_range=0.2,
    horizontal_flip=True,
    brightness_range=[0.7, 1.3],
)

val_datagen = ImageDataGenerator(rescale=1.0 / 255)

train_generator = train_datagen.flow_from_directory(
    f"{DATASET_DIR}/train",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
)

val_generator = val_datagen.flow_from_directory(
    f"{DATASET_DIR}/validation",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
)

print("Classes encontradas:", train_generator.class_indices)
# Deve mostrar algo tipo: {'latinhas': 0, 'outros': 1}

# ----------------------------
# 2. Montar o modelo com transfer learning
# ----------------------------
base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,   # remove a camada final original
    weights="imagenet",
)
base_model.trainable = False  # congela os pesos pré-treinados

# ---- CONFIG 2: cabeça um pouco maior (128 -> 64) ----
model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.3),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(64, activation="relu"),
    layers.Dropout(0.2),
    layers.Dense(1, activation="sigmoid"),  # saída binária: latinha ou não
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
    loss="binary_crossentropy",
    metrics=["accuracy"],
)

model.summary()

# ----------------------------
# 3. Treinar (Fase 1 - base congelada)
# ----------------------------
early_stop_fase1 = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=4, restore_best_weights=True
)

history = model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=val_generator,
    callbacks=[early_stop_fase1],
)

# ----------------------------
# 4. Fine-tuning: descongela parte da base para ganhar mais precisão
# ----------------------------
base_model.trainable = True
for layer in base_model.layers[:-20]:  # mantém a maior parte congelada
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),  # LR bem baixo
    loss="binary_crossentropy",
    metrics=["accuracy"],
)

early_stop_fase2 = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=4, restore_best_weights=True
)

history_fine = model.fit(
    train_generator,
    epochs=15,
    validation_data=val_generator,
    callbacks=[early_stop_fase2],
)

# ----------------------------
# 5. Plotar Loss e Accuracy
# ----------------------------
import matplotlib.pyplot as plt

fase1_epochs = len(history.history["loss"])

loss = history.history["loss"] + history_fine.history["loss"]
val_loss = history.history["val_loss"] + history_fine.history["val_loss"]

accuracy = history.history["accuracy"] + history_fine.history["accuracy"]
val_accuracy = history.history["val_accuracy"] + history_fine.history["val_accuracy"]

epochs_range = range(1, len(loss) + 1)

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(epochs_range, loss, "b-", label="Train Loss")
plt.plot(epochs_range, val_loss, "r-", label="Validation Loss")
plt.axvline(x=fase1_epochs + 0.5, color="gray", linestyle="--", label="Início Fine-tuning")
plt.title("Loss ao longo das épocas - Config 2 (128->64)")
plt.xlabel("Épocas")
plt.ylabel("Loss")
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(epochs_range, accuracy, "b-", label="Train Accuracy")
plt.plot(epochs_range, val_accuracy, "r-", label="Validation Accuracy")
plt.axvline(x=fase1_epochs + 0.5, color="gray", linestyle="--", label="Início Fine-tuning")
plt.title("Accuracy ao longo das épocas - Config 2 (128->64)")
plt.xlabel("Épocas")
plt.ylabel("Accuracy")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig("grafico_config2.png", dpi=150)
plt.show()

# ----------------------------
# 6. Avaliar no conjunto de TESTE (dados que o modelo nunca viu)
# ----------------------------
test_datagen = ImageDataGenerator(rescale=1.0 / 255)

test_generator = test_datagen.flow_from_directory(
    f"{DATASET_DIR}/test",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
    shuffle=False,
)

test_loss, test_acc = model.evaluate(test_generator)
print(f"\nResultado no conjunto de teste -> loss: {test_loss:.4f} | acurácia: {test_acc:.4f}")

# ----------------------------
# 7. Salvar o modelo treinado
# ----------------------------
model.save("classificador_latinha_MobNet_2.keras")
print("Modelo salvo como classificador_latinha_MobNet_2.keras")