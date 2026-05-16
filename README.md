# 🤖 Wandi-Vision
> *Agora o Wandi pode ver...*

Sistema de visão computacional com inteligência artificial para o robô **Wandi**. Controla uma esteira transportadora em tempo real via gestos de mão detectados por câmera, e monitora automaticamente a passagem de peças com contagem inteligente por cor.

![Python](https://img.shields.io/badge/Python-87%25-3776AB?style=flat-square&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-13%25-00599C?style=flat-square&logo=c%2B%2B&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-0F9D58?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=flat-square&logo=opencv)
![Arduino](https://img.shields.io/badge/Arduino-Serial-00979D?style=flat-square&logo=arduino&logoColor=white)

---

## 📖 Sobre o Projeto

O **Wandi-Vision** é um sistema embarcado de visão computacional que integra duas câmeras, detecção de gestos com IA e comunicação serial com Arduino para controlar uma esteira transportadora industrial. O operador controla o motor da esteira apenas com gestos de mão, enquanto uma segunda câmera monitora a esteira e conta automaticamente as peças que passam.

---

## 🧩 Módulos do Sistema

### 🖐️ Controle por Gestos (Câmera Nativa)
- Usa **MediaPipe Hands** para detectar a posição dos dedos em tempo real
- Identifica se **apenas o indicador** está levantado em cada mão
- Envia comandos de motor ao Arduino via comunicação serial (PySerial)

### 👁️ Wandi CAM (Câmera da Esteira)
- Segunda câmera dedicada a monitorar a esteira transportadora
- Detecta objetos azuis via **filtragem HSV** com OpenCV
- Conta automaticamente cada peça ao cruzar a linha central (X ≈ 320)
- Usa lógica de debounce (`estado_passagem`) para evitar contagem duplicada

### 🖥️ Dashboard Unificado
- Painel 1280×720 com as duas câmeras lado a lado em **letterbox**
- Exibe status do motor, contagem de peças e estado da detecção em tempo real

### ⚙️ Comunicação com Arduino
- Envia instruções ao motor via `serial.Serial` na porta `COM9` a 9600 baud
- Opera em **modo visual** (sem travar) caso o Arduino não seja encontrado

---

## 🤌 Lógica de Gestos → Motor

| Gesto | Comando | Ação |
|---|---|---|
| Indicador esquerdo ↑ | `F` | Motor para **frente** |
| Indicador direito ↑ | `T` | Motor para **trás** (reverso) |
| Ambos os indicadores juntos (dist < 0.10) | `S` | Motor **parado** |
| Qualquer outra posição | `S` | Motor **parado** (segurança) |

> Apenas o indicador deve estar levantado — os demais dedos precisam estar abaixados para o gesto ser reconhecido.

---

## ⌨️ Controles do Teclado

| Tecla | Ação |
|---|---|
| `Q` | Encerra o sistema e desliga o motor com segurança |
| `R` | Zera o contador de peças detectadas |

---

## 🛠️ Stack Tecnológica

| Biblioteca | Uso |
|---|---|
| `mediapipe` | Detecção de mãos e landmarks dos dedos |
| `opencv-python` | Captura de câmera, processamento de imagem e UI |
| `numpy` | Filtragem HSV, criação de canvas e composição de frames |
| `pyserial` | Comunicação serial com o Arduino |
| `math` | Cálculo de distância entre pontas dos dedos |

---

## 🚀 Como Executar

### Pré-requisitos

```bash
pip install opencv-python mediapipe numpy pyserial
```

### Configuração

1. Conecte o Arduino na porta `COM9` (ajuste no código se necessário)
2. Certifique-se de que as câmeras estão nas portas `0` (operador) e `1` (esteira)
3. Carregue o sketch Arduino da pasta `Esteiras_transportadora_1_2/` no seu Arduino

### Execução

```bash
python detectar.py
```

---

## 📁 Estrutura do Projeto

```
Wandi-Vision/
├── detectar.py                      # Script principal (Python)
├── Esteiras_transportadora_1_2/     # Sketch Arduino (C++) para controle do motor
└── .vscode/                         # Configurações do editor
```

---

## 🔧 Configurações Importantes

```python
# Portas de câmera
cap_nativa = cv2.VideoCapture(0)   # Câmera do operador
cap_wandi  = cv2.VideoCapture(1)   # Câmera da esteira

# Porta serial do Arduino
arduino = serial.Serial('COM9', 9600, timeout=1)

# Filtro de cor azul (HSV) para detecção de peças
azul_baixo = np.array([100, 150,  50])
azul_alto  = np.array([140, 255, 255])

# Posição da linha de contagem (centro da tela 640x480)
linha_contagem_x = 320
```

---

## 📌 Tópicos

`arduino` `computer-vision` `robotics` `ia` `belt` `mediapipe` `mediapipe-hands` `wandirobot`

---

*Desenvolvido por [@elisioLuamba](https://github.com/elisioLuamba)*
