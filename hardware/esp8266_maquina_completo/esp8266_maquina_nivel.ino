#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

//=========================
// WiFi
//=========================

const char* ssid = "Hector09910";
const char* password = "Heitor 08";

//=========================
// API (rodando localmente, para testes)
//=========================

// IP da máquina onde "npm run dev" está rodando, na mesma rede WiFi do ESP8266.
// Descubra com "ipconfig" (Windows) ou "ifconfig"/"ip a" (Linux/Mac).
const char* API_BASE =
"http://192.168.179.106:3000/api/v1/maquinas"; // ajuste o IP

const int MAQUINA_ID = 11; // id da linha na tabela "maquinas"

//=========================
// Sensor ultrassônico / calibração de nível
//=========================

const int PINO_TRIG = 5; // GPIO5 (D1)
const int PINO_ECHO = 4; // GPIO4 (D2)

const float PROFUNDIDADE_CM = 30.0; // distância sensor -> fundo quando vazio
const float DIST_CHEIO_CM = 0.0;    // distância quando cheio

const unsigned long INTERVALO_LEITURA_MS = 60000; // 1 leitura por minuto
unsigned long ultimaLeitura = 0;

const float VARIACAO_MINIMA_PERCENT = 5.0;
float ultimoNivelEnviado = -1;

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

//=========================

float calcularNivelPercent() {

  digitalWrite(PINO_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PINO_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PINO_TRIG, LOW);

  long duracao = pulseIn(PINO_ECHO, HIGH, 30000); // timeout 30ms

  if (duracao == 0) {
    Serial.println("Leitura inválida do sensor (timeout).");
    return -1;
  }

  float distanciaCm = duracao * 0.0343 / 2.0;

  Serial.print("Distância medida: ");
  Serial.print(distanciaCm);
  Serial.println(" cm");

  float nivel = 100.0 * (PROFUNDIDADE_CM - distanciaCm) /
                (PROFUNDIDADE_CM - DIST_CHEIO_CM);

  if (nivel < 0) nivel = 0;
  if (nivel > 100) nivel = 100;

  return nivel;

}

//=========================

void enviarNivel(float nivelPercent) {

  WiFiClient client; // HTTP simples, sem TLS -- servidor local na rede

  HTTPClient http;

  String url = String(API_BASE) + "/" + String(MAQUINA_ID);

  if (!http.begin(client, url)) {

    Serial.println("Falha ao iniciar HTTP");

    return;

  }

  http.addHeader(
      "Content-Type",
      "application/json"
  );

  String json =
  "{"
    "\"nivel\":" + String(nivelPercent, 1) +
  "}";

  Serial.println();

  Serial.println("Enviando nível para API...");

  Serial.println(json);

  int codigo = http.sendRequest("PATCH", json);

  Serial.print("HTTP: ");

  Serial.println(codigo);

  if (codigo > 0) {

    Serial.println();

    Serial.println("Resposta:");

    Serial.println(http.getString());

  } else {

    Serial.print("Erro: ");

    Serial.println(http.errorToString(codigo));

  }

  http.end();

}

//=========================

void setup() {

  Serial.begin(115200);

  configurarSensorUltrassonico();

  conectarWiFi();

}

//=========================

void loop() {

  if (millis() - ultimaLeitura >= INTERVALO_LEITURA_MS) {

    ultimaLeitura = millis();

    float nivelPercent = calcularNivelPercent();

    if (nivelPercent < 0) {
      return;
    }

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
