# 🤖 Hitasha • Your 3D Living Desktop Screen Mate & Indian Bestfriend Assistant

> **A real living 3D Indian bestfriend on your screen! Hitasha physically walks across your monitor, hovers with gentle physics, watches your screen with you to comment on your work or gaming, gives proactive posture and hydration reminders, executes desktop tasks, and keeps you company like a true companion in real life!**

---

## 🇮🇳 Authentic Indian Girl Presence & Styling

Hitasha embodies the warmth, wit, and charm of a modern Indian best friend:
- **Traditional Ornaments & Styling**:
  - **Red Velvet Bindi**: Classic circular forehead bindi with a tiny golden center bead.
  - **Golden Jhumkas**: Dangling bell earrings on her ear flaps with mini droplet beads that swing as she moves.
  - **Winged Kajal Eyeliner**: Expressive kohl eyeliner styling around hazel cartoon eyes.
  - **Golden Bangles (Kangan)**: Elegant golden bangles on both wrists.
  - **Warm Festive Clay Palette**: Warm terracotta coral hood, soft warm skin undertones, and rose blush.
- **Natural Indian Female Voice**:
  - **Online**: Powered by Microsoft Edge Neural Speech (`en-IN-NeerjaNeural` / `en-IN-KavyaNeural`) for studio-quality Indian English speech played via Pygame audio mixer.
  - **Offline**: Instant automatic fallback to local Windows SAPI5 voices when disconnected from the internet.
- **Desi Best Friend Banter**:
  - Infused with natural warmth, affection, and slang (*"Arre yaar!"*, *"Suno na"*, *"Haan bilkul"*, *"Chai break le lo"*, *"Pakka!"*, *"Batao na"*).

---

## 🛑 Manual Start & Stop (Full Control Anywhere)

Hitasha gives you complete manual control over when she runs, sleeps, or stops:

### 1. One-Click Desktop Launchers
On your Windows Desktop:
- **`Start Hitasha.bat`**: Double-click to instantly launch Hitasha floating on your screen.
- **`Stop Hitasha.bat`**: Double-click to cleanly terminate Hitasha and free all background processes.

### 2. In-App Stop & Sleep Buttons
- **🛑 Stop Button**: Located on both the Command Deck top bar and the Screen Mate floating bar. Shuts down Hitasha cleanly with a warm goodbye.
- **💤 Sleep / ⚡ Wake Button**: Puts Hitasha into power-saving sleep mode. She curls up, closes her eyes in a peaceful sleep animation, pauses auto-roaming, and frees CPU/GPU cycles until you wake her!

### 3. Windows System Tray
Right-click Hitasha's icon in the Windows Taskbar Notification Area (next to the clock):
- `👁️ Toggle Command Deck`
- `🚶 Toggle Screen Mate`
- `💤 Sleep / ⚡ Wake`
- `🔥 Roast Me`
- `📸 Screenshot`
- `🛑 Stop Hitasha`

---

## ⚡ Offline & Online Hybrid Architecture

Hitasha runs seamlessly whether you are connected to the internet or completely offline:

| Mode | AI Intelligence | Voice Engine | Screen Vision & Features |
|---|---|---|---|
| **Local GPU (RTX 5050)** | **Ollama / LM Studio** with `llama3.2:3b`, `qwen2.5:3b` | Edge-TTS (if connected) or pyttsx3 offline | Full screen observation, local memory, system diagnostics |
| **Online Mode** | **Google Gemini 2.5 Flash** (Interactions & Vision) | **Edge-TTS `en-IN-NeerjaNeural`** | Multimodal screen reasoning, live web search, unlimited banter |
| **Full Offline** | **Rule-Based Desi Dialogue Tree** (Roasts, Jokes, Riddles) | **Local Windows SAPI5** (`pyttsx3`) | Offline process watcher, timers, alarms, notes, games |

### Local GPU Parameters (Tuned for RTX 5050 8GB VRAM):
- `num_gpu: 99` (100% full VRAM offload, 0 CPU bottleneck)
- `temperature: 0.7` (Creative, witty, conversational)
- `top_p: 0.9` & `top_k: 40` (Natural vocabulary)
- `max_tokens / num_predict: 150` (Punchy spoken voice replies)
- `num_ctx: 4096` (Complete chat context window)

---

## ✨ Features Breakdown

### 1. 🧍 Physically Walks & Hovers Directly On Your Desktop
- **Transparent Borderless Screen Mate**: Hitasha stands and floats directly on top of your windows, code, or games with a transparent background (`WindowStaysOnTopHint`).
- **Walking Across Screen**: Hitasha turns her body in the direction of movement, swings her arms and boots, and walks smoothly across your desktop!
- **Anti-Gravity Hovering**: Levitation mode with continuous sine-wave physics (`✨ Hover`).
- **Interactive Drag & Drop**: Click and drag Hitasha anywhere on your screen.
- **3D Humanoid Animations**:
  - `🧘 Idle`, `🚶 Walk`, `👋 Wave`, `🕺 Dance`, `💅 Sassy`, `💬 Talk`, `🦘 Jump`, `✨ Hover`, `🤔 Think`, `🤣 Laugh`, `💤 Sleep`.

### 2. 👁️ Watches Screen with You (AI Co-Watching)
- **Active Window Contextual Commentary**:
  - **Coding (VS Code, PyCharm, IDEs)**: Comments on your syntax and coding progress.
  - **Videos (YouTube, Netflix)**: Asks for digital popcorn and warns about rabbit holes.
  - **Social (Reddit, Twitter)**: Teases you about endless scrolling.
  - **Chatting (Discord, Slack, WhatsApp)**: Asks about the tea being spilled.
  - **Gaming (Steam, Minecraft)**: Cheers for your victory.

### 3. 🦐 Proactive Bestfriend Reminders
- **Posture Checks**: *"Unshrimp your spine right now before your backbone files a grievance! 🦐"*
- **Hydration Breaks**: *"Water break! Your body is running on pure caffeine and dry air! Drink up! 💧"*
- **20-20-20 Eye Breaks**: *"Screen break time! Blink 10 times and give your eyes a quick rest! 👀"*
- **Custom Timers**: *"Remind me in 15 minutes to take a break"* -> Hitasha chimes, walks over, and reminds you!

### 4. ⚡ Desktop Tasks & Tools
- **Media Keys**: *"Volume up"*, *"Volume down"*, *"Mute volume"*, *"Pause music"*, *"Play music"*.
- **Folders & Apps**: *"Open downloads"*, *"Open desktop"*, *"Open project"*, *"Open YouTube"*, *"Open Spotify"*.
- **Screenshots**: *"Take a screenshot"* -> Saves to `./screenshots/` and displays immediately.
- **PC Stats**: *"How's my PC?"* -> Instant CPU, RAM, and Battery diagnostics.
- **Jarvis Memory**: Remembers your name and facts across sessions in `memory.json`.

---

## 🧹 Ponytail Codebase Pruning & Tech Stack

Following the **Ponytail** pragmatic software engineering principles:
- **Dead Code Elimination**: Pruned 476 lines of obsolete 2D QPainter canvas code (`avatar.py`), retaining only clean `Mood` constants.
- **Dependency Optimization**: Removed unused packages (`opencv-python`). Standardized on native Python standard library + lightweight PyQt6, Edge-TTS, and Pygame.
- **Unified Clean Control**: Replaced scattered test and helper scripts with dedicated `Start_Hitasha.bat`, `Stop_Hitasha.bat`, and `stop.py`.

---

## 🚀 Quick Start Guide

### Launching Hitasha:
- **Option 1**: Double-click **`Start Hitasha.bat`** on your Desktop.
- **Option 2**: Run `run.bat` in the project root.
- **Option 3**: In PowerShell:
  ```powershell
  .\.venv\Scripts\python.exe main.py
  ```

### Stopping Hitasha:
- **Option 1**: Double-click **`Stop Hitasha.bat`** on your Desktop.
- **Option 2**: Click the **🛑** button on the Command Deck or Screen Mate bar.
- **Option 3**: Right-click the system tray icon and select **🛑 Stop Hitasha**.
