
#include <BluetoothSerial.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>


// ============================================================
// OLED
// ============================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

#define OLED_SDA 21
#define OLED_SCL 22

#define OLED_ADDR 0x3C


// ============================================================
// Bluetooth
// ============================================================

BluetoothSerial SerialBT;


// ============================================================
// OLED Object
// ============================================================

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  -1
);


// ============================================================
// Variables
// ============================================================

String input = "";

String mode = "INFO";

String lyric = "";

String song = "";

String artist = "";


// ============================================================
// OLED Display
// ============================================================

void showOLED(String text) {

  display.clearDisplay();

  display.setTextColor(
    SSD1306_WHITE
  );

  display.setTextSize(1);

  int y = 0;

  int start = 0;

  while (
    start < text.length()
    && y < 64
  ) {

    int end = text.indexOf(
      '\n',
      start
    );

    if (end == -1) {
      end = text.length();
    }

    display.setCursor(
      0,
      y
    );

    display.println(
      text.substring(
        start,
        end
      )
    );

    y += 8;

    start = end + 1;
  }

  display.display();
}


// ============================================================
// Process Bluetooth Command
// ============================================================

void processCommand(String command) {

  command.trim();


  // ==========================================================
  // HANDSHAKE
  // ==========================================================

  if (command == "HELLO") {

    SerialBT.println(
      "TYMusicV2"
    );

    Serial.println(
      "Handshake: TYMusicV2"
    );

    return;
  }


  // ==========================================================
  // MODE
  // ==========================================================

  if (
    command.startsWith(
      "MODE="
    )
  ) {

    mode = command.substring(
      5
    );

    Serial.println(
      "MODE: " + mode
    );

    return;
  }


  // ==========================================================
  // LYRIC
  // ==========================================================

  if (
    command.startsWith(
      "LYRIC="
    )
  ) {

    lyric = command.substring(
      6
    );

    Serial.println(
      "LYRIC: " + lyric
    );

    showOLED(
      lyric
    );

    return;
  }


  // ==========================================================
  // INFO
  // ==========================================================

  if (
    command.startsWith(
      "INFO="
    )
  ) {

    String data =
      command.substring(
        5
      );

    int p1 =
      data.indexOf(
        '|'
      );

    int p2 =
      data.indexOf(
        '|',
        p1 + 1
      );

    if (
      p1 != -1
      && p2 != -1
    ) {

      song =
        data.substring(
          0,
          p1
        );

      artist =
        data.substring(
          p1 + 1,
          p2
        );


      Serial.println(
        "SONG: " + song
      );

      Serial.println(
        "ARTIST: " + artist
      );


      display.clearDisplay();

      display.setTextColor(
        SSD1306_WHITE
      );

      display.setTextSize(1);


      display.setCursor(
        0,
        0
      );

      display.println(
        "TYMusicV2"
      );


      display.setCursor(
        0,
        16
      );

      display.println(
        song
      );


      display.setCursor(
        0,
        32
      );

      display.println(
        artist
      );


      display.display();
    }

    return;
  }
}


// ============================================================
// SETUP
// ============================================================

void setup() {

  // ----------------------------------------------------------
  // Serial Monitor
  // ----------------------------------------------------------

  Serial.begin(
    115200
  );


  // ----------------------------------------------------------
  // OLED
  // ----------------------------------------------------------

  Wire.begin(
    OLED_SDA,
    OLED_SCL
  );


  if (
    !display.begin(
      SSD1306_SWITCHCAPVCC,
      OLED_ADDR
    )
  ) {

    Serial.println(
      "OLED failed"
    );

    while (true) {
      delay(1000);
    }
  }


  // ----------------------------------------------------------
  // Initial OLED
  // ----------------------------------------------------------

  display.clearDisplay();

  display.setTextColor(
    SSD1306_WHITE
  );

  display.setTextSize(1);


  display.setCursor(
    0,
    0
  );

  display.println(
    "TYMusicV2"
  );


  display.setCursor(
    0,
    16
  );

  display.println(
    "Bluetooth"
  );


  display.setCursor(
    0,
    32
  );

  display.println(
    "Waiting..."
  );


  display.display();


  // ----------------------------------------------------------
  // Bluetooth
  // ----------------------------------------------------------

  SerialBT.begin(
    "TYMusicV2"
  );


  // ----------------------------------------------------------
  // Serial Monitor
  // ----------------------------------------------------------

  Serial.println(
    "======================"
  );

  Serial.println(
    "TYMusicV2"
  );

  Serial.println(
    "Bluetooth: TYMusicV2"
  );

  Serial.println(
    "Waiting for connection"
  );

  Serial.println(
    "======================"
  );
}


// ============================================================
// LOOP
// ============================================================

void loop() {

  while (
    SerialBT.available()
  ) {

    char c =
      SerialBT.read();


    if (
      c == '\n'
    ) {

      processCommand(
        input
      );

      input = "";

    } else {

      input += c;
    }
  }
}