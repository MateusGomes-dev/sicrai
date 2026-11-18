"""
Servidor de IA - classifica latinha vs não-latinha

Por enquanto (sem câmera física ainda e sem o dataset completo), o
endpoint /classificar-aleatoria escolhe uma imagem AO ACASO da pasta
"erros_classificacao" (que já vem com o projeto, com fotos reais de
latinha e não-latinha) e roda o modelo nela -- simula o que vai
acontecer quando o ESP32-CAM mandar uma foto de verdade.

IMPORTANTE: coloque este arquivo dentro da pasta "IA" do projeto do
site (a mesma pasta onde estão os arquivos .keras e a pasta
erros_classificacao) -- ele usa caminhos relativos à própria posição
do arquivo, então funciona sem precisar editar caminho nenhum.

Instalação:
    pip install flask tensorflow pillow

Rodar:
    python servidor_ia.py
"""

import os
import random
import glob

import numpy as np
from flask import Flask, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

app = Flask(__name__)

IMG_SIZE = (224, 224)

#Pode mudar dependendo do modelo
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
MODELO_PATH = os.path.join(PASTA_SCRIPT, "classificador_latinha_Atual.keras")

# Pasta com imagens de exemplo já incluída no projeto (fotos que o
# modelo errou na avaliação -- serve bem como banco de teste temporário)
PASTA_TESTE = os.path.join(PASTA_SCRIPT, "erros_classificacao")

print("Carregando modelo...")
modelo = load_model(MODELO_PATH)
print("Modelo carregado!")


def escolher_imagem_aleatoria():

    extensoes = ("*.jpg", "*.jpeg", "*.png")
    candidatas = []

    for ext in extensoes:
        candidatas.extend(
            glob.glob(os.path.join(PASTA_TESTE, "**", ext), recursive=True)
        )

    if not candidatas:
        return None

    return random.choice(candidatas)


def classificar(caminho_imagem):

    img = image.load_img(caminho_imagem, target_size=IMG_SIZE)
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    pred = modelo.predict(img_array)[0][0]

    eh_latinha = pred < 0.5
    confianca = (1 - pred) if eh_latinha else pred

    return {
        "material": "latinha" if eh_latinha else "nao_latinha",
        "confianca": round(float(confianca) * 100, 1),
    }


@app.route("/classificar-aleatoria", methods=["GET"])
def classificar_aleatoria():

    caminho = escolher_imagem_aleatoria()

    if caminho is None:
        return jsonify({
            "erro": f"Nenhuma imagem encontrada em {PASTA_TESTE}"
        }), 404

    resultado = classificar(caminho)
    resultado["imagem_usada"] = os.path.basename(caminho)

    return jsonify(resultado), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)