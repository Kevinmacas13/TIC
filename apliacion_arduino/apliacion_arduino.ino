#include <SPI.h>
#include <MFRC522.h>           // Librería para el RFID
#include <LiquidCrystal_I2C.h> // Librería para el módulo I2C
#include <Wire.h>
#define RST_PIN 9   // Pin 9 para el reset del RC522
#define SS_PIN 10   // Pin 10 para el SS (SDA) del RC522
#include <Keypad.h> // Librerúa para el  teclado
const byte filas = 4;
const byte columnas = 4;
byte pinesFilas[] = {7, 6, 5, 3};
byte pinesColumnas[] = {A0, A1, A2, A3};
char teclas[4][4] = {{'1', '2', '3', 'A'},
                     {'4', '5', '6', 'B'},
                     {'7', '8', '9', 'C'},
                     {'*', '0', '#', 'D'}};

MFRC522 mfrc522(SS_PIN, RST_PIN); // Crear el objeto para el RC522
Keypad teclado1 = Keypad(makeKeymap(teclas), pinesFilas, pinesColumnas, filas, columnas);
LiquidCrystal_I2C lcd(0x27, 16, 2); // Definir el  LCD
// Mensajes para el LCD
String linea1 = "BIENVENIDO";
String linea2 = "";

const int pinBuzzer = 2; // Constante que contiene el número del pin de Arduino al cual conectamos un buzzer activo
const int pinRelay = 8;
const int pinSensorM = 4;

void setup()
{
  lcd.init();
  lcd.backlight();
  pinMode(pinBuzzer, OUTPUT);        // Definir el pin del Buzzer como Salida
  pinMode(pinRelay, OUTPUT);         // Definir el  pin del Relay como  salida
  pinMode(pinSensorM, INPUT_PULLUP); // Definir el  pin del Relay como  entrada

  Serial.begin(9600); // Iniciar la comunicación  serial
  SPI.begin();        // Iniciar el Bus SPI
  mfrc522.PCD_Init(); // Iniciar  el MFRC522
}

void loop()
{
  // Verificar si alguna tecla fue presionada
  char tecla_presionada = teclado1.getKey();
  // Revisar si hay nuevas tarjetas  presentes
  if (mfrc522.PICC_IsNewCardPresent())
  {
    // Seleccionar la tarjeta
    if (mfrc522.PICC_ReadCardSerial())
    {

      // Enviamos serialemente su UID
      for (byte i = 0; i < mfrc522.uid.size; i++)
      {
        Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
        Serial.print(mfrc522.uid.uidByte[i], HEX);
      }
      Serial.println();
      // Terminamos la lectura de la tarjeta  actual
      mfrc522.PICC_HaltA();
      ActualizarLCD("Lectura tarjeta", "");
      delay(150);
    }
  }
  // Revisar si hay una tecla presionada
  if (tecla_presionada)
  {
    Serial.println(tecla_presionada);
  }

  // Verificar el  monitor Serial
  if (Serial.available() > 0)
  {
    // Lee los datos recibidos
    String datos_recibidos = Serial.readString();
    linea1 = datos_recibidos;
    linea2 = "";
    String cadena1 = "LecturaCorrecta";
    String cadena2 = "CierrePuerta";
    String cadena3 = "Codigo enviado";
    String cadena4 = "Reconocimiento Facial";
    String cadena5 = "Codigo Incorrecto";
    String cadena6 = "Usuario Correcto";
    if (datos_recibidos == cadena1)
    {
      ActivarRelay();
      linea1 = "  Lectura ";
      linea2 = "  Correcta ";
    }
    if (datos_recibidos == cadena2)
    {
      Serial.println(digitalRead(pinSensorM));
      linea1 = "  Cierre ";
      linea2 = "  Puerta ";
    }
    if (datos_recibidos == cadena3)
    {
      ActivarBuzzer();
      linea1 = "Codigo enviado";
      linea2 = " Ingreselo";
    }
    if (datos_recibidos == cadena4)
    {
      ActivarBuzzer();
      linea1 = " Reconocimiento";
      linea2 = " Facial .....";
    }
    if (datos_recibidos == cadena5)
    {
      linea1 = "  Codigo";
      linea2 = " Incorrecto";
    }
    if (datos_recibidos == cadena6)
    {
      ActivarBuzzer();
      linea1 = "  Usuario";
      linea2 = "  Correcto";
    }
  }
  ActualizarLCD(linea1, linea2);
}
// Función para activar el Buzzer
void ActivarBuzzer()
{
  digitalWrite(pinBuzzer, HIGH); // Poner en alto(5V) el pin del buzzer
  delay(1000);                   // Esperar 1 segundo
  digitalWrite(pinBuzzer, LOW);  // Poner en bajo(0V) el pin del buzzer
}

// Función para activar  Relay
void ActivarRelay()
{
  digitalWrite(pinRelay, HIGH);
  // Serial.println("Relay activado");
  delay(1000); // Esperar 4 segundos
  digitalWrite(pinRelay, LOW);
  // Serial.println("Relay Desactivado");
  delay(1000); // Esperar 1 segundo
}

// Función para escribir en el lcd
void ActualizarLCD(String linea1, String linea2)
{
  lcd.clear();         // Limpiar la pantalla del LCD
  lcd.setCursor(0, 0); // Colocar el cursor en la primera línea
  lcd.print(linea1);   // Imprimir la primera línea
  lcd.setCursor(0, 1); // Colocar el cursor en la segunda línea
  lcd.print(linea2);   // Imprimir la segunda línea
  delay(100);
}
