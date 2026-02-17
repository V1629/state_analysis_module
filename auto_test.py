"""
Automated Test Script for test_orchestrator.py
Feeds 75 messages automatically via pexpect, simulating a real human conversation.

The emotional arc grows LINEARLY over time:
  Phase 1 (1-10):   Neutral / casual — just vibing
  Phase 2 (11-20):  Mild stress creeping in — work pressure
  Phase 3 (21-30):  Growing stress + self-doubt
  Phase 4 (31-42):  Emotional low — sadness, isolation
  Phase 5 (43-52):  Turning point — small rays of hope
  Phase 6 (53-63):  Gradual improvement — building momentum
  Phase 7 (64-75):  Feeling strong — gratitude, confidence

Messages are in Hinglish (Hindi + English mix) for natural feel.

Usage:
    python auto_test.py
"""

import pexpect
import sys
import time

# ==========================================================
# 75 DIVERSE TEST MESSAGES
# ==========================================================

MESSAGES = [
    # =================================================================
    # PHASE 1: Neutral / Casual Start — just vibing (1-10)
    # The user is new, casual, nothing deep yet.
    # =================================================================
    "Hey, kya haal hai?",
    "Bas yaar, timepass chal raha hai. Kuch khaas nahi",
    "Aaj thoda boring day hai office mein",
    "Lunch mein maggi khayi, college ke din yaad aa gaye",
    "Weekend ka koi plan nahi hai abhi tak",
    "Kal raat Netflix pe ek movie dekhi, decent thi",
    "Aaj chai peete peete socha tujhse baat karta hoon",
    "Mausam acha hai aaj, thodi thand hai lekin accha lag raha hai",
    "Abhi kuch nahi kar raha, just scrolling through Instagram",
    "Yaar subah se koi productive kaam nahi kiya, feeling lazy",

    # =================================================================
    # PHASE 2: Slight worry / mild stress creeping in (11-20)
    # Small stressors appear — work pressure, deadlines, nothing extreme.
    # =================================================================
    "Office mein thoda kaam badh gaya hai is week",
    "Boss ne ek naya project assign kar diya, deadline tight hai",
    "Yaar sleep schedule bigad gaya hai, raat ko 2 baje soya kal",
    "Thoda sa pressure feel ho raha hai but manageable hai",
    "Ek meeting mein kuch samajh nahi aaya, awkward laga",
    "Subah jaldi uthna padta hai but body cooperate nahi karti",
    "Chai ke bina toh din shuru hi nahi hota yaar",
    "Kaam itna hai ki gym jaana band ho gaya temporarily",
    "Kabhi kabhi lagta hai time hi nahi milta apne liye",
    "Aaj colleague ne bola ki mera kaam slow hai, thoda bura laga",

    # =================================================================
    # PHASE 3: Growing stress + self-doubt (21-30)
    # Stress compounds. Doubt starts. Sleep issues. Social withdrawal.
    # =================================================================
    "Yaar last 2 weeks se continuously kaam kar raha hoon, thak gaya",
    "Kal raat properly nahi soya, mind mein thoughts chalte rehte hain",
    "Dost log plan bana rahe the weekend ka but mera mann nahi tha",
    "Kabhi kabhi lagta hai main sab se peeche reh gaya hoon",
    "Instagram pe sabko dekhta hoon, sab settle ho rahe hain, mujhe anxiety hoti hai",
    "Ghar pe bhi koi samajhta nahi ki kitna pressure hai kaam ka",
    "Two months ago I thought things would get better but nothing changed",
    "Yaar concentration bilkul nahi ho rahi, ek simple task mein ghante lag rahe",
    "Pata nahi kya ho raha hai, mood swings aa rahe hain",
    "Raat ko sone se pehle bahut overthink karta hoon these days",

    # =================================================================
    # PHASE 4: Emotional low — sadness, isolation, frustration (31-42)
    # The user opens up more. Real vulnerability. Things feel heavy.
    # =================================================================
    "Honestly yaar, bahut tired feel ho raha hai, physically bhi aur mentally bhi",
    "Kisi se baat karne ka mann nahi karta, bus akela rehna hai",
    "Last week ek purane friend se baat hui, usne bhi time nahi diya, hurt hua",
    "Mujhe lagta hai logo ko meri care nahi hai, I'm just there for convenience",
    "Three years ago I lost my dadi and sometimes I still miss her so much",
    "Ghar se door rehna mushkil hai, especially jab mood low ho",
    "Kal raat bahut roya, pata nahi kyun, bas emotions aa gaye",
    "Sometimes I feel like I'm stuck in a loop, same day repeat ho raha hai",
    "Mujhe dar lagta hai ki main kabhi successful nahi hounga",
    "I keep comparing myself to others and it just makes everything worse",
    "Yaar bahut lonely feel hota hai kabhi kabhi, even in a room full of people",
    "Kisi ko batata hoon toh bolte hain sab theek ho jayega, but it doesn't help",

    # =================================================================
    # PHASE 5: Turning point — small rays of hope (43-52)
    # User starts reflecting. Small positive moments. Not fully better, but shifting.
    # =================================================================
    "Aaj subah walk pe gaya after a long time, thoda accha laga",
    "Ek purani playlist suni, college ke gaane, mood thoda lift hua",
    "Mummy ka call aaya tha, unse baat karke accha laga",
    "Socha ki ek diary likhna shuru karunga, thoughts clear hone chahiye",
    "Aaj office mein ek chhoti si cheez complete ki aur surprisingly accha feel hua",
    "Last summer jab ghar gaya tha, woh trip yaad aa rahi hai, best time tha",
    "Yaar shayad mujhe kisi professional se baat karni chahiye about my mental health",
    "Aaj gym gaya 3 weeks baad, body dard ho rahi hai but mentally better feel hua",
    "I realized ki comparison band karna padega, apni pace se chalna hoga",
    "Ek naya book start ki hai, raat ko phone ki jagah book padh raha hoon",

    # =================================================================
    # PHASE 6: Gradual improvement — building momentum (53-63)
    # User is actively working on themselves. More positive messages. Growth visible.
    # =================================================================
    "Aaj 2 din se consistently subah 7 baje uth raha hoon, feels good",
    "Office mein ek task time se complete kiya, boss ne appreciate kiya",
    "Yaar meditation try ki, sirf 10 minutes but bahut calm feel hua",
    "Dosto ke saath weekend pe chai pe mila, bahut maza aaya after so long",
    "I've started saying no to things that drain me, it's liberating honestly",
    "Kal raat 11 baje soya and 7 baje utha, first time in months",
    "Mujhe lagta hai main slowly apni life ko figure out kar raha hoon",
    "Aaj ek junior ko kuch sikhaaya office mein, accha laga helping someone",
    "Next month mein ek short trip plan kar raha hoon mountains pe, excited hoon",
    "Pehle jaise overthink nahi hota ab, I think journaling is actually working",
    "I'm learning to be patient with myself, sab ek din mein nahi hota",

    # =================================================================
    # PHASE 7: Feeling strong — confidence, gratitude, peace (64-75)
    # User is in a much better place. Reflective, grateful, forward-looking.
    # =================================================================
    "Yaar aaj realize hua ki 2 months pehle kitna low tha, ab bahut better hoon",
    "Family se video call kiya, sab khush the, mujhe bhi accha laga",
    "Office mein ek naya project lead kar raha hoon, confidence aa raha hai",
    "I feel grateful ki mere paas log hain jo care karte hain, even if few",
    "Aaj gym mein personal best mara, 6 weeks of consistency ka result hai",
    "Main apne aap se proud hoon ki mushkil time mein give up nahi kiya",
    "A year ago I was in such a dark place, and look at me now, still standing",
    "Zindagi mein ups and downs toh aayenge, but ab handle karna aa gaya hai",
    "Yaar thank you for being there, baat karke bahut halka feel hota hai",
    "Next year ke liye bahut saare plans hain, excited hoon future ke liye",
    "I've learned ki mental health pe dhyan dena zaroori hai, no shame in it",
    "Aaj ka din bahut accha raha, grateful hoon har chhoti cheez ke liye",
]


# ==========================================================
# MAIN - AUTOMATED CHAT
# ==========================================================

def main():
    print("=" * 80)
    print("🤖 AUTOMATED TEST - Feeding 75 Hinglish messages (linear emotional arc)")
    print("=" * 80)

    # Spawn the test_orchestrator.py process using the venv python
    cwd = "/home/vaibhav-mishra/projects/Time_extraction/files"
    python_bin = f"{cwd}/venv/bin/python3"
    child = pexpect.spawn(
        f"{python_bin} test_orchestrator.py",
        cwd=cwd,
        encoding="utf-8",
        timeout=120,
    )

    # Mirror all output to our terminal in real time
    child.logfile_read = sys.stdout

    # Wait for the initial setup to complete and the prompt to appear
    print("\n⏳ Waiting for orchestrator to initialize...\n")
    child.expect("💬 You:", timeout=60)

    # Send each message
    for i, msg in enumerate(MESSAGES, 1):
        print(f"\n\n{'#'*80}")
        print(f"  >>> AUTO-SENDING MESSAGE {i}/{len(MESSAGES)}: {msg}")
        print(f"{'#'*80}\n")

        child.sendline(msg)
        time.sleep(0.3)  # small delay to mimic typing

        # Wait for the next prompt (or end of output)
        try:
            child.expect("💬 You:", timeout=90)
        except pexpect.TIMEOUT:
            print(f"\n⚠️  Timeout waiting for prompt after message {i}. Continuing...")
            continue
        except pexpect.EOF:
            print(f"\n⚠️  Process ended after message {i}.")
            break

    # Send 'exit' to cleanly close
    print(f"\n\n{'#'*80}")
    print("  >>> SENDING: exit")
    print(f"{'#'*80}\n")
    child.sendline("exit")

    # Wait for process to finish
    try:
        child.expect(pexpect.EOF, timeout=30)
    except pexpect.TIMEOUT:
        print("⚠️  Process didn't exit cleanly, forcing close.")
        child.close(force=True)

    print("\n" + "=" * 80)
    print(f"✅ AUTOMATED TEST COMPLETE - Sent {len(MESSAGES)} messages")
    print("=" * 80)


if __name__ == "__main__":
    main()
