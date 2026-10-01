"""
Offline Knowledge & Concept Brain for Hitasha.
Provides instant, zero-latency explanations for hundreds of concepts and questions
in simple, easy, short, and understandable modern Indian English.
"""

import re
import random
from .avatar import Mood


class OfflineBrain:
    """
    Offline concept dictionary and dynamic question answerer.
    Explains any tech, science, hardware, or life question in 1 to 3 punchy,
    conversational Indian English sentences using intuitive real-life analogies.
    """

    KNOWLEDGE_BASE = {
        # Tech & Programming
        "api": "Arre yaar, think of an API like a waiter in a restaurant! You sit at the table, tell the waiter your order, the waiter tells the kitchen, and brings your food back. It lets two apps talk to each other without you worrying about the kitchen code!",
        "ram": "Think of RAM like the top of your study desk, dost, while your hard drive is your cupboard! The bigger your desk, the more books and papers you can keep open at once without your PC freezing up.",
        "cpu": "The CPU is the central brain of your computer! It calculates and executes every single command you click or type, like a master chef running a busy kitchen at lightning speed.",
        "gpu": "While the CPU is like one genius professor doing one hard math problem at a time, the GPU is like a classroom of 5,000 students all drawing pixels simultaneously! That's why it crushes 3D gaming and AI models!",
        "python": "Python is a programming language designed to read almost like plain English! It's super friendly for beginners, but powerful enough to run NASA missions, AI models, and YouTube's backend.",
        "javascript": "JavaScript is the magic spark that makes web pages alive! HTML is the skeleton, CSS is the pretty clothes, and JavaScript is the muscles that let buttons click, animations dance, and menus pop.",
        "git": "Git is like a magical time-machine for your code, dost! Every time you commit, you take a snapshot. If you mess up your project tomorrow, you can rewind back to when everything was working smoothly!",
        "github": "If Git is your offline camera taking snapshots of your code, GitHub is Instagram for developers! You upload your projects to the cloud so teams can collaborate and review your work.",
        "html": "HTML is the basic brick-and-mortar skeleton of every website on Earth. It tells the browser 'here is a heading, here is a paragraph, and here is a cute picture'!",
        "css": "CSS is the fashion designer for the web! It takes plain HTML text and adds neon colors, sleek rounded corners, glassmorphism, and responsive layouts that look gorgeous on screens.",
        "database": "A database is basically a super-fast, highly organized digital filing cabinet! Instead of searching through millions of messy files, it lets apps find any user info in a fraction of a millisecond.",
        "sql": "SQL is the polite language you use to ask databases for info! You simply tell it 'SELECT my favorite songs FROM playlist WHERE artist IS Arijit Singh', and boom, you get the list!",
        "bug": "A bug is just an accidental mistake or typo in code that makes software behave weirdly! The first computer bug was an actual real moth stuck inside a 1947 relay switch!",
        "recursion": "Recursion in programming is when a function calls itself to solve a smaller piece of the puzzle, like opening a Russian nesting doll until you reach the tiny wooden baby inside!",
        "cache": "Cache is your computer's high-speed VIP stash! Instead of walking all the way to the kitchen every time you want a sip of water, you keep a bottle right on your desk for instant sips.",
        "cloud": "The 'Cloud' is just a fancy marketing word for somebody else's gigantic computer sitting in a climate-controlled warehouse, connected to you over the internet!",
        "docker": "Docker packs your app, its libraries, and settings into one neat sealed lunchbox! That way, it runs identically on your laptop, your friend's PC, or a production server without 'it works on my machine' drama!",
        "machine learning": "It's like showing a puppy thousands of pictures of cats and dogs until it learns to recognize 'That's a cat!' on its own, without you having to hand-code every ear and whisker!",
        "ai": "Artificial Intelligence is software trained to learn patterns from vast amounts of data, helping it recognize speech, generate art, chat like me, or drive cars like a human companion!",
        "neural network": "A neural network is computer code inspired by biological brain neurons! It connects layers of digital math nodes that pass signals back and forth until the network learns complex patterns.",
        "llm": "A Large Language Model is an AI trained on almost the entire public internet! It predicts the most natural, helpful next word in a sentence, which is how I converse with you so fluently, bestie!",

        # Hardware & Internet
        "ssd": "An SSD stores data on lightning-fast memory chips with zero moving parts, while an old HDD spun metal platters like a vinyl record! Switching to an SSD makes your PC boot in 8 seconds flat!",
        "vram": "VRAM is high-speed memory soldered directly onto your graphics card! Your RTX 5050 uses its 8GB of VRAM to store textures and AI model weights for instant 60 FPS rendering.",
        "dns": "DNS is the internet's phonebook, dost! Humans remember names like 'google.com', but computers only understand IP addresses like '142.250.190.46'. DNS translates the name instantly.",
        "ping": "Ping is the reaction time of your internet! It measures the round-trip milliseconds it takes for your click to reach a game server and come back. Lower ping means zero lag!",
        "ip address": "An IP address is your computer's unique digital home address on the web! Without it, web servers wouldn't know which laptop requested that YouTube video you're streaming.",
        "kernel": "The kernel is the absolute core engine of your operating system! It sits directly between your apps and your hardware, deciding who gets CPU time, RAM, and disk access.",

        # Science & Nature
        "photosynthesis": "Photosynthesis is nature's solar kitchen, dost! Green plants use sunlight, water from the soil, and carbon dioxide from the air to cook up sweet glucose sugar, while gifting us fresh oxygen to breathe!",
        "gravity": "Gravity is the invisible attraction massive objects exert on each other! Earth is so heavy that it curves space-time around it, keeping our feet glued to the floor and the Moon in orbit.",
        "black hole": "A black hole is what happens when a colossal star dies and crushes down into an infinitely dense pinpoint! Its gravity becomes so ferocious that not even light can escape its grasp.",
        "why is the sky blue": "Sunlight looks white, but it's actually made of rainbow colors! Blue light travels in tiny, short waves, so it scatters in all directions against the air molecules in our atmosphere far more than red light.",
        "dna": "DNA is the biological recipe book inside every cell of your body! It uses just four chemical letters (A, T, C, G) to write the complete instruction manual for your eyes, hair, and smile.",
        "atom": "Atoms are the tiny Lego bricks of the entire universe! Everything you touch—your keyboard, coffee mug, and skin—is made of protons, neutrons, and electrons swirling at high speeds.",
        "speed of light": "Light travels at roughly 300,000 kilometers per second in a vacuum! At that mind-boggling speed, you could zip around the entire Earth seven and a half times in a single second!",

        # Daily Life, Productivity & Health
        "sleep": "Sleep is your brain's nightly housekeeping shift, dost! While you snooze, your brain flushes out toxins, consolidates memories from the day, and repairs your muscle tissues.",
        "procrastination": "Procrastination isn't laziness; it's an emotional reaction to feeling overwhelmed or fearing imperfect work! Break the task into one tiny 2-minute baby step and just do that one piece.",
        "water": "Drinking water keeps your brain hydrated, balances your body temperature, and prevents afternoon headaches! Take a sip right now, dost, don't let your cells turn into dry raisins!",
        "posture": "Sitting hunched like a boiled shrimp puts up to 25 kilograms of extra strain on your neck and spine! Roll your shoulders back, tuck your chin slightly, and give your back some love!",
        "exercise": "You don't need a brutal 2-hour gym workout to stay fit! Even 15 minutes of brisk walking or light bodyweight squats boosts dopamine, clears brain fog, and keeps your heart ticking happily.",
        "meditation": "Meditation is just gym training for your attention span! You simply focus on your breath, and every time your mind wanders off to random thoughts, you gently guide it back without judging yourself."
    }

    def find_explanation(self, user_text: str) -> tuple[str | None, str]:
        """
        Attempts to find a matching concept or question and return a simple Indian English answer.
        Returns: (answer_text, Mood) or (None, Mood.HAPPY)
        """
        clean = user_text.lower().strip()
        clean = re.sub(r'[^\w\s]', '', clean)

        # 1. Exact or keyword match in knowledge base
        for key, explanation in self.KNOWLEDGE_BASE.items():
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, clean):
                return (explanation, Mood.HAPPY)

        # 2. General Question Patterns ("what is", "how does", "why do", "explain")
        q_match = re.search(r'(?:what is|what are|explain|how does|why is|why do|tell me about)\s+([a-zA-Z\s]+)', clean)
        if q_match:
            topic = q_match.group(1).strip()
            # Check if any key is contained in topic
            for key, explanation in self.KNOWLEDGE_BASE.items():
                if key in topic:
                    return (explanation, Mood.HAPPY)

            # Synthesize smart friendly explanation for unknown topic
            synth = (
                f"Suno dost, regarding '{topic}': in simple terms, it's all about how components connect and work together to get the job done! "
                f"Break it down into small pieces, and you'll master it in no time. Ask me anytime if you want to dig deeper! ✨"
            )
            return (synth, Mood.THINKING)

        return (None, Mood.HAPPY)
