#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

//=========================
// WiFi
//=========================

const char* ssid = "VIVOFIBRA-3E11";
const char* password = "BXciRnVctS";

//=========================
// API
//=========================

const char* API_HOST = "192.168.15.5:3000"; // ajuste o IP

//=========================
// Sensor ultrassônico - nível
//=========================

const int PINO_TRIG = 5; // D1
const int PINO_ECHO = 4; // D2

const float PROFUNDIDADE_CM = 30.0;
const float DIST_CHEIO_CM = 0.0;

const int MAQUINA_ID = 11;

const unsigned long INTERVALO_LEITURA_MS = 60000;
unsigned long ultimaLeitura = 0;

const float VARIACAO_MINIMA_PERCENT = 5.0;
float ultimoNivelEnviado = -1;

//=========================
// RFID (RC522)
//=========================

#define PINO_SDA  15 // D8
#define PINO_RST  16 // D0

MFRC522 leitor(PINO_SDA, PINO_RST);

String ultimoUidConsultado = "";

//=========================
// Servo defletor - direciona conforme o material
//=========================

const int PINO_SERVO_DEFLETOR = 2; // D4

Servo servoDefletor;

const int ANGULO_NEUTRO   = 90;  // posição de repouso, centralizado
const int ANGULO_LATINHA  = 0;  // gira pra um lado se for latinha
const int ANGULO_OUTRO    = 180; // gira pro outro lado se não for

const unsigned long TEMPO_SEGURANDO_POSICAO_MS = 5000; // tempo parado na posição antes de voltar ao neutro

//=========================

void conectarWiFi() {

  Serial.print("Conectando ao WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println();
  Serial.println("WiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

}

//=========================

void configurarSensorUltrassonico() {
  pinMode(PINO_TRIG, OUTPUT);
  pinMode(PINO_ECHO, INPUT);
  digitalWrite(PINO_TRIG, LOW);
}

void configurarRfid() {
  SPI.begin();
  leitor.PCD_Init();
  Serial.println("Leitor RFID pronto.");
}

void configurarServoDefletor() {
  servoDefletor.attach(PINO_SERVO_DEFLETOR);
  servoDefletor.write(ANGULO_NEUTRO);
}

//=========================
// Sensor - nível (%)
//=========================

float calcularNivelPercent() {

  digitalWrite(PINO_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PINO_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PINO_TRIG, LOW);

  long duracao = pulseIn(PINO_ECHO, HIGH, 30000);

  if (duracao == 0) {
    Serial.println("Leitura inválida do sensor (timeout).");
    return -1;
  }

  float distanciaCm = duracao / 58.2;

  Serial.print("Distância medida: ");
  Serial.print(distanciaCm);
  Serial.println(" cm");

  float nivel = 100.0 * (PROFUNDIDADE_CM - distanciaCm) /
                (PROFUNDIDADE_CM - DIST_CHEIO_CM);

  if (nivel < 0) nivel = 0;
  if (nivel > 100) nivel = 100;

  return nivel;

}

void enviarNivel(float nivelPercent) {

  WiFiClient client;
  HTTPClient http;

  String url = "http://" + String(API_HOST) + "/api/v1/maquinas/" + String(MAQUINA_ID);

  if (!http.begin(client, url)) {
    Serial.println("Falha ao iniciar HTTP (nível)");
    return;
  }

  http.addHeader("Content-Type", "application/json");

  String json = "{\"nivel\":" + String(nivelPercent, 1) + "}";

  int codigo = http.sendRequest("PATCH", json);

  Serial.print("PATCH nível -> HTTP: ");
  Serial.println(codigo);

  http.end();

}

//=========================
// RFID - lê UID se presente
//=========================

String lerUidSePresente() {

  /*if (!leitor.PICC_IsNewCardPresent()) return "";
  if (!leitor.PICC_ReadCardSerial()) return "";

  String uid = "";
  for (byte i = 0; i < leitor.uid.size; i++) {
    if (leitor.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(leitor.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  leitor.PICC_HaltA();*/

  return "933F210C";

}

// Só identifica o usuário (sem disparar a reciclagem ainda)
bool consultarUsuarioPorRfid(String uid, String &nomeEncontrado) {

  WiFiClient client;
  HTTPClient http;

  String url = "http://" + String(API_HOST) + "/api/v1/perfis/rfid/" + uid;

  if (!http.begin(client, url)) {
    Serial.println("Falha ao iniciar HTTP (RFID)");
    return false;
  }

  int codigo = http.GET();
  bool encontrado = false;

  if (codigo == 200) {

    String resposta = http.getString();
    StaticJsonDocument<512> doc;

    if (!deserializeJson(doc, resposta)) {
      nomeEncontrado = doc["dados"]["nome"].as<String>();
      encontrado = true;
    }

  } else if (codigo == 404) {
    Serial.println("Cartão não cadastrado.");
  } else {
    Serial.print("Erro inesperado: ");
    Serial.println(http.errorToString(codigo));
  }

  http.end();

  return encontrado;

}

//=========================
// Dispara a classificação da IA + credita pontos + move o servo
//=========================

void dispararReciclagem(String uid) {

  WiFiClient client;
  HTTPClient http;

  String url = "http://" + String(API_HOST) + "/api/v1/perfis/rfid/" + uid + "/reciclar";

  if (!http.begin(client, url)) {
    Serial.println("Falha ao iniciar HTTP (reciclar)");
    return;
  }

  http.setTimeout(15000); // dá tempo pra IA processar (a inferência sozinha já leva uns 5s)

  http.addHeader("Content-Type", "application/json");

  int codigo = http.POST(""); // corpo vazio -- a API só precisa do uid na URL

  Serial.print("POST reciclar -> HTTP: ");
  Serial.println(codigo);

  if (codigo == 200) {

    String resposta = http.getString();

    StaticJsonDocument<1024> doc;
    DeserializationError erro = deserializeJson(doc, resposta);

    if (erro) {
      Serial.print("Erro ao interpretar resposta: ");
      Serial.println(erro.c_str());
    } else {

      String material = doc["dados"]["classificacao"]["material"].as<String>();
      float confianca = doc["dados"]["classificacao"]["confianca"].as<float>();
      int pontosGanhos = doc["dados"]["pontosGanhos"].as<int>();
      int pontosTotal = doc["dados"]["perfil"]["pontos"].as<int>();

      bool ehLatinha = (material == "latinha");

      Serial.println();
      Serial.println("========================");
      Serial.print("Material: ");
      Serial.print(material);
      Serial.print(" (");
      Serial.print(confianca);
      Serial.println("% de confiança)");
      Serial.print("Pontos ganhos: ");
      Serial.println(pontosGanhos);
      Serial.print("Total de pontos: ");
      Serial.println(pontosTotal);
      Serial.println("========================");

      // Move o servo defletor para o lado correspondente
      servoDefletor.write(ehLatinha ? ANGULO_LATINHA : ANGULO_OUTRO);

      delay(TEMPO_SEGURANDO_POSICAO_MS); // segura na posição por um tempo (simula o objeto caindo)

      servoDefletor.write(ANGULO_NEUTRO); // volta pro centro, pronto pro próximo

    }

  } else {
    Serial.print("Erro ao reciclar: ");
    Serial.println(http.errorToString(codigo));
  }

  http.end();

}

//=========================

void setup() {

  Serial.begin(115200);

  configurarSensorUltrassonico();
  configurarRfid();
  configurarServoDefletor();

  conectarWiFi();

}

//=========================

void loop() {

  // ---- RFID: identifica e, se novo, dispara a reciclagem completa ----
  // MODO TESTE: como o UID está fixo (sem leitor físico), dispara a cada
  // X segundos em vez de depender do UID mudar. Trocar de volta para a
  // lógica original quando o RC522 estiver lendo cartões de verdade.
  const unsigned long INTERVALO_TESTE_MS = 8000; // a cada 8 segundos
  static unsigned long ultimoTesteMs = 0;

  String uid = lerUidSePresente();

  if (uid.length() > 0 && millis() - ultimoTesteMs >= INTERVALO_TESTE_MS) {

    ultimoTesteMs = millis();

    Serial.print("Cartão detectado! UID: ");
    Serial.println(uid);

    delay(50);
    
    float nivelAtual = calcularNivelPercent();

    if (nivelAtual >= 85) {

      Serial.println("Armazenamento cheio! Cadastro/login bloqueado até esvaziar.");

    } else {

      String nome;
      bool encontrado = consultarUsuarioPorRfid(uid, nome);

      if (encontrado) {

        Serial.print("Usuário validado: ");
        Serial.println(nome);

        dispararReciclagem(uid);

      }

    }

    ultimoUidConsultado = uid;

  } else if (uid.length() == 0) {

    ultimoUidConsultado = "";

  }

  // ---- Sensor de nível ----
  if (millis() - ultimaLeitura >= INTERVALO_LEITURA_MS) {

    ultimaLeitura = millis();

    float nivelPercent = calcularNivelPercent();

    if (nivelPercent < 0) return;

    Serial.print("Nível: ");
    Serial.print(nivelPercent);
    Serial.println("%");

    bool primeiraLeitura = (ultimoNivelEnviado < 0);
    bool mudouSignificativamente =
        fabs(nivelPercent - ultimoNivelEnviado) >= VARIACAO_MINIMA_PERCENT;

    if (primeiraLeitura || mudouSignificativamente) {
      enviarNivel(nivelPercent);
      ultimoNivelEnviado = nivelPercent;
    }

  }

}
