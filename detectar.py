import cv2
import mediapipe as mp
import numpy as np
import serial
import time
import math

# --- 1. CONFIGURAÇÃO MEDIAPIPE ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# --- 2. CONFIGURAÇÃO DAS CÂMERAS ---
cap_nativa = cv2.VideoCapture(0)
cap_wandi = cv2.VideoCapture(1)

# Filtro de cor azul (Wandi CAM - Objetos da esteira)
azul_baixo = np.array([100, 150, 50])
azul_alto = np.array([140, 255, 255])

# Variáveis de Contagem
contador_pecas = 0
estado_passagem = False # Evita contar a mesma peça várias vezes
linha_contagem_x = 320  # Posição da linha de contagem (meio da tela 640x480)

# --- 3. CONFIGURAÇÃO SERIAL (ARDUINO) ---
try:
    arduino = serial.Serial('COM9', 9600, timeout=1)
    time.sleep(2)
    print(">>> Conectado ao Arduino com sucesso!")
except Exception as e:
    print(f">>> AVISO: Arduino não encontrado. O sistema rodará apenas a interface visual. Detalhe: {e}")
    arduino = None

estado_atual_esteira = 'S' # Começa com a instrução de Parada

# --- 4. FUNÇÃO DA INTERFACE (LETTERBOX) ---
def redimensionar_com_proporcao(img, largura_alvo, altura_alvo):
    h, w = img.shape[:2]
    proporcao = min(largura_alvo/w, altura_alvo/h)
    nova_largura = int(w * proporcao)
    nova_altura = int(h * proporcao)
    
    img_redimensionada = cv2.resize(img, (nova_largura, nova_altura))
    canvas = np.zeros((altura_alvo, largura_alvo, 3), dtype=np.uint8)
    
    offset_x = (largura_alvo - nova_largura) // 2
    offset_y = (altura_alvo - nova_altura) // 2
    canvas[offset_y:offset_y+nova_altura, offset_x:offset_x+nova_largura] = img_redimensionada
    return canvas

# --- 5. CONFIGURAÇÃO DA JANELA ---
nome_janela = 'DASHBOARD: OPERADOR - TAREFA'
cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
cv2.resizeWindow(nome_janela, 1280, 720)

print(">>> Sistema iniciado. Pressione 'q' para encerrar.")

while True:
    success1, frame_user = cap_nativa.read()
    success2, frame_wandi = cap_wandi.read()

    if not success1 or not success2:
        print("Erro ao ler as câmeras.")
        break

    # Redimensiona previamente para garantir que as coordenadas fiquem consistentes
    frame_user = cv2.resize(frame_user, (640, 480))
    frame_wandi = cv2.resize(frame_wandi, (640, 480))

    # --- PROCESSAMENTO OPERADOR E CONTROLE (NATIVA) ---
    frame_user = cv2.flip(frame_user, 1)
    rgb_user = cv2.cvtColor(frame_user, cv2.COLOR_BGR2RGB)
    res_hands = hands.process(rgb_user)
    
    comando_desejado = 'S' # Padrão: Parado
    
    left_index_up = False
    right_index_up = False
    ponta_esq = None
    ponta_dir = None

    if res_hands.multi_hand_landmarks and res_hands.multi_handedness:
        for lm, hand_info in zip(res_hands.multi_hand_landmarks, res_hands.multi_handedness):
            label = hand_info.classification[0].label # "Left" ou "Right"
            
            # Lógica: Verifica se APENAS o indicador está levantado
            index_up = lm.landmark[8].y < lm.landmark[6].y
            middle_down = lm.landmark[12].y > lm.landmark[10].y
            ring_down = lm.landmark[16].y > lm.landmark[14].y
            pinky_down = lm.landmark[20].y > lm.landmark[18].y
            
            apenas_indicador = index_up and middle_down and ring_down and pinky_down

            if label == "Left":
                cor_mao = (255, 0, 0) # Azul
                if apenas_indicador:
                    left_index_up = True
                    ponta_esq = lm.landmark[8]
            else:
                cor_mao = (0, 255, 0) # Verde
                if apenas_indicador:
                    right_index_up = True
                    ponta_dir = lm.landmark[8]
                    
            mp_draw.draw_landmarks(
                frame_user, lm, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=cor_mao, thickness=2, circle_radius=4),
                mp_draw.DrawingSpec(color=cor_mao, thickness=2)
            )

        # --- Lógica de Controle Final ---
        if left_index_up and right_index_up:
            # Ambos indicadores levantados: verificar se estão unidos para PARAR
            distancia = math.hypot(ponta_esq.x - ponta_dir.x, ponta_esq.y - ponta_dir.y)
            if distancia < 0.10:
                comando_desejado = 'S'
                h, w, _ = frame_user.shape
                cv2.line(frame_user, (int(ponta_esq.x * w), int(ponta_esq.y * h)), 
                                     (int(ponta_dir.x * w), int(ponta_dir.y * h)), (0, 255, 255), 3)
            else:
                comando_desejado = 'S' # Levantados mas separados = para por segurança
        elif left_index_up:
            comando_desejado = 'F' # Indicador Esquerdo = FRENTE
        elif right_index_up:
            comando_desejado = 'T' # Indicador Direito = TRÁS (Reverso)

    # Envio para o Arduino
    if arduino and comando_desejado != estado_atual_esteira:
        arduino.write(comando_desejado.encode())
        estado_atual_esteira = comando_desejado
        print(f"Sinal enviado: {comando_desejado}")

    # --- PROCESSAMENTO WANDI CAM (ÁREA DE TAREFA E CONTAGEM) ---
    frame_wandi = cv2.flip(frame_wandi, 1)
    hsv = cv2.cvtColor(frame_wandi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, azul_baixo, azul_alto)
    conts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detectado = False
    maior_contorno = None
    maior_area = 0

    # Busca o maior objeto na tela para evitar contar ruídos
    for c in conts:
        area = cv2.contourArea(c)
        if area > 800 and area > maior_area:
            maior_area = area
            maior_contorno = c

    if maior_contorno is not None:
        detectado = True
        x, y, w, h = cv2.boundingRect(maior_contorno)
        cx = x + w // 2 # Ponto central X do objeto
        cy = y + h // 2 # Ponto central Y do objeto
        
        # Desenha a caixa no objeto
        cv2.rectangle(frame_wandi, (x, y), (x+w, y+h), (255, 200, 0), 2)
        cv2.circle(frame_wandi, (cx, cy), 5, (0, 0, 255), -1)

        # Lógica de Contagem (Passando pelo centro da tela)
        # Cria uma "faixa" de tolerância entre X=300 e X=340
        if 300 < cx < 340:
            if not estado_passagem:
                contador_pecas += 1
                estado_passagem = True # Bloqueia contagem até o objeto sair da faixa
        elif cx < 280 or cx > 360:
            estado_passagem = False # Objeto saiu da faixa, libera para o próximo

    else:
        estado_passagem = False

    # Desenhar Linha de Contagem e Texto na Wandi CAM
    cv2.line(frame_wandi, (linha_contagem_x, 0), (linha_contagem_x, 480), (0, 255, 255), 2)
    cv2.putText(frame_wandi, f"PECAS DETECTADAS: {contador_pecas}", (20, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)

    # --- CRIAÇÃO DA UI (MOLDURAS) ---
    painel_user = redimensionar_com_proporcao(frame_user, 640, 480)
    painel_wandi = redimensionar_com_proporcao(frame_wandi, 640, 480)

    # Textos da Interface
    texto_motor = f"MOTOR: {estado_atual_esteira} (F=Frente, T=Tras, S=Parado)"
    cor_motor = (0, 255, 0) if estado_atual_esteira in ['F', 'T'] else (0, 0, 255)
    
    cv2.putText(painel_user, "OPERADOR", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
    cv2.putText(painel_user, texto_motor, (20, 80), cv2.FONT_HERSHEY_DUPLEX, 0.6, cor_motor, 1)

    status_cor = (0, 255, 0) if detectado else (0, 0, 255)
    cv2.putText(painel_wandi, "WANDI CAM", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, status_cor, 1)

    # Unir painéis e rodapé
    ui_final = np.hstack((painel_user, painel_wandi))
    footer = np.zeros((40, 1280, 3), dtype=np.uint8)
    cv2.putText(footer, "SISTEMA ATIVO | PRESSIONE 'Q' PARA SAIR | 'R' PARA ZERAR CONTAGEM", (300, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    layout_total = np.vstack((ui_final, footer))

    cv2.imshow(nome_janela, layout_total)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord('q'):
        if arduino:
            arduino.write('S'.encode())
        break
    elif tecla == ord('r'):
        # Permite zerar o contador pressionando a tecla 'R' no teclado
        contador_pecas = 0

# Limpeza
cap_nativa.release()
cap_wandi.release()
if arduino:
    arduino.close()
cv2.destroyAllWindows()