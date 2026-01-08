import logging
import json
import os
import asyncio
import sys
from datetime import timedelta
from telegram.constants import ChatMemberStatus
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ---------- Настройки ----------
BOT_TOKEN = "8291804416:AAHqlpSYJGJc3PhxpuY2ySgvwdpKng048c0"        # ← ЗАМЕНИТЕ
OWNER_ID = 6591792069                        # ← ВАШ Telegram ID (число!)
BLACKLIST_FILE = "blocked_media.json"
CACHE_FILE = "sticker_titles_cache.json"

# 🔥 Ключевые слова (проверяются и в set_name, и в title)
BAD_KEYWORDS = {
    "nsfw", "xxx", "porn", "adult", "sex", "fuck", "bitch", "nude", "hentai", "NSFW",
    "erotic", "lewd", "r18", "18+", "kinky", "sexy", "xхх", "ххх", "порно", "секс", "эротика",
    "hot", "horny", "boobs", "ass", "cum", "fuck", "anal", "gay", "lesbian", "yaoi", "yuri," "2g1c", "2 girls 1 cup", "acrotomophilia", "alabama hot pocket",
    "alaskan pipeline",
    "anal",
    "anilingus",
    "anus",
    "apeshit",
    "arsehole",
    "ass",
    "asshole",
    "assmunch",
    "auto erotic",
    "autoerotic",
    "babeland",
    "baby batter",
    "baby juice",
    "ball gag",
    "ball gravy",
    "ball kicking",
    "ball licking",
    "ball sack",
    "ball sucking",
    "bangbros",
    "bareback",
    "barely legal",
    "barenaked",
    "bastard",
    "bastardo",
    "bastinado",
    "bbw",
    "bdsm",
    "beaner",
    "beaners",
    "beaver cleaver",
    "beaver lips",
    "bestiality",
    "big black",
    "big breasts",
    "big knockers",
    "big tits",
    "bimbos",
    "birdlock",
    "bitch",
    "bitches",
    "black cock",
    "blonde action",
    "blonde on blonde action",
    "blowjob",
    "blow job",
    "blow your load",
    "blue waffle",
    "blumpkin",
    "bollocks",
    "bondage",
    "boner",
    "boob",
    "boobs",
    "booty call",
    "brown showers",
    "brunette action",
    "bukkake",
    "bulldyke",
    "bullet vibe",
    "bullshit",
    "bung hole",
    "bunghole",
    "busty",
    "butt",
    "buttcheeks",
    "butthole",
    "camel toe",
    "camgirl",
    "camslut",
    "camwhore",
    "carpet muncher",
    "carpetmuncher",
    "chocolate rosebuds",
    "circlejerk",
    "cleveland steamer",
    "clit",
    "clitoris",
    "clover clamps",
    "clusterfuck",
    "cock",
    "cocks",
    "coprolagnia",
    "coprophilia",
    "cornhole",
    "coon",
    "coons",
    "creampie",
    "cum",
    "cumming",
    "cunnilingus",
    "cunt",
    "darkie",
    "date rape",
    "daterape",
    "deep throat",
    "deepthroat",
    "dendrophilia",
    "dick",
    "dildo",
    "dingleberry",
    "dingleberries",
    "dirty pillows",
    "dirty sanchez",
    "doggie style",
    "doggiestyle",
    "doggy style",
    "doggystyle",
    "dog style",
    "dolcett",
    "domination",
    "dominatrix",
    "dommes",
    "donkey punch",
    "double dong",
    "double penetration",
    "dp action",
    "dry hump",
    "dvda",
    "eat my ass",
    "ecchi",
    "ejaculation",
    "erotic",
    "erotism",
    "escort",
    "eunuch",
    "faggot",
    "fecal",
    "felch",
    "fellatio",
    "feltch",
    "female squirting",
    "femdom",
    "figging",
    "fingerbang",
    "fingering",
    "fisting",
    "foot fetish",
    "footjob",
    "frotting",
    "fuck",
    "fuck buttons",
    "fuckin",
    "fucking",
    "fucktards",
    "fudge packer",
    "fudgepacker",
    "futanari",
    "gang bang",
    "gay sex",
    "genitals",
    "giant cock",
    "girl on",
    "girl on top",
    "girls gone wild",
    "goatcx",
    "goatse",
    "god damn",
    "gokkun",
    "golden shower",
    "goodpoop",
    "goo girl",
    "goregasm",
    "grope",
    "group sex",
    "g-spot",
    "guro",
    "hand job",
    "handjob",
    "hard core",
    "hardcore",
    "hentai",
    "homoerotic",
    "honkey",
    "hooker",
    "hot carl",
    "hot chick",
    "how to kill",
    "how to murder",
    "huge fat",
    "humping",
    "incest",
    "intercourse",
    "jack off",
    "jail bait",
    "jailbait",
    "jelly donut",
    "jerk off",
    "jigaboo",
    "jiggaboo",
    "jiggerboo",
    "jizz",
    "juggs",
    "kike",
    "kinbaku",
    "kinkster",
    "kinky",
    "knobbing",
    "leather restraint",
    "leather straight jacket",
    "lemon party",
    "lolita",
    "lovemaking",
    "make me come",
    "male squirting",
    "masturbate",
    "menage a trois",
    "milf",
    "missionary position",
    "motherfucker",
    "mound of venus",
    "mr hands",
    "muff diver",
    "muffdiving",
    "nambla",
    "nawashi",
    "negro",
    "neonazi",
    "nigga",
    "nigger",
    "nig nog",
    "nimphomania",
    "nipple",
    "nipples",
    "nsfw images",
    "nude",
    "nudity",
    "nympho",
    "nymphomania",
    "octopussy",
    "omorashi",
    "one cup two girls",
    "one guy one jar",
    "orgasm",
    "orgy",
    "paedophile",
    "paki",
    "panties",
    "panty",
    "pedobear",
    "pedophile",
    "pegging",
    "penis",
    "phone sex",
    "piece of shit",
    "pissing",
    "piss pig",
    "pisspig",
    "playboy",
    "pleasure chest",
    "pole smoker",
    "ponyplay",
    "poof",
    "poon",
    "poontang",
    "punany",
    "poop chute",
    "poopchute",
    "porn",
    "porno",
    "pornography",
    "prince albert piercing",
    "pthc",
    "pubes",
    "pussy",
    "queaf",
    "queef",
    "quim",
    "raghead",
    "raging boner",
    "rape",
    "raping",
    "rapist",
    "rectum",
    "reverse cowgirl",
    "rimjob",
    "rimming",
    "rosy palm",
    "rosy palm and her 5 sisters",
    "rusty trombone",
    "sadism",
    "santorum",
    "scat",
    "schlong",
    "scissoring",
    "semen",
    "sex",
    "sexo",
    "sexy",
    "shaved beaver",
    "shaved pussy",
    "shemale",
    "shibari",
    "shit",
    "shitblimp",
    "shitty",
    "shota",
    "shrimping",
    "skeet",
    "slanteye",
    "slut",
    "s&m",
    "smut",
    "snatch",
    "snowballing",
    "sodomize",
    "sodomy",
    "spic",
    "splooge",
    "splooge moose",
    "spooge",
    "spread legs",
    "spunk",
    "strap on",
    "strapon",
    "strappado",
    "strip club",
    "style doggy",
    "suck",
    "sucks",
    "suicide girls",
    "sultry women",
    "swastika",
    "swinger",
    "tainted love",
    "taste my",
    "tea bagging",
    "threesome",
    "throating",
    "tied up",
    "tight white",
    "tit",
    "tits",
    "titties",
    "titty",
    "tongue in a",
    "topless",
    "tosser",
    "towelhead",
    "tranny",
    "tribadism",
    "tub girl",
    "tubgirl",
    "tushy",
    "twat",
    "twink",
    "twinkie",
    "two girls one cup",
    "undressing",
    "upskirt",
    "urethra play",
    "urophilia",
    "vagina",
    "venus mound",
    "vibrator",
    "violet wand",
    "vorarephilia",
    "voyeur",
    "vulva",
    "wank",
    "wetback",
    "wet dream",
    "white power",
    "wrapping men",
    "wrinkled starfish",
    "xx",
    "xxx",
    "yaoi",
    "yellow showers",
    "yiffy",
    "zoophilia",
    "arse",
    "ballsack",
    "balls",
    "biatch",
    "bloody",
    "bollock",
    "bollok",
    "bugger",
    "bum",
    "buttplug",
    "crap",
    "damn",
    "dyke",
    "fag",
    "feck",
    "fellate",
    "felching",
    "f u c k",
    "flange",
    "Goddamn",
    "God damn",
    "hell",
    "homo",
    "jerk",
    "knobend",
    "knob end",
    "labia",
    "lmao",
    "lmfao",
    "muff",
    "omg",
    "piss",
    "poop",
    "prick",
    "pube",
    "queer",
    "scrotum",
    "s hit",
    "sh1t",
    "smegma",
    "turd",
    "whore",
    "4r5e",
    "50 yard cunt punt",
    "5h1t",
    "5hit",
    "a_s_s",
    "a2m",
    "a$$",
    "a55",
    "a$$hole",
    "a55hole",
    "adult",
    "aeolus",
    "ahole",
    "amateur",
    "anal impaler",
    "anal leakage",
    "analprobe",
    "ar5e",
    "areola",
    "areole",
    "arian",
    "arrse",
    "aryan",
    "ass fuck",
    "ass hole",
    "ass-fucker",
    "assbang",
    "assbanged",
    "assbangs",
    "asses",
    "assfuck",
    "assfucker",
    "assfukka",
    "assh0le",
    "asshat",
    "assho1e",
    "assholes",
    "assmaster",
    "assmucus",
    "asswhole",
    "asswipe",
    "asswipes",
    "azazel",
    "azz",
    "b!tch",
    "b00bs",
    "b17ch",
    "b1tch",
    "babe",
    "babes",
    "ballbag",
    "bang",
    "bang (one's) box",
    "banger",
    "barf",
    "bastards",
    "bawdy",
    "beardedclam",
    "beastial",
    "beastiality",
    "beatch",
    "beater",
    "beaver",
    "beef curtain",
    "beef curtain",
    "beer",
    "beeyotch",
    "bellend",
    "beotch",
    "bestial",
    "bi+ch",
    "bigtits",
    "bimbo",
    "bitch tit",
    "bitched",
    "bitcher",
    "bitchers",
    "bitchin",
    "bitching",
    "bitchy",
    "blow",
    "blow me",
    "blow mud",
    "blowjobs",
    "blue waffle",
    "blumpkin",
    "bod",
    "bodily",
    "boink",
    "boiolas",
    "bone",
    "boned",
    "boners",
    "bong",
    "boobies",
    "booby",
    "booger",
    "bookie",
    "booobs",
    "boooobs",
    "booooobs",
    "booooooobs",
    "bootee",
    "bootie",
    "booty",
    "booze",
    "boozer",
    "boozy",
    "bosom",
    "bosomy",
    "bowel",
    "bowels",
    "bra",
    "brassiere",
    "breast",
    "breasts",
    "buceta",
    "bull shit",
    "bullshits",
    "bullshitted",
    "bullturds",
    "bung",
    "bunny fucker",
    "bust a load",
    "butt fuck",
    "butt fuck",
    "buttfuck",
    "buttfucker",
    "buttmuch",
    "c-0-c-k",
    "c-o-c-k",
    "c-u-n-t",
    "c.0.c.k",
    "c.o.c.k.",
    "c.u.n.t",
    "c0ck",
    "c0cksucker",
    "caca",
    "cahone",
    "cameltoe",
    "cawk",
    "cervix",
    "chinc",
    "chincs",
    "chink",
    "choade",
    "chode",
    "chodes",
    "chota bags",
    "cipa",
    "cl1t",
    "climax",
    "clit licker",
    "clitorus",
    "clits",
    "clitty",
    "clitty litter",
    "cnut",
    "cocain",
    "cocaine",
    "cock pocket",
    "cock snot",
    "cock sucker",
    "cock-sucker",
    "cockblock",
    "cockface",
    "cockhead",
    "cockholster",
    "cockknocker",
    "cockmunch",
    "cockmuncher",
    "cocksmoker",
    "cocksuck",
    "cocksucked",
    "cocksucker",
    "cocksucking",
    "cocksucks",
    "cocksuka",
    "cocksukka",
    "coital",
    "cok",
    "cokmuncher",
    "coksucka",
    "commie",
    "condom",
    "cop some wood",
    "corksucker",
    "cornhole",
    "corp whore",
    "cox",
    "crabs",
    "crack",
    "cracker",
    "crackwhore",
    "crappy",
    "cum chugger",
    "cum dumpster",
    "cum freak",
    "cum guzzler",
    "cumdump",
    "cummer",
    "cummin",
    "cums",
    "cumshot",
    "cumshots",
    "cumslut",
    "cumstain",
    "cunilingus",
    "cunillingus",
    "cunny",
    "cunt hair",
    "cunt-struck",
    "cuntbag",
    "cuntface",
    "cunthunter",
    "cuntlick",
    "cuntlick",
    "cuntlicker",
    "cuntlicker",
    "cuntlicking",
    "cunts",
    "cuntsicle",
    "cut rope",
    "cyalis",
    "cyberfuc",
    "cyberfuck",
    "cyberfucked",
    "cyberfucker",
    "cyberfuckers",
    "cyberfucking",
    "d0ng",
    "d0uch3",
    "d0uche",
    "d1ck",
    "d1ld0",
    "d1ldo",
    "dago",
    "dagos",
    "dammit",
    "damned",
    "damnit",
    "dawgie-style",
    "dick hole",
    "dick shy",
    "dick-ish",
    "dickbag",
    "dickdipper",
    "dickface",
    "dickflipper",
    "dickhead",
    "dickheads",
    "dickish",
    "dickripper",
    "dicksipper",
    "dickweed",
    "dickwhipper",
    "dickzipper",
    "diddle",
    "dike",
    "dildos",
    "diligaf",
    "dillweed",
    "dimwit",
    "dingle",
    "dink",
    "dinks",
    "dipship",
    "dirsa",
    "dirty Sanchez",
    "dlck",
    "dog-fucker",
    "doggie-style",
    "doggin",
    "dogging",
    "doggy-style",
    "dong",
    "donkeyribber",
    "doofus",
    "doosh",
    "dopey",
    "douch3",
    "douche",
    "douchebag",
    "douchebags",
    "douchey",
    "drunk",
    "duche",
    "dumass",
    "dumbass",
    "dumbasses",
    "dummy",
    "dykes",
    "eat a dick",
    "eat hair pie",
    "ejaculate",
    "ejaculated",
    "ejaculates",
    "ejaculating",
    "ejakulate",
    "enlargement",
    "erect",
    "erection",
    "essohbee",
    "extacy",
    "extasy",
    "f u c k e r",
    "f_u_c_k",
    "f-u-c-k",
    "f.u.c.k",
    "f4nny",
    "facial",
    "fack",
    "fagg",
    "fagged",
    "fagging",
    "faggit",
    "faggitt",
    "faggs",
    "fagot",
    "fagots",
    "fags",
    "faig",
    "faigt",
    "fanny",
    "fannybandit",
    "fannyflaps",
    "fannyfucker",
    "fanyy",
    "fart",
    "fartknocker",
    "fat",
    "fatass",
    "fcuk",
    "fcuker",
    "fcuking",
    "fecker",
    "felcher",
    "feltcher",
    "fingerfuck",
    "fingerfucked",
    "fingerfucker",
    "fingerfuckers",
    "fingerfucking",
    "fingerfucks",
    "fist fuck",
    "fisted",
    "fistfuck",
    "fistfucked",
    "fistfucker",
    "fistfuckers",
    "fistfucking",
    "fistfuckings",
    "fistfucks",
    "fisty",
    "flog the log",
    "floozy",
    "foad",
    "fondle",
    "foobar",
    "fook",
    "fooker",
    "foreskin",
    "freex",
    "frigg",
    "frigga",
    "fubar",
    "fuck",
    "fuck hole",
    "fuck puppet",
    "fuck trophy",
    "fuck yo mama",
    "fuck-ass",
    "fuck-bitch",
    "fuck-tard",
    "fucka",
    "fuckass",
    "fucked",
    "fucker",
    "fuckers",
    "fuckface",
    "fuckhead",
    "fuckheads",
    "fuckings",
    "fuckingshitmotherfucker",
    "fuckme",
    "fuckmeat",
    "fucknugget",
    "fucknut",
    "fuckoff",
    "fucks",
    "fucktard",
    "fucktoy",
    "fuckup",
    "fuckwad",
    "fuckwhit",
    "fuckwit",
    "fuk",
    "fuker",
    "fukker",
    "fukkin",
    "fuks",
    "fukwhit",
    "fukwit",
    "fux",
    "fux0r",
    "fvck",
    "fxck",
    "gae",
    "gai",
    "gang-bang",
    "gangbang",
    "gangbang",
    "gangbanged",
    "gangbangs",
    "ganja",
    "gassy ass",
    "gay",
    "gaylord",
    "gays",
    "gaysex",
    "gey",
    "gfy",
    "ghay",
    "ghey",
    "gigolo",
    "glans",
    "god-dam",
    "god-damned",
    "godamn",
    "godamnit",
    "goddam",
    "goddammit",
    "goddamn",
    "goddamned",
    "goldenshower",
    "gonad",
    "gonads",
    "gook",
    "gooks",
    "gringo",
    "gspot",
    "gtfo",
    "guido",
    "h0m0",
    "h0mo",
    "ham flap",
    "hard on",
    "hardcoresex",
    "he11",
    "hebe",
    "heeb",
    "hemp",
    "heroin",
    "herp",
    "herpes",
    "herpy",
    "heshe",
    "hitler",
    "hiv",
    "hoar",
    "hoare",
    "hobag",
    "hoer",
    "hom0",
    "homey",
    "homoey",
    "honky",
    "hooch",
    "hookah",
    "hoor",
    "hootch",
    "hooter",
    "hooters",
    "hore",
    "horniest",
    "horny",
    "hotsex",
    "how to murdep",
    "hump",
    "humped",
    "hussy",
    "hymen",
    "inbred",
    "injun",
    "j3rk0ff",
    "jack-off",
    "jackass",
    "jackhole",
    "jackoff",
    "jap",
    "japs",
    "jerk-off",
    "jerk0ff",
    "jerked",
    "jerkoff",
    "jism",
    "jiz",
    "jizm",
    "jizzed",
    "junkie",
    "junky",
    "kawk",
    "kikes",
    "kill",
    "kinky Jesus",
    "kkk",
    "klan",
    "knob",
    "knobead",
    "knobed",
    "knobhead",
    "knobjocky",
    "knobjokey",
    "kock",
    "kondum",
    "kondums",
    "kooch",
    "kooches",
    "kootch",
    "kraut",
    "kum",
    "kummer",
    "kumming",
    "kums",
    "kunilingus",
    "kwif",
    "kyke",
    "l3i+ch",
    "l3itch",
    "lech",
    "LEN",
    "leper",
    "lesbians",
    "lesbo",
    "lesbos",
    "lez",
    "lezbian",
    "lezbians",
    "lezbo",
    "lezbos",
    "lezzie",
    "lezzies",
    "lezzy",
    "loin",
    "loins",
    "lube",
    "lust",
    "lusting",
    "lusty",
    "m-fucking",
    "m0f0",
    "m0fo",
    "m45terbate",
    "ma5terb8",
    "ma5terbate",
    "mafugly",
    "mams",
    "masochist",
    "massa",
    "master-bate",
    "masterb8",
    "masterbat*",
    "masterbat3",
    "masterbate",
    "masterbating",
    "masterbation",
    "masterbations",
    "masturbating",
    "masturbation",
    "maxi",
    "menses",
    "menstruate",
    "menstruation",
    "meth",
    "mo-fo",
    "mof0",
    "mofo",
    "molest",
    "moolie",
    "moron",
    "mothafuck",
    "mothafucka",
    "mothafuckas",
    "mothafuckaz",
    "mothafucked",
    "mothafucker",
    "mothafuckers",
    "mothafuckin",
    "mothafucking",
    "mothafuckings",
    "mothafucks",
    "mother fucker",
    "mother fucker",
    "motherfuck",
    "motherfucka",
    "motherfucked",
    "motherfuckers",
    "motherfuckin",
    "motherfucking",
    "motherfuckings",
    "motherfuckka",
    "motherfucks",
    "mtherfucker",
    "mthrfucker",
    "mthrfucking",
    "muff puff",
    "muffdiver",
    "murder",
    "mutha",
    "muthafecker",
    "muthafuckaz",
    "muthafucker",
    "muthafuckker",
    "muther",
    "mutherfucker",
    "mutherfucking",
    "muthrfucking",
    "n1gga",
    "n1gger",
    "nad",
    "nads",
    "naked",
    "napalm",
    "nappy",
    "nazi",
    "nazism",
    "need the dick",
    "nigg3r",
    "nigg4h",
    "niggah",
    "niggas",
    "niggaz",
    "niggers",
    "niggle",
    "niglet",
    "nimrod",
    "ninny",
    "nob",
    "nob jokey",
    "nobhead",
    "nobjocky",
    "nobjokey",
    "nooky",
    "numbnuts",
    "nut butter",
    "nutsack",
    "opiate",
    "opium",
    "oral",
    "orally",
    "organ",
    "orgasim",
    "orgasims",
    "orgasmic",
    "orgasms",
    "orgies",
    "ovary",
    "ovum",
    "ovums",
    "p.u.s.s.y.",
    "p0rn",
    "paddy",
    "pantie",
    "pastie",
    "pasty",
    "pawn",
    "pcp",
    "pecker",
    "pedo",
    "pedophilia",
    "pedophiliac",
    "pee",
    "peepee",
    "penetrate",
    "penetration",
    "penial",
    "penile",
    "penisfucker",
    "perversion",
    "peyote",
    "phalli",
    "phallic",
    "phonesex",
    "phuck",
    "phuk",
    "phuked",
    "phuking",
    "phukked",
    "phukking",
    "phuks",
    "phuq",
    "pigfucker",
    "pillowbiter",
    "pimp",
    "pimpis",
    "pinko",
    "piss-off",
    "pissed",
    "pisser",
    "pissers",
    "pisses",
    "pissflaps",
    "pissin",
    "pissoff",
    "pissoff",
    "pms",
    "polack",
    "pollock",
    "pornos",
    "pot",
    "potty",
    "pricks",
    "prig",
    "pron",
    "prostitute",
    "prude",
    "pubic",
    "pubis",
    "punkass",
    "punky",
    "puss",
    "pusse",
    "pussi",
    "pussies",
    "pussy fart",
    "pussy palace",
    "pussypounder",
    "pussys",
    "puto",
    "queaf",
    "queero",
    "queers",
    "quicky",
    "r-tard",
    "racy",
    "raped",
    "raper",
    "raunch",
    "rectal",
    "rectus",
    "reefer",
    "reetard",
    "reich",
    "retard",
    "retarded",
    "revue",
    "rimjaw",
    "ritard",
    "rtard",
    "rum",
    "rump",
    "rumprammer",
    "ruski",
    "s_h_i_t",
    "s-h-1-t",
    "s-h-i-t",
    "s-o-b",
    "s.h.i.t.",
    "s.o.b.",
    "s0b",
    "sadist",
    "sandbar",
    "sausage queen",
    "scag",
    "scantily",
    "schizo",
    "screw",
    "screwed",
    "screwing",
    "scroat",
    "scrog",
    "scrot",
    "scrote",
    "scrud",
    "scum",
    "seaman",
    "seamen",
    "seduce",
    "sexual",
    "sh!+",
    "sh!t",
    "shag",
    "shagger",
    "shaggin",
    "shagging",
    "shamedame",
    "shi+",
    "shit fucker",
    "shitdick",
    "shite",
    "shiteater",
    "shited",
    "shitey",
    "shitface",
    "shitfuck",
    "shitfull",
    "shithead",
    "shithole",
    "shithouse",
    "shiting",
    "shitings",
    "shits",
    "shitt",
    "shitted",
    "shitter",
    "shitters",
    "shitting",
    "shittings",
    "shiz",
    "sissy",
    "skag",
    "skank",
    "slave",
    "sleaze",
    "sleazy",
    "slope",
    "slut bucket",
    "slutdumper",
    "slutkiss",
    "sluts",
    "smutty",
    "sniper",
    "snuff",
    "sodom",
    "son-of-a-bitch",
    "souse",
    "soused",
    "spac",
    "sperm",
    "spick",
    "spik",
    "spiks",
    "steamy",
    "stfu",
    "stiffy",
    "stoned",
    "strip",
    "stroke",
    "stupid",
    "sucked",
    "sucking",
    "sumofabiatch",
    "t1t",
    "t1tt1e5",
    "t1tties",
    "tampon",
    "tard",
    "tawdry",
    "teabagging",
    "teat",
    "teets",
    "teez",
    "terd",
    "teste",
    "testee",
    "testes",
    "testical",
    "testicle",
    "testis",
    "thrust",
    "thug",
    "tinkle",
    "tit wank",
    "titfuck",
    "titi",
    "titt",
    "tittie5",
    "tittiefucker",
    "tittyfuck",
    "tittyfucker",
    "tittywank",
    "titwank",
    "toke",
    "toots",
    "tramp",
    "transsexual",
    "trashy",
    "tush",
    "tw4t",
    "twathead",
    "twats",
    "twatty",
    "twunt",
    "twunter",
    "ugly",
    "undies",
    "unwed",
    "urinal",
    "urine",
    "uterus",
    "uzi",
    "v14gra",
    "v1gra",
    "vag",
    "valium",
    "viagra",
    "virgin",
    "vixen",
    "vodka",
    "vomit",
    "vulgar",
    "w00se",
    "wad",
    "wang",
    "wanker",
    "wanky",
    "wazoo",
    "wedgie",
    "weed",
    "weenie",
    "weewee",
    "weiner",
    "weirdo",
    "wench",
    "wh0re",
    "wh0reface",
    "whitey",
    "whiz",
    "whoar",
    "whoralicious",
    "whorealicious",
    "whored",
    "whoreface",
    "whorehopper",
    "whorehouse",
    "whores",
    "whoring",
    "wigger",
    "willies",
    "willy",
    "womb",
    "woody",
    "wop",
    "x-rated",
    "xrated",
    "yeasty",
    "yobbo",
    "zoophile",
    "asshole*",
    "beastial*",
    "bestial*",
    "bitch*",
    "buttmunch",
    "cockmunch*",
    "cocksuck*",
    "cuntlick*",
    "donkeypunch*",
    "ejaculat*",
    "felch*",
    "fleshflute",
    "*fuck*",
    "gangbang*",
    "hardcoresex",
    "jack-off",
    "jerk-off",
    "niggers",
    "pricks",
    "pussys",
    "shitter*",
    "shitting*",
    "skank*",
    "twunt*",
    "wank*",
    "*whore*",
    "cocksuck",
    "cocksucked",
    "cocksucks",
    "cyberfucked",
    "cyberfucking",
    "ejaculates",
    "ejaculating",
    "fingerfuck",
    "fingerfucked",
    "fingerfucking",
    "fingerfucks",
    "fistfucked",
    "fistfuckers",
    "fistfucking",
    "fistfuckings",
    "fistfucks",
    "fuckme",
    "gangbanged",
    "gangbangs",
    "jiz",
    "jizm",
    "mothafucked",
    "mothafucking",
    "pissin",
    "shitters",
    "shitty"
}

# ---------- Загрузка/сохранение ----------
def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "packs": set(data.get("packs", [])),
                "stickers": set(data.get("stickers", [])),
                "gifs": set(data.get("gifs", [])),
            }
    return {"packs": set(), "stickers": set(), "gifs": set()}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "packs": list(blacklist["packs"]),
                "stickers": list(blacklist["stickers"]),
                "gifs": list(blacklist["gifs"]),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

def load_title_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_title_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

blocked = load_blacklist()
title_cache = load_title_cache()


# ---------- Вспомогательная проверка ----------
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def contains_nsfw(text: str) -> bool:
    if not text:
        return False
    lower_text = text.lower()
    return any(word in lower_text for word in BAD_KEYWORDS)


# ---------- Команды (только для владельца) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(
        "🛡️ Бот блокирует стикеры:\n"
        "• По имени пака (из ссылки)\n"
        "• По названию пака (видимому имени)\n"
        "• По ID (ручная блокировка)\n\n"
        "Используйте /list — управление чёрным списком."
    )

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    if not blocked["packs"] and not blocked["stickers"] and not blocked["gifs"]:
        await update.message.reply_text("🗑️ Чёрный список пуст.")
        return

    keyboard = []

    for pack in sorted(blocked["packs"]):
        title = title_cache.get(pack, "—")
        keyboard.append([InlineKeyboardButton(f"📦 {pack}\n«{title[:20]}»", callback_data=f"del_pack_{pack}")])

    for fid in sorted(blocked["stickers"])[:5]:
        keyboard.append([InlineKeyboardButton(f"🖼️ Стикер {fid[:8]}...", callback_data=f"del_sticker_{fid}")])
    for fid in sorted(blocked["gifs"])[:5]:
        keyboard.append([InlineKeyboardButton(f"🎬 GIF {fid[:8]}...", callback_data=f"del_gif_{fid}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите элемент для удаления:", reply_markup=reply_markup)


#Удаление 
async def handle_delete_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("del_pack_"):
        pack_name = data[9:]
        title = title_cache.get(pack_name, pack_name)
        await query.message.reply_text(
            f"❓ Удалить пак?\nИмя: `{pack_name}`\nНазвание: «{title}»",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_pack_{pack_name}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_sticker_"):
        fid = data[12:]
        await query.message.reply_text(
            f"❓ Удалить стикер?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_sticker_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_gif_"):
        fid = data[8:]
        await query.message.reply_text(
            f"❓ Удалить GIF?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_gif_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

async def confirm_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_pack_"):
        pack_name = data[17:]
        if pack_name in blocked["packs"]:
            blocked["packs"].remove(pack_name)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Пак `{pack_name}` удалён из чёрного списка.")
        else:
            await query.edit_message_text("❌ Пак уже удалён.")

    elif data.startswith("confirm_del_sticker_"):
        fid = data[20:]
        if fid in blocked["stickers"]:
            blocked["stickers"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Стикер `{fid}` удалён.")
        else:
            await query.edit_message_text("❌ Стикер уже удалён.")

    elif data.startswith("confirm_del_gif_"):
        fid = data[16:]
        if fid in blocked["gifs"]:
            blocked["gifs"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ GIF `{fid}` удалена.")
        else:
            await query.edit_message_text("❌ GIF уже удалена.")

    elif data == "cancel":
        await query.edit_message_text("❌ Удаление отменено.")

async def handle_delete_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("del_pack_"):
        pack_name = data[9:]
        title = title_cache.get(pack_name, pack_name)
        await query.message.reply_text(
            f"❓ Удалить пак?\nИмя: `{pack_name}`\nНазвание: «{title}»",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_pack_{pack_name}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_sticker_"):
        fid = data[12:]
        await query.message.reply_text(
            f"❓ Удалить стикер?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_sticker_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

    elif data.startswith("del_gif_"):
        fid = data[8:]
        await query.message.reply_text(
            f"❓ Удалить GIF?\nID: `{fid}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_del_gif_{fid}")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")]
            ])
        )

async def confirm_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_pack_"):
        pack_name = data[17:]
        if pack_name in blocked["packs"]:
            blocked["packs"].remove(pack_name)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Пак `{pack_name}` удалён из чёрного списка.")
        else:
            await query.edit_message_text("❌ Пак уже удалён.")

    elif data.startswith("confirm_del_sticker_"):
        fid = data[20:]
        if fid in blocked["stickers"]:
            blocked["stickers"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ Стикер `{fid}` удалён.")
        else:
            await query.edit_message_text("❌ Стикер уже удалён.")

    elif data.startswith("confirm_del_gif_"):
        fid = data[16:]
        if fid in blocked["gifs"]:
            blocked["gifs"].remove(fid)
            save_blacklist(blocked)
            await query.edit_message_text(f"✅ GIF `{fid}` удалена.")
        else:
            await query.edit_message_text("❌ GIF уже удалена.")

    elif data == "cancel":
        await query.edit_message_text("❌ Удаление отменено.")

# ---------- Добавление медиа (только от владельца) ----------
async def add_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    if not is_owner(user_id) or chat_type != "private":
        return

    if update.message.sticker:
        pack_name = update.message.sticker.set_name
        if not pack_name:
            await update.message.reply_text("❌ Стикер вне пака.")
            return
        blocked["packs"].add(pack_name)
        save_blacklist(blocked)

        # Также обновим кэш заголовка
        try:
            sticker_set = await context.bot.get_sticker_set(pack_name)
            title_cache[pack_name] = sticker_set.title
            save_title_cache(title_cache)
        except:
            pass

        await update.message.reply_text(f"✅ Пак `{pack_name}` добавлен.")
        return

    # GIF — как раньше
    fid = None
    if update.message.document and update.message.document.mime_type == "image/gif":
        fid = update.message.document.file_unique_id
    elif update.message.animation:
        fid = update.message.animation.file_unique_id
    if fid:
        blocked["gifs"].add(fid)
        save_blacklist(blocked)
        await update.message.reply_text("✅ GIF добавлена.")


# ---------- Модерация в группах ----------

async def moderate_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Проверка стикера
    if update.message.sticker:
        pack_name = update.message.sticker.set_name

        # 🔹 1. Быстрая проверка по set_name
        if pack_name and contains_nsfw(pack_name):
            await delete_and_mute(update, context, user_id, chat_id, "стикер (имя пака)")
            return

        # 🔹 2. Проверка по заголовку (с кэшированием)
        if pack_name:
            if pack_name not in title_cache:
                try:
                    sticker_set = await context.bot.get_sticker_set(pack_name)
                    title_cache[pack_name] = sticker_set.title
                    save_title_cache(title_cache)
                except Exception as e:
                    title_cache[pack_name] = ""
                    logging.warning(f"Не удалось загрузить пак {pack_name}: {e}")

            title = title_cache.get(pack_name, "")
            if contains_nsfw(title):
                await delete_and_mute(update, context, user_id, chat_id, "стикер (название пака)")
                return

        # 🔹 3. Ручная блокировка пака
        if pack_name and pack_name in blocked["packs"]:
            await delete_and_mute(update, context, user_id, chat_id, "заблокированный стикерпак")
            return

        # 🔹 4. По ID
        fid = update.message.sticker.file_unique_id
        if fid in blocked["stickers"]:
            await delete_and_mute(update, context, user_id, chat_id, "заблокированный стикер")
            return

    # Проверка GIF
    fid = None
    if update.message.document and update.message.document.mime_type == "image/gif":
        fid = update.message.document.file_unique_id
    elif update.message.animation:
        fid = update.message.animation.file_unique_id

    if fid and fid in blocked["gifs"]:
        await delete_and_mute(update, context, user_id, chat_id, "заблокированная GIF")
        return


# ---------- Вспомогательная функция: удалить + замутить ----------
MUTE_DURATION = 3600  # 1 час в секундах (измените по желанию)

async def delete_and_mute(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int, reason: str):
    # Удаляем сообщение
    try:
        await update.message.delete()
    except:
        pass

    # Проверяем, не админ ли пользователь
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            logging.info(f"Попытка замутить админа {user_id} — отмена.")
            return
    except:
        pass  # если не удалось проверить — всё равно мутим

    # Мутим пользователя
    try:
        until = update.message.date + timedelta(seconds=MUTE_DURATION)
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions={
                "can_send_messages": False,
                "can_send_audios": False,
                "can_send_documents": False,
                "can_send_photos": False,
                "can_send_videos": False,
                "can_send_video_notes": False,
                "can_send_voice_notes": False,
                "can_send_polls": False,
                "can_send_other_messages": False,  # стикеры, эмодзи и т.д.
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
            },
            until_date=until,
        )
        logging.info(f"Пользователь {user_id} замучен на {MUTE_DURATION} сек за {reason}.")
    except Exception as e:
        logging.warning(f"Не удалось замутить {user_id}: {e}")

# ---------- Основная функция ----------
async def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CallbackQueryHandler(handle_delete_request, pattern=r"^del_"))
    app.add_handler(CallbackQueryHandler(confirm_deletion, pattern=r"^confirm_del_|^cancel"))
    app.add_handler(MessageHandler(
        (filters.Sticker.ALL | filters.Document.GIF | filters.ANIMATION) & filters.ChatType.PRIVATE,
        add_media
    ))
    app.add_handler(MessageHandler(
        (filters.Sticker.ALL | filters.Document.GIF | filters.ANIMATION) & ~filters.ChatType.PRIVATE,
        moderate_media
    ))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logging.info(f"✅ Бот запущен! Владелец: {OWNER_ID}")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
