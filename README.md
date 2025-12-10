[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/Fruitsmart/SmartPriceCharge-HACS/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

# 🔋 SmartPriceCharge

[](https://github.com/hacs/integration)
[](https://www.home-assistant.io)
[](https://www.google.com/search?q=)

**SmartPriceCharge** ist eine native Home Assistant Integration zur vollautomatischen, intelligenten Steuerung von Heimspeichern.

Anders als statische Zeitpläne nutzt diese Integration eine Kombination aus **Tibber-Strompreisen**, **lokaler PV-Prognose** und deinem **historischen Verbrauch**, um den Speicher wirtschaftlich optimal zu steuern. Dabei berücksichtigt sie die physikalischen Grenzen des Speichers (Kapazität & Ladegeschwindigkeit), um Fehlplanungen zu vermeiden.

## ✨ Features

### 🧠 Smart Logic & Physik

  * **Smart Calculation (Bedarfsrechnung):** Die Integration lädt nicht pauschal. Sie berechnet den Bedarf dynamisch: `(Durchschnittsverbrauch der letzten Tage - PV-Forecast)`. Es wird nur die Differenz aus dem Netz geladen, die die PV voraussichtlich nicht decken kann.
  * **Physics Aware:** Die Planung respektiert die **Akkugröße** und die **maximale Ladegeschwindigkeit**. Es werden nur so viele günstige Tibber-Slots gebucht, wie der Akku in der verfügbaren Zeit physikalisch aufnehmen kann.
  * **Weather Awareness:** Pausiert die Entladung, wenn laut Wetter/Sonnenstand in Kürze direkter PV-Ertrag zu erwarten ist. Das vermeidet unnötige Ladezyklen und schont den Akku.

### 📉 Strategien & Modi

  * **Eco Charge:** Bucht automatisch die günstigsten Stunden des Tages, um den berechneten Ziel-SoC zu erreichen.
  * **Smart Discharge (Dip-Refill):** Entlädt den Akku nur, wenn der Preis-Spread (Jetzt vs. Später) groß genug ist.
  * **Sleep-Over Mode:** Analysiert abends die Preise für den nächsten Morgen (05:00–09:00 Uhr). Sind diese hoch, wird das Entladelimit (Min-SoC) dynamisch angehoben, um Energie für den Morgen zu reservieren.
  * **Panic Mode:** Notladung, falls der Akku leer ist (\< Min-SoC) und in \< 1,5h ein extremer Preis-Peak ansteht.

### ⚙️ Hardware & UX

  * **Inverter-Steuerung:** Setzt aktiv den **DoD/SoC-Slider** am Wechselrichter (getestet mit GoodWe, adaptierbar).
  * **Logic Invert:** Unterstützt Wechselrichter, die DoD (Depth of Discharge) statt SoC nutzen (rechnet automatisch `100 - x`).
  * **Safety Heartbeat:** Sendet regelmäßige Befehle, um Timeouts am Inverter zu verhindern.
  * **Native Config Flow:** Keine YAML-Konfiguration nötig\! Alle Schwellwerte, Sensoren und Optionen sind live über die Home Assistant UI einstellbar.

-----

## 📋 Voraussetzungen

Damit SmartPriceCharge funktioniert, benötigst du:

1.  Eine **Home Assistant** Installation.
2.  Einen dynamischen Stromtarif (z.B. **Tibber**) und die entsprechenden Preissensoren.
3.  Eine PV-Prognose-Integration (Empfehlung: [ha-solar-forecast-ml](https://github.com/Zara-Toorox/ha-solar-forecast-ml) oder Solcast).
4.  Einen steuerbaren Wechselrichter/Speicher, dessen SoC-Limit/Ladestrom via HA gesetzt werden kann.

-----

## 💾 Installation

Da diese Integration (noch) nicht im Standard-HACS-Store ist, muss sie als "Custom Repository" hinzugefügt werden.

### Via HACS (Empfohlen)

1.  Öffne **HACS** in deinem Home Assistant.
2.  Gehe auf **Integrationen**.
3.  Klicke oben rechts auf die **drei Punkte (Menü)** und wähle **Benutzerdefinierte Repositories**.
4.  Füge die URL dieses Repositories in das Feld ein:
    ```text
    https://github.com/Fruitsmart/SmartPriceCharge-HACS
    ```
5.  Wähle als Kategorie **Integration**.
6.  Klicke auf **Hinzufügen**.
7.  Suche nun in HACS nach "SmartPriceCharge" und installiere es.
8.  **Starte Home Assistant neu.**

### Manuelle Installation

1.  Lade den Ordner `custom_components/smart_price_charge` aus diesem Repo herunter.
2.  Kopiere den Ordner in dein Home Assistant Verzeichnis unter `/config/custom_components/`.
3.  Starte Home Assistant neu.

-----

## 🔧 Konfiguration

Nach dem Neustart kannst du die Integration hinzufügen:

1.  Gehe zu **Einstellungen** -\> **Geräte & Dienste**.
2.  Klicke auf **Integration hinzufügen**.
3.  Suche nach **SmartPriceCharge**.
4.  Folge dem Einrichtungsassistenten. Du wirst gebeten, deine Sensoren auszuwählen (z.B. Tibber Preis, Batterie SoC, Forecast Entity).

### Feintuning (Optionen)

Über den **"Konfigurieren"**-Button der Integration kannst du jederzeit folgende Werte anpassen:

  * **Akkukapazität (kWh):** Wichtig für die "Physics Aware"-Berechnung.
  * **Max. Ladegeschwindigkeit (kW):** Um Überbuchung von Slots zu vermeiden.
  * **Preis-Spread:** Ab welchem Preisunterschied soll nachgeladen werden?
  * **Sicherheitspuffer:** Wieviel % SoC sollen immer als Reserve bleiben?

-----

## ⚖️ Haftungsausschluss & Lizenz

Dieses Projekt steht unter der **MIT Lizenz**.

**WICHTIGER HINWEIS:**
Diese Software interagiert direkt mit Hardware (Wechselrichtern, Batteriespeichern) und steuert Lade-/Entladeprozesse. Obwohl die Software mit Sicherheitsmechanismen (z.B. Heartbeats, Plausibilitätschecks) entwickelt wurde, erfolgt die Nutzung **auf eigene Gefahr**.

Der Entwickler übernimmt keine Haftung für:
* Schäden an der Hardware (Inverter, Akku).
* Finanzielle Verluste durch unerwartetes Ladeverhalten (z.B. Laden zu Hochpreisphasen bei API-Fehlern).
* Funktionsstörungen durch Updates von Home Assistant oder Tibber.

Bitte teste die Integration nach der Installation sorgfältig und überwache die ersten Ladezyklen.

-----

## ❤️ Unterstützung

Gefällt dir dieses Projekt? Wenn es dir hilft, Stromkosten zu sparen, freue ich mich über einen Kaffee ☕️

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=fam.obst@live.de&item_name=TibberSmartCharge&currency_code=EUR)


## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.
