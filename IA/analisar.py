import os
import shutil
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image_dataset_from_directory

# ==== CONFIGURAÇÕES ====
MODELO_PATH = "classificador_latinha.keras"
DIR_TESTE = r"C:\Users\pehfe\Downloads\SicraiIA\dataset\test"
IMG_SIZE = (224, 224)
BATCH_SIZE = 16   # mesmo batch size usado no treino, só por consistência
PASTA_ERROS = "erros_classificacao"

# ==== CARREGA MODELO E DADOS ====
modelo = tf.keras.models.load_model(MODELO_PATH)

dataset_teste = image_dataset_from_directory(
    DIR_TESTE,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

classes = dataset_teste.class_names
caminhos_arquivos = dataset_teste.file_paths

print(f"Ordem das classes detectada: {classes}")  # deve ser algo como ['latinhas', 'outros']

# ==== FAZ AS PREDIÇÕES ====
y_true = []
y_pred = []
confiancas = []

for imagens, rotulos in dataset_teste:
    imagens_normalizadas = imagens / 255.0  # <-- mesmo rescale usado no treino (ImageDataGenerator)
    preds = modelo.predict(imagens_normalizadas, verbose=0)
    pred_classes = (preds > 0.5).astype(int).flatten()
    conf = np.where(pred_classes == 1, preds.flatten(), 1 - preds.flatten())

    y_true.extend(rotulos.numpy())
    y_pred.extend(pred_classes)
    confiancas.extend(conf)

y_true = np.array(y_true)
y_pred = np.array(y_pred)
confiancas = np.array(confiancas)

# ==== IDENTIFICA OS ERROS ====
# Remove a pasta antiga (se existir) e cria uma nova, limpa
if os.path.exists(PASTA_ERROS):
    shutil.rmtree(PASTA_ERROS)
os.makedirs(PASTA_ERROS)

erros = []
for i, (real, previsto, conf, caminho) in enumerate(zip(y_true, y_pred, confiancas, caminhos_arquivos)):
    if real != previsto:
        erros.append({
            "arquivo": caminho,
            "classe_real": classes[real],
            "classe_prevista": classes[previsto],
            "confianca": round(float(conf), 4)
        })
        nome = os.path.basename(caminho)
        destino = os.path.join(
            PASTA_ERROS,
            f"real_{classes[real]}_previu_{classes[previsto]}_{nome}"
        )
        shutil.copy(caminho, destino)

# ==== RELATÓRIO ====
print(f"\nTotal de imagens testadas: {len(y_true)}")
print(f"Total de erros: {len(erros)} ({len(erros)/len(y_true)*100:.2f}%)\n")

for e in erros:
    print(f"{e['arquivo']}  |  real={e['classe_real']}  previsto={e['classe_prevista']}  conf={e['confianca']}")