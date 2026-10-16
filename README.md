# Kobra – Python-IDE fürs iPhone

Kobra ist eine Python-Entwicklungsumgebung, die als Web-App läuft und auf dem iPhone (und iPad) wie eine
normale App auf dem Home-Bildschirm liegt. Python 3.14 läuft direkt auf dem Gerät (Pyodide/WebAssembly).
Ein Server, Xcode oder der App Store werden nicht gebraucht. Nach dem ersten Start funktioniert alles offline.

**Funktionen**

- **Projekte mit Ordnern und mehreren Dateien**, gespeichert auf dem Gerät. Import und Export als ZIP, Dateien
  aus der Dateien-App importieren. Dateien, die dein Programm schreibt, erscheinen im Dateibaum.
- **Smarter Editor**: Syntaxfarben, Vervollständigung mit Dokumentation (jedi), Signaturhilfe, Fehlerprüfung
  beim Tippen (pyflakes), fertige Bausteine (if, for, while, def, class, try, with, tkinter, PyQt, Dateien,
  Daten …), Tastenleiste über der iOS-Tastatur, Suchen & Ersetzen, Gliederung, Gehe zu Definition,
  Umbenennen, Formatieren mit black, Suche in allen Dateien.
- **Konsole** mit `input()`, interaktiver Python-Eingabe (auch `await`), Variablen-Ansicht und klickbaren
  Fehlermeldungen, die zur Zeile springen. Ein Stopp-Knopf beendet auch Endlosschleifen.
- **Pakete**: `pip`-Installation von PyPI per Knopfdruck. numpy, pandas, matplotlib, scipy, sympy,
  scikit-learn, pillow und viele mehr werden beim `import` automatisch geladen. `requirements.txt` wird unterstützt.
- **GUI**: tkinter (inkl. ttk, messagebox, filedialog, simpledialog, Canvas) und PyQt5/PyQt6/PySide6 laufen
  in einem eingebauten Nachbau. Normaler Desktop-Code öffnet seine Fenster also direkt in der App.
  matplotlib-Grafiken und Animationen erscheinen in der Konsole.
- **Versionskontrolle**: Git direkt auf dem Gerät (Commit, Verlauf, Unterschiede, Dateien zurücksetzen,
  Zweige, Zusammenführen) und Abgleich mit GitHub (Klonen, Hochladen, Holen).
- Hell- und Dunkelmodus, angepasst an iPhone-Notch und iPad (dreispaltig im Querformat).

---

## 1. Installation (einmalig, ca. 10 Minuten)

Die App muss einmal im Internet liegen, damit Safari sie installieren kann. Am einfachsten geht das kostenlos
mit **GitHub Pages**. Die Schritte A und B gehen am bequemsten am Mac (Browser genügt), Schritt C am iPhone.

### A. Repository anlegen und Dateien hochladen

1. Auf <https://github.com> anmelden (oder kostenlos registrieren).
2. Oben rechts **+ → New repository**. Name z. B. `kobra`, Sichtbarkeit **Public**
   (GitHub Pages ist bei kostenlosen Konten nur für öffentliche Repositorys verfügbar). **Create repository**.
3. Auf der neuen, leeren Seite auf **uploading an existing file** klicken.
4. Die ZIP-Datei entpacken und den **Inhalt** des Ordners `kobra` (also `index.html`, `sw.js`, `js`, `vendor` …,
   nicht den Ordner selbst) in das Browserfenster ziehen. Warten, bis alle Dateien gelistet sind, dann
   **Commit changes**.

### B. GitHub Pages einschalten

1. Im Repository **Settings → Pages**.
2. Bei *Build and deployment* → *Source*: **Deploy from a branch**, Branch **main**, Ordner **/ (root)**,
   **Save**.
3. Nach 1–2 Minuten erscheint oben die Adresse, z. B. `https://deinname.github.io/kobra/`.

### C. Auf dem iPhone installieren

1. Die Adresse in **Safari** öffnen und warten, bis der Punkt oben links **grün** ist (Python bereit).
   Der erste Start lädt ca. 15 MB und braucht deshalb Internet.
2. **Teilen-Symbol → Zum Home-Bildschirm → Hinzufügen**.
3. Kobra ab jetzt **nur noch über das Symbol** auf dem Home-Bildschirm öffnen. Die installierte App hat unter
   iOS einen eigenen Speicher, getrennt vom Safari-Tab.

> **Alternativen zu GitHub Pages**: Jeder Anbieter für statische Webseiten mit HTTPS funktioniert, z. B.
> Cloudflare Pages („Upload assets“) oder Netlify Drop. Den Ordner einfach hochladen.

---

## 2. GitHub-Abgleich einrichten (optional)

Git auf dem Gerät (Commits, Verlauf, Zweige) funktioniert sofort. Für das Klonen, Hochladen und Holen von
GitHub braucht Kobra zwei Dinge: einen kleinen **Git-Proxy**, denn Browser dürfen aus Sicherheitsgründen nicht
direkt mit GitHub-Git sprechen, und ein **GitHub-Token**.

### Git-Proxy als Cloudflare Worker (kostenlos, 3 Minuten)

1. Auf <https://dash.cloudflare.com> kostenlos registrieren und anmelden.
2. **Workers & Pages → Create → Create Worker** (Vorlage „Hello World“), Name z. B. `kobra-git`, **Deploy**.
3. **Edit code**: den gesamten Inhalt durch die Datei `git-proxy/worker.js` aus diesem Ordner ersetzen,
   **Deploy**.
4. Die Adresse notieren, z. B. `https://kobra-git.deinname.workers.dev`. Beim Aufruf im Browser sollte
   „Kobra Git-Proxy läuft.“ erscheinen.
5. Empfohlen: unter **Settings → Variables and Secrets** eine Variable `ALLOWED_ORIGINS` mit dem Wert
   `https://deinname.github.io` anlegen. Dann kann nur deine Kobra-Seite den Proxy benutzen.

Der Proxy leitet ausschließlich Git-Anfragen an GitHub, GitLab, Codeberg und Bitbucket weiter und speichert nichts.

### GitHub-Token erstellen

1. GitHub → Profilbild → **Settings → Developer settings → Personal access tokens → Fine-grained tokens →
   Generate new token**.
2. Ablaufdatum wählen. Unter *Repository access* „Only select repositories“ und die gewünschten Repositorys
   auswählen (oder „All repositories“).
3. Unter *Permissions → Repository permissions* **Contents: Read and write** setzen.
4. **Generate token** und den Token kopieren (er wird nur einmal angezeigt).

### In Kobra eintragen

**••• → Einstellungen → Git**: Name, E-Mail, Token und Proxy-Adresse eintragen und speichern.
Der Token bleibt nur auf deinem Gerät.

### Benutzen

- **Projekt hochladen**: Bereich *Git* → *Versionskontrolle einrichten* → Änderungen committen →
  *Mit GitHub verbinden* (Adresse wie `https://github.com/deinname/projekt.git`, das Repository vorher auf
  GitHub leer anlegen) → *Hochladen*.
- **Von GitHub holen**: *Holen* übernimmt neue Commits. Lokale Änderungen vorher committen.
- **Bestehendes Repository öffnen**: Ordnersymbol oben links → *Von GitHub klonen*.

---

## 3. Bedienung in Kürze

| Aktion | So geht's |
| --- | --- |
| Programm starten | **Start** oben rechts startet die geöffnete `.py`-Datei. **Lange drücken** öffnet das Menü mit Startdatei, Argumenten und Python-Neustart. |
| Programm stoppen | Derselbe Knopf zeigt während des Laufs **Stopp**. Bei Fenster-Programmen gibt es zusätzlich ■ in der Fensterleiste. |
| Bausteine | In der Tastenleiste über der Tastatur auf das gelbe **Bausteine**-Symbol (vier Kästchen) tippen oder im Editor `for`, `if`, `def` … tippen und einen Vorschlag wählen. Mit der **Tab**-Taste links in der Leiste springst du zum nächsten Platzhalter. |
| Vervollständigung | Erscheint beim Tippen automatisch, z. B. nach `.`. Von Hand über das ✦-Symbol in der Tastenleiste oder **Strg+Leertaste** (Hardware-Tastatur). Das Buch-Symbol zeigt die Dokumentation zum Wort unter dem Cursor. |
| Datei-Aktionen | Im Bereich *Dateien* auf **•••** neben einer Datei tippen: umbenennen, verschieben, als Startdatei festlegen, teilen. |
| Projekte | Ordnersymbol oben links: wechseln, *Neues Projekt* (mit Vorlagen), *ZIP importieren*, *Von GitHub klonen*. |
| Pakete | Bereich *Pakete*: Namen eingeben oder einen beliebten Eintrag antippen. |
| Fenster (tkinter/PyQt) | Öffnen sich als Ebene über der App. Die Leiste darüber hat Knöpfe für Pfeiltasten, Tastatur (Tasten an das Programm senden), Zoom, Ausblenden (die Pille „Fenster“ holt sie zurück), Stopp und Schließen. |

---

## 4. Was geht – und was nicht

Kobra läuft vollständig im Browser. Daraus ergeben sich ein paar Grenzen:

- **Pakete**: Reine Python-Pakete von PyPI funktionieren. Pakete mit C-/Rust-Code nur, wenn Pyodide sie
  vorkompiliert anbietet (numpy, pandas, scipy, matplotlib, pillow, scikit-learn, sympy, lxml, cryptography …).
  Nicht möglich sind z. B. psycopg2, pygame, tensorflow oder torch. Kobra sagt in diesem Fall verständlich, warum.
- **tkinter/PyQt sind Nachbauten**, keine echten Bibliotheken. Die üblichen Widgets, Layouts (pack/grid/place,
  QVBox/QHBox/QGrid/QForm), Dialoge, Menüs, Canvas/QPainter, Timer und Ereignisse funktionieren. Exotische Teile
  fehlen, etwa Tk-Erweiterungen, OpenGL, QWebEngine, Qt Designer `.ui`-Dateien und Qt-Model/View-Klassen mit
  eigenen Modellen. Das Aussehen ist an das Original angelehnt, aber nicht pixelgenau.
- **Keine Threads und keine Unterprozesse**: `threading.Thread` lässt sich nicht starten,
  `subprocess`/`os.system` gehen nicht. `QThread` läuft im Nachbau synchron. Für Nebenläufigkeit `asyncio` verwenden.
- **Netzwerk**: Webzugriffe (z. B. `pyodide.http.pyfetch`) gehen nur zu Servern, die Zugriffe aus dem Browser
  erlauben (CORS). Sockets und eigene Server sind nicht möglich.
- **Dateien** liegen im App-Speicher des Geräts, nicht in der Dateien-App. Zum Austausch dient
  *Importieren / Teilen / ZIP*.

---

## 5. Datensicherung

Deine Projekte liegen im Speicher der installierten Web-App auf dem iPhone. iOS löscht diesen Speicher, wenn du
die App vom Home-Bildschirm entfernst oder die Website-Daten in den Safari-Einstellungen löschst. Deshalb:

- wichtige Projekte regelmäßig zu **GitHub hochladen** oder
- über **Projekte → Als ZIP exportieren** in der Dateien-App/iCloud sichern.

Wechselst du die Adresse (z. B. anderer Hoster), sind die Projekte dort leer. Mit ZIP-Export und -Import kannst
du sie umziehen.

---

## 6. Aktualisieren

Wenn du Dateien von Kobra änderst, lädst du sie erneut ins Repository hoch. In `sw.js` dabei die Zeile
`const VERSION = 'kobra-v1.0.0';` hochzählen (z. B. `v1.0.1`). Beim nächsten Öffnen zeigt Kobra
„Eine neue Version von Kobra ist bereit.“, und ein Tipp auf **Neu laden** übernimmt sie.

---

## 7. Probleme lösen

- **Punkt bleibt gelb/rot, Python startet nicht**: Beim allerersten Start (und nach einem Update von Python)
  wird Internet gebraucht. Mit Internet die App schließen und neu öffnen oder **Start** lange drücken →
  *Python neu starten*.
- **Programm hängt**: **Stopp** drücken. Kobra startet Python dann neu; deine Dateien bleiben erhalten.
- **Git: „Keine Verbindung zum Git-Proxy“**: Proxy-Adresse in den Einstellungen prüfen (ohne `/` am Ende)
  und ggf. `ALLOWED_ORIGINS` im Worker kontrollieren (exakt `https://deinname.github.io`, ohne Pfad).
- **Git: „Hochladen abgelehnt“**: Der Token braucht *Contents: Read and write* für genau dieses Repository.
- **`input()` antwortet nicht im Safari-Tab ohne Installation**: Kobra braucht dafür den Service Worker. Einmal
  neu laden; in der installierten App funktioniert es immer.

---

## 8. Für Entwickler

| Datei/Ordner | Inhalt |
| --- | --- |
| `index.html`, `styles.css` | App-Oberfläche |
| `js/` | Editor (CodeMirror 6), Dateien, Konsole, GUI-Darstellung, Pakete, Git |
| `worker.js` | Python-Worker (Pyodide, input, pip, IntelliSense) |
| `sw.js` | Service Worker: Offline-Cache und synchroner Kanal für `input()` und blockierende GUI-Schleifen |
| `vendor/vendor.js` | Gebündelte Bibliotheken: CodeMirror, isomorphic-git, LightningFS, JSZip, diff |
| `py/` | Python-Quellen: tkinter- und PyQt-Nachbau, Laufzeit, matplotlib-Backend |
| `py-bundle.json` | Die Python-Quellen gebündelt; wird von der App geladen |
| `tools/build_bundle.py` | Erzeugt `py-bundle.json` neu, nach jeder Änderung in `py/` ausführen |
| `git-proxy/worker.js` | Cloudflare-Worker für den GitHub-Abgleich |

Die Python-Version kommt von `https://cdn.jsdelivr.net/pyodide/v314.0.7/full/`. Eine andere Pyodide-Adresse
lässt sich über den Browser-Speicher `localStorage['kobra.indexURL']` setzen.
