import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import warnings
warnings.filterwarnings("ignore")

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

import tensorflow as tf
tf.get_logger().setLevel("ERROR")

import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
)

# ----------------------------
# Configurações -- ajuste conforme o seu ambiente
# ----------------------------
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
DATASET_DIR = r"D:\Users\0081864\Downloads\SicraiIA\SicraiIA\dataset"
MODEL_PATH = "classificador_latinha_MobNet_3.keras"

# Se o seu modelo foi treinado com rescale=1./255 (MobileNetV2), deixe True.
# Se for o EfficientNetB0 (sem rescale), mude para False.
USAR_RESCALE = True


def montar_test_generator():
    if USAR_RESCALE:
        test_datagen = ImageDataGenerator(rescale=1.0 / 255)
    else:
        test_datagen = ImageDataGenerator()

    test_generator = test_datagen.flow_from_directory(
        f"{DATASET_DIR}/test",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="binary",
        shuffle=False,  # ESSENCIAL: sem shuffle, para bater y_true com y_pred na ordem certa
    )
    return test_generator


def contar_imagens_por_classe(pasta):
    """Conta quantas imagens existem em cada subpasta (classe) de um diretório."""
    contagem = {}
    if not os.path.isdir(pasta):
        return contagem
    for classe in sorted(os.listdir(pasta)):
        caminho_classe = os.path.join(pasta, classe)
        if os.path.isdir(caminho_classe):
            qtd = len([
                f for f in os.listdir(caminho_classe)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp"))
            ])
            contagem[classe] = qtd
    return contagem


def imprimir_balanceamento():
    print("=" * 60)
    print("BALANCEAMENTO DO DATASET")
    print("=" * 60)
    for split in ["train", "validation", "test"]:
        pasta = os.path.join(DATASET_DIR, split)
        contagem = contar_imagens_por_classe(pasta)
        total = sum(contagem.values())
        print(f"\n{split.upper()} (total: {total} imagens)")
        for classe, qtd in contagem.items():
            pct = (qtd / total * 100) if total > 0 else 0
            print(f"  {classe}: {qtd} imagens ({pct:.1f}%)")


def avaliar_modelo():
    print(f"\nCarregando modelo: {MODEL_PATH}")
    modelo = load_model(MODEL_PATH)

    test_generator = montar_test_generator()
    class_indices = test_generator.class_indices  # ex: {'latinhas': 0, 'outros': 1}
    nomes_classes = list(class_indices.keys())
    print(f"Classes encontradas: {class_indices}")

    # Previsões em probabilidade (0 a 1) para todo o conjunto de teste
    y_true = test_generator.classes  # rótulos verdadeiros, na ordem do generator
    y_prob = modelo.predict(test_generator, verbose=1).ravel()
    y_pred = (y_prob >= 0.5).astype(int)

    # ----------------------------
    # Métricas gerais
    # ----------------------------
    acc = accuracy_score(y_true, y_pred)
    precisao = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    try:
        auc = roc_auc_score(y_true, y_prob)
    except ValueError:
        auc = None

    print("\n" + "=" * 60)
    print("MÉTRICAS GERAIS (no conjunto de TESTE)")
    print("=" * 60)
    print(f"Acurácia:  {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Precisão:  {precisao:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-score:  {f1:.4f}")
    if auc is not None:
        print(f"AUC-ROC:   {auc:.4f}")

    # ----------------------------
    # Relatório por classe
    # ----------------------------
    print("\n" + "=" * 60)
    print("RELATÓRIO POR CLASSE")
    print("=" * 60)
    print(classification_report(y_true, y_pred, target_names=nomes_classes, digits=4))

    # ----------------------------
    # Matriz de confusão
    # ----------------------------
    cm = confusion_matrix(y_true, y_pred)
    print("=" * 60)
    print("MATRIZ DE CONFUSÃO")
    print("=" * 60)
    print(f"{'':15s} | Previsto: {nomes_classes[0]:12s} | Previsto: {nomes_classes[1]:12s}")
    print("-" * 60)
    for i, nome_real in enumerate(nomes_classes):
        print(f"Real: {nome_real:10s} | {cm[i][0]:20d} | {cm[i][1]:20d}")

    # Gera e salva a imagem da matriz de confusão
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(nomes_classes)))
    ax.set_yticks(range(len(nomes_classes)))
    ax.set_xticklabels(nomes_classes)
    ax.set_yticklabels(nomes_classes)
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de Confusão")

    for i in range(len(nomes_classes)):
        for j in range(len(nomes_classes)):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=14)

    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig("matriz_confusao_config3.png", dpi=150)
    print("\nImagem da matriz de confusão salva como 'matriz_confusao_config3.png'")

    return {
        "acuracia": acc,
        "precisao": precisao,
        "recall": recall,
        "f1": f1,
        "auc": auc,
        "matriz_confusao": cm,
    }


if __name__ == "__main__":
    imprimir_balanceamento()
    resultados = avaliar_modelo()
    print("\nAvaliação concluída.")