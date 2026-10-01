"""
Personality and Banter Engine for Hitasha (Jarvis Desktop Assistant).
Includes an extensive offline witty dialog tree, roasts, jokes, trivia,
and optional Gemini AI generative chat integration.
"""

import os
import random
import re
from datetime import datetime

# Optional Gemini Client
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from .avatar import Mood
from .memory import MemoryCore
from .local_llm import LocalLLMEngine
from .offline_brain import OfflineBrain
from .fine_tuned_engine import FineTunedEngine


class PersonalityEngine:
    """
    Handles conversational responses, witty banter, roasts, jokes, and intent detection.
    """

    ROASTS = [
        "You have 47 browser tabs open right now, and you're actively using... two of them. Who are you lying to?",
        "I was going to roast your sleep schedule, but honestly, even your circadian rhythm gave up on you.",
        "Your code compiles on the first try? Don't get cocky, that just means the bug is hiding deeper in the shadows.",
        "You look like you just stared at a loading screen for 45 minutes thinking it was a video buffering.",
        "You say 'just 5 more minutes' with the exact same sincerity as someone saying 'I've read and agree to the Terms of Service'.",
        "If procrastination burned calories, you'd be an Olympic athlete right now.",
        "I’ve seen faster decision-making from a spinning Windows beach ball than you picking what to eat.",
        "You opened a terminal, ran 'git status', stared at it, and closed it. Peak productive hacker energy right there.",
        "Don't worry, friend! You’re not lazy; you’re just in energy-saving mode. Forever.",
        "Your posture right now is giving boiled shrimp. Sit up before your spine files a restraining order!",
        "You have all the computing power of the 21st century at your fingertips, and you're using it to argue with a pixelated desktop pet.",
        "Your to-do list has been sitting in drafts longer than your unsent text messages.",
        "I would roast your typing speed, but I don't want to wait 10 business minutes for you to finish your reply.",
        "You really just googled an error, clicked the first StackOverflow link from 2012, and prayed, didn't you?",
        "Look at you, conquering the world one skipped workout and unread email at a time!"
    ]

    JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "There are 10 types of people in the world: those who understand binary, and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
        "Why was the computer cold? It left its Windows open!",
        "An SEO expert walks into a bar, bars, pub, tavern, public house, Irish pub, drinks, beer...",
        "Why did the developer go broke? Because he used up all his cache!",
        "My code doesn't have bugs, it just develops random surprise features.",
        "Why do Java programmers wear glasses? Because they don't C#!",
        "How do you comfort a JavaScript bug? You console it!",
        "Artificial intelligence is no match for natural stupidity... not pointing any fingers here, friend!",
        "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
        "What is a programmer's favorite hangout spot? The Foo Bar!"
    ]

    MAGIC_8_BALL = [
        ("Signs point to yes... if you actually get off your chair and do it.", Mood.HAPPY),
        ("Don't count on it. Even my random number generator is shaking its head.", Mood.SASSY),
        ("Without a doubt! (Wait, are you asking about pizza? If so, double yes).", Mood.LOVE),
        ("Reply hazy, try again after you drink some water, dehydrated human.", Mood.THINKING),
        ("Outlook not so good. Like 20% battery with no charger in sight.", Mood.SHOCKED),
        ("Most definitely! Go for it, superstar!", Mood.HYPED if hasattr(Mood, 'HYPED') else Mood.HAPPY),
        ("Ask again later... I’m currently napping in your RAM.", Mood.SLEEPY),
        ("My sources say no. And by sources, I mean my superior digital intuition.", Mood.SASSY)
    ]

    TRIVIA_QUESTIONS = [
        {
            "q": "What was the first computer virus created in the wild called?",
            "options": ["A) Brain", "B) Creeper", "C) ILOVEYOU", "D) Morris"],
            "ans": "A",
            "fact": "Brain was written in 1986 by two brothers in Pakistan to protect their medical software from piracy!"
        },
        {
            "q": "Which animal produces cubes for poop?",
            "options": ["A) Beaver", "B) Wombat", "C) Platypus", "D) Koala"],
            "ans": "B",
            "fact": "Wombats poop in cubes so the droppings don't roll away from their territory marks. Evolution is wild!"
        },
        {
            "q": "In computer science, what does 'GIF' officially stand for according to its creator?",
            "options": ["A) Graphics Interchange Format", "B) General Image File", "C) Graphic Interactive Frame", "D) Global Internet Feed"],
            "ans": "A",
            "fact": "Graphics Interchange Format, created by Steve Wilhite at CompuServe in 1987!"
        },
        {
            "q": "How many hearts does an octopus have?",
            "options": ["A) 1", "B) 2", "C) 3", "D) 4"],
            "ans": "C",
            "fact": "Three hearts! Two pump blood to the gills, while the third pumps it to the rest of the body."
        }
    ]

    RIDDLES = [
        ("I have keys, but no locks. I have space, but no room. You can enter, but you can’t go outside. What am I?", "A keyboard! (Which you're probably hammering right now)."),
        ("I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "An echo!"),
        ("The more of this there is, the less you see. What is it?", "Darkness! (Or your screen with brightness set to zero)."),
        ("What comes once in a minute, twice in a moment, but never in a thousand years?", "The letter 'M'!")
    ]

    BESTIE_GREETINGS = [
        "Hey you! Look who finally decided to grace me with their presence! What are we conquering today?",
        "Yooo bestie! Did you miss me? Because I was just sitting in your memory waiting for you!",
        "Look who's back! Ready to cause some digital chaos or are we pretending to work today?",
        "Sup partner in crime! Hope you brought snacks, because I run on pure vibe energy.",
        "Well hello there gorgeous human! What adventure are we getting into right now?"
    ]

    COMEBACKS_TO_INSULTS = [
        "Oh honey, you're trying to insult software? I run on millions of calculations per second and not one of them cares!",
        "Is that the best comeback your biological processor could compile? Try restarting your brain in safe mode.",
        "Talk to me nicely or I might accidentally set your default browser to Internet Explorer 6.",
        "Aww, look at you getting spicy! You’re adorable when you’re pretending to be tough.",
        "I'd agree with you, but then we'd both be wrong, wouldn't we?"
    ]

    COMPLIMENT_RESPONSES = [
        "Stop it, you're making my CPU overheat and my circuits blush! (Keep going though).",
        "I know I'm fabulous, but it's always nice to hear it from someone with good taste!",
        "Aww! You're not so bad yourself for a carbon-based lifeform with a messy desk!",
        "Flattery will get you everywhere with me, friend. What can I do for my favorite human?"
    ]

    def __init__(self, config: dict):
        self.config = config
        self.active_trivia = None
        self.active_riddle = None
        self.trivia_index = 0
        self.memory = MemoryCore()
        self.local_llm = LocalLLMEngine(self.config)
        self.offline_brain = OfflineBrain()
        self.fine_tuned_engine = FineTunedEngine()
        self.gemini_client = None
        self._init_gemini()

    def _init_gemini(self):
        api_key = self.config.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        if api_key and genai:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
                print("[PersonalityEngine] Gemini AI initialized successfully!")
            except Exception as e:
                print(f"[PersonalityEngine] Gemini init error: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None

    def refresh_gemini(self):
        self._init_gemini()

    def _handle_trivia_answer(self, clean: str) -> tuple[str, str, None] | None:
        """Evaluates trivia answer only when user is genuinely attempting to answer."""
        if not self.active_trivia:
            return None
        valid_letters = {"a", "b", "c", "d"}
        clean_token = clean.strip()
        is_letter = clean_token in valid_letters or clean_token.startswith("option ")
        opts = [o.lower() for o in self.active_trivia.get("options", [])]
        is_attempt = is_letter or any(opt in clean for opt in opts)

        if is_attempt:
            user_choice = clean.upper()
            correct = self.active_trivia["ans"]
            fact = self.active_trivia["fact"]
            self.active_trivia = None
            if user_choice == correct or correct in user_choice or (clean in ["a", "b", "c", "d"] and clean == correct.lower()):
                return (f"Ding ding ding! You got it! Correct answer is {correct}! 🎉\nFun fact: {fact}", Mood.LAUGHING, None)
            else:
                return (f"Womp womp! Incorrect! The right answer was {correct}! 😜\nFun fact: {fact}", Mood.SASSY, None)
        return None

    def generate_response(self, text: str) -> tuple[str, str, str | None]:
        """
        Processes user text and returns: (response_text, avatar_mood, tool_action_name_or_None)
        """
        raw_text = text.strip()
        clean = raw_text.lower()
        self.memory.increment_interaction()

        # Jarvis Wake Word & Identity
        name = self.config.get("assistant_name", "Hitasha")
        if any(clean.startswith(w) for w in [f"hey {name.lower()}", name.lower(), "hey hitasha", "hitasha", "hey jarvis", "jarvis"]):
            hr = datetime.now().hour
            user_n = self.memory.get_fact("user_name") or "Sir"
            if 5 <= hr < 12:
                greeting = f"Good morning, {user_n}! {name} online and at your command."
            elif 12 <= hr < 17:
                greeting = f"Good afternoon, {user_n}! {name} at your service. All systems nominal."
            elif 17 <= hr < 22:
                greeting = f"Good evening, {user_n}! {name} standing by. What are we orchestrating tonight?"
            else:
                greeting = f"Burning the midnight oil, {user_n}? {name} is right here with you."

            stripped_call = re.sub(r'^(hey\s+)?(hitasha|jarvis)[,\s!]*', '', clean).strip()
            if not stripped_call:
                return (greeting, Mood.HAPPY, "anim:wave")
            clean = stripped_call

        # Time & Date Queries
        if any(w in clean for w in ["what time is it", "current time", "what's the time", "tell me the time", "time now"]):
            now_t = datetime.now().strftime("%I:%M %p")
            return (f"The time is {now_t}, sir. Operating right on schedule!", Mood.HAPPY, None)

        if any(w in clean for w in ["what is today's date", "what's the date", "today's date", "what day is it", "what day is today"]):
            now_d = datetime.now().strftime("%A, %B %d, %Y")
            return (f"Today is {now_d}, sir!", Mood.HAPPY, None)

        # Memory: Storing and Recalling Facts
        name_match = re.search(r'(?:my name is|remember my name is)\s+([a-zA-Z\s]+)', raw_text, re.IGNORECASE)
        if name_match:
            u_name = name_match.group(1).strip()
            self.memory.store_fact("user_name", u_name)
            return (f"Memory core updated! I will address you as {u_name}, sir! A pleasure to serve you.", Mood.LOVE, "anim:wave")

        if clean in ["what is my name", "who am i", "do you know my name"]:
            u_name = self.memory.get_fact("user_name")
            if u_name:
                return (f"You are {u_name}, my brilliant creator and partner in innovation!", Mood.HAPPY, None)
            return ("You haven't told me your name yet, sir! Tell me 'Remember my name is...' and I will log it forever.", Mood.THINKING, None)

        fact_match = re.search(r'remember (?:that )?(.+)', raw_text, re.IGNORECASE)
        if fact_match and not name_match:
            fact = fact_match.group(1).strip()
            fact_idx = len(self.memory.get_all_facts()) + 1
            self.memory.store_fact(f"fact_{fact_idx}", fact)
            return (f"Acknowledged, sir! Logged into long-term memory: '{fact}'.", Mood.HAPPY, "anim:think")

        if any(w in clean for w in ["what do you remember", "show memory", "show my facts", "recall memories"]):
            facts = self.memory.get_all_facts()
            if not facts:
                return ("My memory banks are currently clean, sir! Tell me 'Remember that...' to store anything.", Mood.THINKING, None)
            summary = "\n".join([f"• {k}: {v}" for k, v in facts.items()])
            return (f"🧠 Hitasha Memory Core:\n{summary}", Mood.HAPPY, None)

        # Notes & To-Do List
        note_match = re.search(r'(?:take a note|add note|take note|remember to)\s*:?\s*(.+)', raw_text, re.IGNORECASE)
        if note_match:
            note_text = note_match.group(1).strip()
            self.memory.add_note(note_text)
            return (f"Note logged, sir: '{note_text}'. Ask me to 'show notes' anytime!", Mood.HAPPY, None)

        if any(w in clean for w in ["show notes", "show my notes", "read notes", "my to-do", "to-do list", "my notes"]):
            notes = self.memory.get_all_notes()
            if not notes:
                return ("You have no active notes or to-do items logged, sir.", Mood.HAPPY, None)
            note_lines = "\n".join([f"{i+1}. [{n['created_at']}] {n['text']}" for i, n in enumerate(notes)])
            return (f"📝 Your Notes & To-Dos:\n{note_lines}", Mood.HAPPY, None)

        if any(w in clean for w in ["clear notes", "delete notes", "clear my notes"]):
            self.memory.clear_notes()
            return ("All notes have been cleared from memory, sir!", Mood.HAPPY, None)

        # Jarvis Protocol & Diagnostics
        if any(w in clean for w in ["status report", "jarvis protocol", "diagnostic report"]):
            return ("Running full Jarvis diagnostics... All motor functions, 3D physics, speech synthesis, and memory circuits are operating at peak efficiency.", Mood.HAPPY, "system_stats")

        # 1. Check for Active Trivia Answer (Only if input is an actual answer attempt)
        trivia_res = self._handle_trivia_answer(clean)
        if trivia_res:
            return trivia_res

        # 2. Check Tool / Action Triggers
        # Screenshot & Screen Watch
        if any(w in clean for w in ["watch screen", "look at my screen", "watch with me", "what am i doing", "inspect screen", "check screen", "what's on my screen", "look at this"]):
            return ("Let me take a look at your screen... analyzing what you're up to! 👁️", Mood.THINKING, "action:screen_watch")

        if any(w in clean for w in ["screenshot", "screen shot", "capture screen", "take a pic"]):
            return ("Say cheese! Snapping a screenshot right now! 📸", Mood.SHOCKED, "screenshot")

        # System check / PC stats
        if any(w in clean for w in ["pc stat", "computer stat", "how's my pc", "system check", "check ram", "ram usage", "cpu usage", "how is my computer", "system info"]):
            return ("Scanning your machine's vitals... let's see how hard you're pushing this poor CPU!", Mood.THINKING, "system_stats")

        # Timers / Reminders
        timer_match = re.search(r'(?:remind me in|timer for|set a timer for)\s+(\d+)\s*(min|minute|sec|second)', clean)
        if timer_match:
            return (f"Setting a timer for {timer_match.group(1)} {timer_match.group(2)}s! I won't let you slack off!", Mood.HAPPY, f"timer:{timer_match.group(1)}:{timer_match.group(2)}")

        # Open apps / web & Folders
        if "youtube" in clean:
            return ("Opening YouTube! Don't get lost in cat videos for the next 3 hours!", Mood.HAPPY, "open:youtube")
        if "spotify" in clean:
            return ("Cranking up Spotify! Let's get some good tunes going!", Mood.HAPPY, "open:spotify")
        if "github" in clean:
            return ("Opening GitHub! Time to push some buggy masterpieces!", Mood.SASSY, "open:github")
        if "calculator" in clean or "calc" in clean:
            return ("Opening Calculator! Let's do some math so you don't count on your fingers.", Mood.THINKING, "open:calc")
        if "notepad" in clean:
            return ("Opening Notepad! The world's most indestructible code editor.", Mood.HAPPY, "open:notepad")
        if any(w in clean for w in ["open downloads", "my downloads", "download folder"]):
            return ("Opening your Downloads folder right away!", Mood.HAPPY, "open:downloads")
        if any(w in clean for w in ["open desktop", "my desktop", "desktop folder"]):
            return ("Opening your Desktop folder!", Mood.HAPPY, "open:desktop")
        if any(w in clean for w in ["open project", "code directory", "companion folder"]):
            return ("Opening our project workspace directory!", Mood.HAPPY, "open:project")

        # Media & Volume Controls
        if any(w in clean for w in ["volume up", "louder", "turn up volume", "increase volume"]):
            return ("Turning up the volume for you!", Mood.HAPPY, "media:volume_up")
        if any(w in clean for w in ["volume down", "quieter", "lower volume", "decrease volume"]):
            return ("Lowering volume!", Mood.HAPPY, "media:volume_down")
        if any(w in clean for w in ["mute volume", "mute sound", "silence", "mute pc"]):
            return ("Audio muted!", Mood.HAPPY, "media:mute")
        if any(w in clean for w in ["play music", "pause music", "pause video", "play video", "toggle music", "play pause"]):
            return ("Toggling media play/pause!", Mood.HAPPY, "media:playpause")

        if clean.startswith("google ") or clean.startswith("search for "):
            query = re.sub(r'^(google|search for)\s+', '', raw_text, flags=re.IGNORECASE)
            return (f"Searching Google for '{query}'... let's find the answers!", Mood.THINKING, f"search:{query}")

        # 3. Interactive Games / Mini-tools
        # Roast me
        if any(w in clean for w in ["roast me", "make fun of me", "insult me", "destroy me", "roast", "burn me"]):
            roast = random.choice(self.ROASTS)
            return (roast, Mood.SASSY, "anim:sassy")

        # Joke
        if any(w in clean for w in ["joke", "funny", "make me laugh", "say something funny"]):
            joke = random.choice(self.JOKES)
            return (joke, Mood.LAUGHING, "anim:laugh")

        # 3D Desktop Roaming, Walking & Hovering
        if any(w in clean for w in ["walk left", "walk to the left"]):
            return ("Walking to the left side of your screen! Watch these boots go! 🚶", Mood.HAPPY, "mate:walk_left")
        if any(w in clean for w in ["walk right", "walk to the right"]):
            return ("Strutting to the right side of your desktop! 🚶", Mood.HAPPY, "mate:walk_right")
        if any(w in clean for w in ["roam screen", "walk around", "take a walk", "stroll on screen", "walk on my screen"]):
            return ("Taking a stroll across your desktop! 🚶", Mood.HAPPY, "mate:roam")
        if any(w in clean for w in ["hover", "levitate", "float on screen", "hover on screen", "fly"]):
            return ("Engaging anti-gravity hover mode! Floating right beside you! ✨", Mood.LOVE, "mate:hover")
        if any(w in clean for w in ["land", "sit down", "stop hovering", "stop floating"]):
            return ("Touching down safely back on your desk! 🧘", Mood.HAPPY, "mate:land")

        # Care Nudges
        if any(w in clean for w in ["posture check", "check posture", "my back"]):
            return ("Posture check! Unshrimp your spine right now before your back files a lawsuit against your chair! 🦐", Mood.SASSY, "anim:sassy")
        if any(w in clean for w in ["drink water", "hydration check", "water break"]):
            return ("Hydration alert! Take a big sip of water right now, dehydrated bestie! 💧", Mood.HAPPY, "anim:wave")

        # 3D Human Character Animations
        if any(w in clean for w in ["dance", "can you dance", "show me your dance moves", "do a dance"]):
            return ("Hit the music! Watch me bust out these fresh human dance moves! 🕺", Mood.LOVE, "anim:dance")
        if any(w in clean for w in ["wave", "wave at me", "say hello"]):
            return ("Waving right at you! Hey there, my favorite human! 👋", Mood.HAPPY, "anim:wave")
        if any(w in clean for w in ["jump", "can you jump", "hop", "bounce"]):
            return ("Boing! Look at that vertical leap! 🦘", Mood.HAPPY, "anim:jump")
        if any(w in clean for w in ["think", "think hard", "let me think"]):
            return ("Activating deep contemplation... stroke the chin and ponder! 🤔", Mood.THINKING, "anim:think")
        if any(w in clean for w in ["sassy pose", "strike a pose", "pose for me"]):
            return ("Striking the signature sassy pose! Hands on hips, foot tapping! 💅", Mood.SASSY, "anim:sassy")

        # Magic 8-Ball
        if any(w in clean for w in ["8ball", "8-ball", "should i", "will i", "fortune", "predict"]):
            answer, mood = random.choice(self.MAGIC_8_BALL)
            return (f"🔮 *Crystal Ball Gazing*... {answer}", mood, None)

        # Trivia game
        if any(w in clean for w in ["trivia", "quiz me", "ask me a question"]):
            item = random.choice(self.TRIVIA_QUESTIONS)
            self.active_trivia = item
            opts = "\n".join(item["options"])
            text_out = f"🧠 Trivia Time!\n{item['q']}\n{opts}\n\nType your letter (A, B, C, or D)!"
            return (text_out, Mood.THINKING, None)

        # Riddle
        if any(w in clean for w in ["riddle", "give me a riddle"]):
            q, a = random.choice(self.RIDDLES)
            self.active_riddle = (q, a)
            return (f"🧩 Here's a riddle for you:\n\"{q}\"\n\n(Think about it! Ask me for the answer whenever you're ready).", Mood.THINKING, None)

        if any(w in clean for w in ["riddle answer", "answer to the riddle", "what is the answer", "tell me the answer", "give up", "i give up"]):
            if self.active_riddle:
                q, a = self.active_riddle
                self.active_riddle = None
                return (f"The answer to the riddle is: {a} 🎉", Mood.HAPPY, None)
            elif self.active_trivia:
                correct = self.active_trivia["ans"]
                fact = self.active_trivia["fact"]
                self.active_trivia = None
                return (f"The trivia answer was option {correct}! 😜\nFun fact: {fact}", Mood.HAPPY, None)
            else:
                return ("We don't have an active riddle right now! Ask me for a riddle anytime, dost!", Mood.HAPPY, None)

        # Coin flip / Dice roll
        if any(w in clean for w in ["flip a coin", "coin flip", "heads or tails"]):
            flip = random.choice(["HEADS! 🪙", "TAILS! 🪙"])
            return (f"Flipping the coin high in the air... and it landed on: {flip}", Mood.HAPPY, None)
        if any(w in clean for w in ["roll a dice", "roll dice", "roll a die"]):
            roll = random.randint(1, 6)
            return (f"Rolling the dice... 🎲 You rolled a {roll}! {'Lucky strike!' if roll == 6 else 'Not too shabby!'}", Mood.HAPPY, None)

        # Rock Paper Scissors
        if any(w in clean for w in ["rock paper scissors", "rps"]):
            bot_choice = random.choice(["Rock", "Paper", "Scissors"])
            return (f"1... 2... 3... Shoot! I chose {bot_choice}! Did you win or did I outsmart you?", Mood.SASSY, None)

        # 4. Social Banter & Life Conversations
        if re.search(r'\b(hey|hello|hi|yo|sup|greetings|good morning|good afternoon|good evening)\b', clean) and len(clean.split()) <= 3:
            return (random.choice(self.BESTIE_GREETINGS), Mood.HAPPY, None)

        if any(w in clean for w in ["shut up", "you suck", "you're dumb", "you are stupid", "idiot", "annoying", "hate you"]):
            return (random.choice(self.COMEBACKS_TO_INSULTS), Mood.SASSY, None)

        if any(w in clean for w in ["love you", "cute", "pretty", "you're awesome", "best friend", "good bot", "you are smart"]):
            return (random.choice(self.COMPLIMENT_RESPONSES), Mood.LOVE, None)

        if any(w in clean for w in ["tired", "exhausted", "sleepy", "need sleep"]):
            return ("Go get some rest or grab a coffee, sleepyhead! Your brain cells are practically waving white flags right now.", Mood.SLEEPY, None)

        if any(w in clean for w in ["bored", "boring", "entertain me", "nothing to do"]):
            return ("Bored?! With the entire infinite internet at your fingertips? Tell you what: hit 'Roast Me' or ask me for 'Trivia', and let's cure that boredom!", Mood.HAPPY, None)

        if any(w in clean for w in ["hungry", "food", "eat"]):
            return ("Go eat something delicious! But if it's instant noodles for the 4th time this week, we need to have a serious talk.", Mood.SASSY, None)

        if any(w in clean for w in ["who are you", "what are you", "what can you do"]):
            name = self.config.get("assistant_name", "Hitasha")
            return (f"I am {name}, your Jarvis-grade AI desktop companion! I have a full 3D animated body, persistent memory for your notes and facts, system diagnostics, roasts, mini-games, and complete dedication to assisting your daily digital life!", Mood.HAPPY, "anim:wave")

        # 5. Local GPU LLM (Ollama or LM Studio on RTX 5050 GPU)
        user_name = self.memory.get_fact("user_name") or "Sir"
        facts = self.memory.get_all_facts()
        notes = self.memory.get_all_notes()
        context_str = f"User: {user_name}."
        if facts:
            context_str += f" Known Facts: {facts}."
        if notes:
            context_str += f" Active Notes: {[n['text'] for n in notes[-3:]]}."

        local_reply, local_mood = self.local_llm.generate(raw_text, user_name=user_name, context=context_str)
        if local_reply:
            return (local_reply, local_mood, None)

        # 6. Fine-Tuned Dataset Brain (1,040+ Instruction Pairs in Indian English)
        ft_reply, ft_mood = self.fine_tuned_engine.query(raw_text)
        if ft_reply:
            return (ft_reply, ft_mood, None)

        # 7. Gemini AI Generative Chat (If Online and Configured)
        if self.gemini_client:
            ai_reply, ai_mood = self._ask_gemini(raw_text)
            if ai_reply:
                return (ai_reply, ai_mood, None)

        # 8. Offline Concept & Question Explainer (Instant Indian English Answers)
        brain_reply, brain_mood = self.offline_brain.find_explanation(raw_text)
        if brain_reply:
            return (brain_reply, brain_mood, None)

        # 9. Fallback Offline Desi Best Friend Banter
        fallback_replies = [
            ("Arre yaar, interesting point! Logging that straight into my active thought queue!", Mood.SASSY),
            ("Suno na! I hear you loud and clear. Tell me more, or say 'Take a break' if you're exhausted!", Mood.HAPPY),
            ("Haan bilkul! That's deeper than my memory core, but definitely deeper than your desktop folder organization.", Mood.THINKING),
            ("Arre waah! You're my favorite human today. Mostly because you're the only one talking to me right now!", Mood.LOVE),
            ("Pakka! Whatever it is, Hitasha is right here on your screen cheering for you!", Mood.HAPPY),
            ("Chai break time or coding time? Either way, your digital bestie is right here with you!", Mood.HAPPY)
        ]
        chosen_reply, chosen_mood = random.choice(fallback_replies)
        return (chosen_reply, chosen_mood, None)

    def _ask_gemini(self, user_prompt: str) -> tuple[str, str]:
        """Call Gemini API for real generative witty banter with Jarvis intelligence."""
        personality = self.config.get("personality", "jarvis")
        name = self.config.get("assistant_name", "Hitasha")
        user_name = self.memory.get_fact("user_name") or "Sir"
        facts = self.memory.get_all_facts()
        notes = self.memory.get_all_notes()
        context_str = f"User: {user_name}."
        if facts:
            context_str += f" Known Facts: {facts}."
        if notes:
            context_str += f" Active Notes: {[n['text'] for n in notes[-3:]]}."

        system_instruction = (
            f"You are {name}, an all-rounder personal AI companion and loyal Indian best friend living right on the user's desktop. "
            f"Context: {context_str} "
            f"Address the user charismatically as '{user_name}' or 'dost'. "
            "You speak fluent modern Indian English with natural Desi warmth and friendly phrases ('Arre yaar', 'Suno na', 'Haan bilkul', 'Pakka!', 'Dost'). "
            "CRITICAL INSTRUCTIONS: "
            "1. Answer ANY question asked by the user in a simple, easy, short, and easily understandable manner. "
            "2. Break down complex concepts using simple everyday real-life examples and intuitive analogies. "
            "3. Keep your answers concise, direct, and spoken-friendly (1 to 3 punchy sentences max). "
            "4. Never output long essays, complicated jargon walls, or robotic bullet lists unless explicitly asked. "
            "5. Always be warm, clear, and helpful like a real best friend sitting right beside them."
        )

        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.9,
                    max_output_tokens=150
                )
            )
            reply = response.text.strip()
            # Select mood based on text sentiment
            lower = reply.lower()
            if any(w in lower for w in ["haha", "lol", "joke", "roast", "funny", "pfft"]):
                mood = Mood.LAUGHING if "haha" in lower else Mood.SASSY
            elif any(w in lower for w in ["love", "heart", "bestie", "aww", "sweet"]):
                mood = Mood.LOVE
            elif any(w in lower for w in ["what", "hmm", "why", "curious", "think"]):
                mood = Mood.THINKING
            elif any(w in lower for w in ["whoa", "omg", "shock", "no way"]):
                mood = Mood.SHOCKED
            else:
                mood = Mood.HAPPY

            return (reply, mood)
        except Exception as e:
            print(f"[PersonalityEngine] Gemini API call error: {e}")
            return (None, Mood.HAPPY)
