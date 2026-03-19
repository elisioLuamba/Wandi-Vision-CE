#include <AccelStepper.h>

AccelStepper motor_esteira1(1, 39, 40); // Motor (Passo, Direção)
#define ENABLE_motor_esteira1 41

// Sensores (mantidos para uso futuro)
#define S1_esteira1 42 
#define S2_esteira1 43 

float speed = 900.0; // Velocidade definida

void setup() {
  Serial.begin(9600); // Canal de comunicação com o Python

  // Configuração do motor
  motor_esteira1.setMaxSpeed(speed);
  motor_esteira1.setSpeed(0); // Inicia parado
  
  pinMode(ENABLE_motor_esteira1, OUTPUT);
  digitalWrite(ENABLE_motor_esteira1, LOW); // Ativa o driver (Geralmente LOW ativa no A4988/TB6600)

  pinMode(S1_esteira1, INPUT);
  pinMode(S2_esteira1, INPUT);
  
  Serial.println("Arduino Pronto. Aguardando Operador...");
}

void loop() {
  // 1. Verifica se há ordens do Python
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    if (comando == 'T') {
      motor_esteira1.setSpeed(speed); // Vai para frente
    } 
    else if (comando == 'F') {
      motor_esteira1.setSpeed(-speed); // Vai para trás (Trás/Reverse)
    }
    else if (comando == 'S') {
      motor_esteira1.setSpeed(0); // Stop/Para
    }
  }

  // 2. Executa o passo do motor (Esta função não bloqueia o código)
  motor_esteira1.runSpeed();
}