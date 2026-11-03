"""
Lesson text and check questions for LearnCrypt.

All the words the learner reads are kept here, separate from the app code,
so they are easy to read, correct and improve without touching the logic.
Lessons use everyday comparisons and avoid technical words where possible.
Technical words that are needed are explained in the glossary at the bottom.
"""

# Module list: (page name, short description shown on the home page)
MODULES = [
    ("1. What is cryptography?", "The big idea in five minutes: messages, keys and locks."),
    ("2. Secret codes from history", "Try the codes people used hundreds of years ago."),
    ("3. How old codes are broken", "Be the code breaker and see why old codes are not safe."),
    ("4. How your phone keeps secrets", "The modern methods that protect WhatsApp, mobile money and banks."),
    ("5. How fast is it?", "Compare the speed of old and modern methods."),
]

# Module 1: What is cryptography?
INTRO_LESSON = """
**Cryptography** is the art of keeping messages secret, so that only the right person can read them.

You already use it every day, usually without noticing:

- when you send a **WhatsApp** message,
- when you enter your **mobile money PIN**,
- when you log in to **online banking**,
- when you see the small **padlock** next to a website address.

In all of these, your information travels through many computers and cables before it arrives.
Cryptography makes sure that anyone who catches it on the way sees only nonsense.
"""

INTRO_WORDS = [
    ("Message", "What you want to send, for example *Meet me at 10*."),
    ("Key", "A secret that both people know. It is used to lock and unlock the message."),
    ("Locked message", "The message after it has been scrambled. Without the key it looks like nonsense, for example *Phhw ph dw 10*."),
]

INTRO_LESSON_2 = """
Think of a **locked box**. You put a letter inside, lock it with a key, and send the box.
Anyone can carry the box, but only someone with the right key can open it and read the letter.

**Encrypting** means putting the message in the box and locking it.
**Decrypting** means unlocking the box and reading the message again.

In LearnCrypt you will move from the simple codes people used long ago, to how those codes
were broken, to the strong methods that protect your phone today. Each part starts with a short
lesson and two or three questions. When you get them right, the hands-on activity opens.
"""

INTRO_QUIZ = [
    {
        "q": "What does encryption do to a message?",
        "options": [
            "Makes it shorter",
            "Turns it into nonsense that only someone with the key can turn back",
            "Deletes it after it is read",
        ],
        "answer": 1,
        "explain": "Encryption scrambles the message. The key is needed to unscramble it.",
    },
    {
        "q": "Which of these uses cryptography?",
        "options": [
            "Sending a WhatsApp message",
            "Reading a printed newspaper",
            "Listening to the radio",
        ],
        "answer": 0,
        "explain": "WhatsApp messages are encrypted on your phone before they are sent.",
    },
    {
        "q": "In our 'locked box' picture, what is the key?",
        "options": [
            "The message itself",
            "The person carrying the box",
            "The secret that locks and unlocks the box",
        ],
        "answer": 2,
        "explain": "The key is the secret. Without it, the box (the locked message) stays shut.",
    },
]

# Module 2: Secret codes from history
CLASSICAL_LESSON = """
Long before computers, people already needed to send secrets: armies, kings and traders.
They used **codes that change letters into other letters**. Here are three famous ones.
"""

CLASSICAL_CARDS = [
    ("Caesar code", "About 2,000 years old",
     "Every letter moves the same number of places along the alphabet. "
     "With a move of 3, **A** becomes **D**, **B** becomes **E**, and so on. "
     "The key is just the number of places."),
    ("Vigenère code", "About 450 years old",
     "Like Caesar, but the move changes from letter to letter, following a **keyword**. "
     "With the keyword *LEMON*, the first letter moves 11 places (L), the next 4 (E), and so on."),
    ("Playfair code", "About 170 years old",
     "Letters are locked **two at a time** using a 5 by 5 grid of letters made from a keyword. "
     "Each pair of letters is swapped for another pair from the grid."),
]

CLASSICAL_QUIZ = [
    {
        "q": "In a Caesar code with a move of 3, what does the letter A become?",
        "options": ["B", "C", "D"],
        "answer": 2,
        "explain": "A moves three places: A → B → C → D.",
    },
    {
        "q": "What makes the Vigenère code harder to read than Caesar?",
        "options": [
            "It uses numbers instead of letters",
            "The move changes from letter to letter, following a keyword",
            "It only works on short words",
        ],
        "answer": 1,
        "explain": "In Caesar every letter moves the same amount. Vigenère follows a keyword, so the move keeps changing.",
    },
]

# Module 3: How old codes are broken
BREAKING_LESSON = """
A code is only useful if outsiders **cannot** work out the message. The old codes fail this test
for two simple reasons.
"""

BREAKING_CARDS = [
    ("Too few keys", "Caesar has only 25 possible moves. A person could try them all in an afternoon. "
     "A computer tries them all in less than a second, then picks the one that looks like real words."),
    ("Language leaves fingerprints", "In English, **E** is the most common letter, then **T** and **A**, while "
     "**Q** and **Z** are rare. Old codes move letters around but keep these patterns. By counting letters, "
     "a code breaker can guess the key. This is called **frequency analysis**."),
]

BREAKING_LESSON_2 = """
The Vigenère code was called *"the unbreakable code"* for about 300 years. It falls the same way:
first the computer works out how long the keyword is, then it breaks each part like a Caesar code.

This is the big lesson: **a good code must hide every pattern**. That is exactly what modern methods do,
as you will see in part 4.
"""

BREAKING_QUIZ = [
    {
        "q": "Why can a computer break a Caesar code so quickly?",
        "options": [
            "There are only 25 possible keys to try",
            "Computers can read any language",
            "Caesar codes are always written in capital letters",
        ],
        "answer": 0,
        "explain": "With only 25 keys, a computer simply tries every one.",
    },
    {
        "q": "What does frequency analysis look at?",
        "options": [
            "How often the message is sent",
            "How often each letter appears",
            "How long the message is",
        ],
        "answer": 1,
        "explain": "Common letters like E and T still stand out in the locked message, and that gives the key away.",
    },
]

# Secret messages for the Caesar code-breaking activity (Part 3).
# The app locks one of these with a random key, so the learner has something to break.
MYSTERY_MESSAGES = [
    "Meet me at the old bridge tonight",
    "The money is hidden under the blue chair",
    "Bring the map to the market on Friday",
    "Do not open the door before noon",
    "The parcel arrives at the bus depot at six",
]

# Module 4: How your phone keeps secrets
MODERN_LESSON = """
Today's methods are built so that the locked message looks like **random noise**, with no pattern to count.
Your phone uses three main tools. You do not need any maths to understand the idea behind each one.
"""

MODERN_CARDS = [
    ("AES: a shared secret key",
     "Like a house key: the **same key** locks and unlocks. Here the key is made from a password you choose. "
     "A full AES key has so many possible values that no computer today can try them all, so the weak point "
     "is usually a short or common password. AES protects the messages themselves in WhatsApp, Wi-Fi and bank apps."),
    ("RSA: a public padlock",
     "Imagine giving everyone an **open padlock**. Anyone can snap it shut on a box for you, "
     "but only **you** have the key that opens it. The padlock is your *public key*, the key is your *private key*. "
     "It also lets you **sign** a message, like a wax seal that proves it came from you and was not changed."),
    ("SHA-256: a digital fingerprint",
     "Turns any message into a short **fingerprint**. The same message always gives the same fingerprint, "
     "but change one letter and the fingerprint changes completely. You cannot turn a fingerprint back into "
     "the message. Used to check that files and passwords have not been changed."),
]

MODERN_QUIZ = [
    {
        "q": "With AES, which key unlocks the message?",
        "options": [
            "The same key that locked it",
            "Any key, as long as it is long",
            "A key from a different person",
        ],
        "answer": 0,
        "explain": "AES is like a house key: one shared secret key both locks and unlocks.",
    },
    {
        "q": "With RSA, which key do you share with other people?",
        "options": ["The private key", "The public key (the open padlock)", "Both keys"],
        "answer": 1,
        "explain": "You hand out open padlocks (public key) freely, and keep the key that opens them (private key) to yourself.",
    },
    {
        "q": "What happens to a SHA-256 fingerprint if you change one letter of the message?",
        "options": ["It stays the same", "Only one character changes", "It changes completely"],
        "answer": 2,
        "explain": "This is called the avalanche effect: a tiny change gives a totally different fingerprint.",
    },
]

# Module 5: How fast is it?
SPEED_LESSON = """
Security is not enough on its own: your phone must also lock and unlock messages **instantly**,
or apps would feel slow.

The old codes in this app were written step by step in simple Python, so that you can follow them.
The modern methods come from a specialist library written in fast, carefully tested code, and many
phones and computers even have a special part of the chip just for AES.

In this part you can run a small race between the methods and see the difference for yourself.
"""

SPEED_QUIZ = [
    {
        "q": "Why must encryption be fast?",
        "options": [
            "So that apps do not feel slow when they protect your messages",
            "Because slow encryption is easier to break",
            "It does not need to be fast",
        ],
        "answer": 0,
        "explain": "Every message, photo and payment is encrypted, so it must happen in a blink.",
    },
    {
        "q": "Should you write your own encryption code for a real app?",
        "options": [
            "Yes, it is safer if nobody else knows how it works",
            "No, use a well-tested library made by experts",
        ],
        "answer": 1,
        "explain": "Even professional developers make mistakes with encryption. Tested libraries are much safer.",
    },
]

# Glossary
GLOSSARY = [
    ("Cryptography", "Keeping information secret and safe by turning it into a form only the right people can read."),
    ("Encrypt", "To lock a message so it becomes unreadable."),
    ("Decrypt", "To unlock a locked message so it can be read again."),
    ("Key", "The secret used to lock and unlock. Can be a number, a word or a long random value."),
    ("Locked message (ciphertext)", "The scrambled version of a message."),
    ("Code breaking (cryptanalysis)", "Working out a secret message without being given the key."),
    ("Frequency analysis", "Counting how often each letter appears, to guess how a message was scrambled."),
    ("AES", "The world's standard method for locking data with one shared secret key."),
    ("RSA", "A method that uses two keys: a public one to lock and a private one to unlock."),
    ("Public key", "The 'open padlock' you can give to anyone."),
    ("Private key", "The secret key you never share. It opens what your public key locked."),
    ("Digital signature", "Proof, made with your private key, that a message came from you and was not changed."),
    ("Hash / fingerprint (SHA-256)", "A short code that identifies a message. It cannot be turned back into the message."),
    ("Password-based key (PBKDF2)", "A slow, careful way of turning a password into a strong key, so guessing passwords takes longer."),
    ("Salt", "A random value mixed in when a key is made, so the same password gives a different key each time."),
]
