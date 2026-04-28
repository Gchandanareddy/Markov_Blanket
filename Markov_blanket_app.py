import streamlit as st
import re

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DAG & Markov Blanket Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #212121; color: #ececec; }
header[data-testid="stHeader"] { background: transparent; }
div[data-testid="stSidebar"] { background: #171717 !important; }
div[data-testid="stSidebar"] * { color: #ececec !important; }

.chat-container { max-width: 800px; margin: 0 auto; padding: 0 1rem 140px 1rem; }

.msg-user { display:flex; justify-content:flex-end; margin:14px 0; gap:10px; align-items:flex-start; }
.msg-user .bubble {
    background: #2f2f2f; color: #ececec;
    padding: 12px 16px; border-radius: 18px 18px 4px 18px;
    max-width: 75%; font-size: 0.95rem; line-height: 1.6; white-space: pre-wrap;
}
.msg-user .av {
    width:34px; height:34px; border-radius:50%; background:#19c37d;
    display:flex; align-items:center; justify-content:center;
    font-size:0.75rem; font-weight:700; color:white; flex-shrink:0; margin-top:2px;
}
.msg-ai { display:flex; justify-content:flex-start; margin:14px 0; gap:10px; align-items:flex-start; }
.msg-ai .bubble {
    background: #2a2a2a; color: #ececec;
    padding: 14px 18px; border-radius: 18px 18px 18px 4px;
    max-width: 88%; font-size: 0.95rem; line-height: 1.7; white-space: pre-wrap;
    border: 1px solid #3a3a3a;
}
.msg-ai .av {
    width:34px; height:34px; border-radius:50%;
    background:linear-gradient(135deg,#ab68ff,#7c3aed);
    display:flex; align-items:center; justify-content:center;
    font-size:1rem; flex-shrink:0; margin-top:2px;
}

.bubble .formula {
    background:#1a1a1a; border-radius:8px; padding:10px 14px; margin:8px 0;
    font-family:'Courier New',monospace; font-size:0.88rem; color:#93c5fd;
    line-height:1.8; display:block; border-left:3px solid #7c3aed;
}
.bubble strong { color:#ffffff; }
.bubble em { color:#c4b5fd; }

/* DAG SVG box */
.dag-wrap {
    background:#1a1a1a; border-radius:12px; padding:16px;
    margin:10px 0; border:1px solid #333; text-align:center;
}

.progress-bar-wrap { position:fixed; top:0; left:0; right:0; height:3px; z-index:9999; background:#333; }
.progress-bar-fill { height:100%; background:linear-gradient(90deg,#7c3aed,#19c37d); transition:width 0.5s; }

.top-bar {
    position:sticky; top:0; background:#212121;
    border-bottom:1px solid #333; padding:10px 0 8px; margin-bottom:6px; z-index:100;
}
.top-bar h2 { text-align:center; font-size:0.95rem; font-weight:500; color:#aaa; margin:0; }

.stButton > button {
    background:#2a2a2a !important; color:#ececec !important;
    border:1px solid #444 !important; border-radius:20px !important;
    font-size:0.85rem !important; padding:6px 14px !important;
    font-family:'Inter',sans-serif !important; transition:all 0.15s !important;
}
.stButton > button:hover { background:#3a3a3a !important; border-color:#7c3aed !important; }

div[data-testid="stChatMessage"] { background:transparent !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# DAG DEFINITION
# Graph from image:
#   W → Y, W → Z
#   X → Y, X → Z  (X→Z inferred from image diagonal)
#   Y → Z, Y → T
#   Z → T
# Nodes: W, X, Y, Z, T
# ═══════════════════════════════════════════════════════════════
# Adjacency (parent → child)
EDGES = [
    ("W", "Y"), ("W", "Z"),
    ("X", "Y"), ("X", "Z"),
    ("Y", "Z"), ("Y", "T"),
    ("Z", "T"),
]

def parents(node):
    return sorted([p for p, c in EDGES if c == node])

def children(node):
    return sorted([c for p, c in EDGES if p == node])

def spouses(node):
    """Co-parents: nodes that share a child with `node` but are not parent/child of it."""
    sp = set()
    for child in children(node):
        for p in parents(child):
            if p != node:
                sp.add(p)
    return sorted(sp)

def markov_blanket(node):
    p = parents(node)
    c = children(node)
    sp = spouses(node)
    mb = sorted(set(p + c + sp))
    return mb

# Pre-compute answers
MB_Y  = markov_blanket("Y")   # parents(Y)+children(Y)+coparents(Y)
MB_W  = markov_blanket("W")   # parents(W)+children(W)+coparents(W)
PAR_Z = parents("Z")          # parents in MB of Z

# SVG DAG
DAG_SVG = """
<div class="dag-wrap">
<svg viewBox="0 0 520 300" xmlns="http://www.w3.org/2000/svg" style="max-width:480px;width:100%;">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#7c3aed"/>
    </marker>
  </defs>

  <!-- Edges -->
  <!-- W→Y --> <line x1="175" y1="65"  x2="235" y2="138" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>
  <!-- W→Z --> <line x1="205" y1="60"  x2="340" y2="138" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>
  <!-- X→Y --> <line x1="85"  y1="160" x2="198" y2="160" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>
  <!-- X→Z --> <line x1="105" y1="148" x2="320" y2="145" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>
  <!-- Y→Z --> <line x1="272" y1="160" x2="318" y2="160" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>
  <!-- Y→T --> <line x1="248" y1="178" x2="248" y2="238" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>
  <!-- Z→T --> <line x1="345" y1="178" x2="278" y2="238" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr)"/>

  <!-- Nodes -->
  <ellipse cx="190" cy="55"  rx="30" ry="20" fill="#f5e6c8" stroke="#c49a3c" stroke-width="2"/>
  <text x="190" y="61" text-anchor="middle" font-size="16" font-weight="bold" fill="#5a3e00">W</text>

  <ellipse cx="65"  cy="160" rx="30" ry="20" fill="#f5e6c8" stroke="#c49a3c" stroke-width="2"/>
  <text x="65"  y="166" text-anchor="middle" font-size="16" font-weight="bold" fill="#5a3e00">X</text>

  <ellipse cx="248" cy="160" rx="30" ry="20" fill="#f5e6c8" stroke="#c49a3c" stroke-width="2"/>
  <text x="248" y="166" text-anchor="middle" font-size="16" font-weight="bold" fill="#5a3e00">Y</text>

  <ellipse cx="355" cy="160" rx="30" ry="20" fill="#f5e6c8" stroke="#c49a3c" stroke-width="2"/>
  <text x="355" y="166" text-anchor="middle" font-size="16" font-weight="bold" fill="#5a3e00">Z</text>

  <ellipse cx="255" cy="260" rx="30" ry="20" fill="#f5e6c8" stroke="#c49a3c" stroke-width="2"/>
  <text x="255" y="266" text-anchor="middle" font-size="16" font-weight="bold" fill="#5a3e00">T</text>
</svg>
<p style="color:#666;font-size:0.78rem;margin:4px 0 0 0;">Graph: W→Y, W→Z, X→Y, X→Z, Y→Z, Y→T, Z→T</p>
</div>
"""

# ═══════════════════════════════════════════════════════════════
# TUTOR MESSAGES
# ═══════════════════════════════════════════════════════════════
WELCOME = f"""👋 Welcome! I'm your **DAG & Markov Blanket Tutor**.

We'll work through this graph step by step — I'll teach the concept, then ask you the question, just like a 1-on-1 tutor!

{DAG_SVG}

**Edges in this graph:**
<span class='formula'>W → Y    W → Z
X → Y    X → Z
Y → Z    Y → T
Z → T</span>

We have **5 questions** about Markov Blankets, confounding, and causal effects.

Ready? Type **"yes"** or click below! 👇"""

TEACH = {
    "q1": f"""Let's tackle **Question 1 — Markov Blanket of Y**.

📖 **What is a Markov Blanket?**
The Markov Blanket of a node makes it *conditionally independent* of all other nodes in the graph. It contains exactly **3 types of nodes**:

<span class='formula'>Markov Blanket(Node) = Parents(Node)
                     + Children(Node)
                     + Co-parents of Children (Spouses)</span>

💡 **Let's find each group for Y:**

<span class='formula'>Parents of Y   → nodes with arrows INTO Y
               → W → Y  and  X → Y
               → Parents = {{W, X}}

Children of Y  → nodes with arrows OUT OF Y
               → Y → Z  and  Y → T
               → Children = {{Z, T}}

Co-parents     → other parents of Y's children
  (Spouses)      Children of Y = Z and T
               → Other parents of Z: W, X (besides Y)
               → Other parents of T: Z (besides Y)
               → Spouses = {{W, X, Z}}</span>

Now combine all three groups (remove duplicates):
MB(Y) = Parents ∪ Children ∪ Spouses

What is the **Markov Blanket of Y**? List all nodes 👇""",

    "q2": f"""Great! Now **Question 2 — Markov Blanket of W**.

Let's apply the same formula to **W** this time:

<span class='formula'>Markov Blanket(W) = Parents(W)
                  + Children(W)
                  + Co-parents of W's children</span>

💡 **Work through each group:**

<span class='formula'>Parents of W   → Any arrows pointing INTO W?
               → Look at the graph... none!
               → Parents = {{}} (empty)

Children of W  → Arrows going OUT of W:
               → W → Y  and  W → Z
               → Children = {{Y, Z}}

Co-parents     → Other parents of W's children:
  (Spouses)      W's children = Y and Z
               → Other parents of Y: X (besides W)
               → Other parents of Z: X, Y (besides W)
               → Spouses = {{X, Y}}</span>

Combine: MB(W) = ∅ ∪ {{Y, Z}} ∪ {{X, Y}}

What is the **Markov Blanket of W**? 👇""",

    "q3": f"""Excellent! **Question 3 — Parents in the Markov Blanket of Z**.

This is a subset question — we want only the **parents** (not all MB members) of Z.

<span class='formula'>Parents of Z = nodes with arrows directly INTO Z

From the graph:
  W → Z  ✅
  X → Z  ✅
  Y → Z  ✅

So Parents(Z) = {{W, X, Y}}</span>

📌 Note: The full Markov Blanket of Z also includes:
- Children of Z = {{T}}
- Co-parents of T (besides Z) = {{Y}}

But Q3 only asks for the **parents** specifically.

What are the **parents in the Markov Blanket of Z**? 👇""",

    "q4": f"""Now **Question 4 — Regression & Statistical Significance**.

🎯 *If we regress Z on X, W, Y (not T), which variables will be statistically significant?*

💡 **Key principle:**
When you regress a variable on its **Markov Blanket members**, only the **direct parents** will be statistically significant (because they have direct causal arrows into Z).

<span class='formula'>We are regressing Z on: X, W, Y, (NOT T)

Direct parents of Z = W, X, Y
  → These have direct causal arrows into Z
  → They WILL be statistically significant ✅

T is a CHILD of Z (Z → T)
  → Not included in the regression anyway
  → Children are NOT parents, so they wouldn't
    explain variance in Z directly</span>

🔑 **The rule:**
In a regression of a node on its Markov Blanket, only **parents** are statistically significant. Co-parents (spouses) and children become insignificant once parents are controlled for.

Which variables will be **statistically significant** in this regression? 👇""",

    "q5": f"""Last question! **Question 5 — Un-confounded Effect of Y on T**.

🎯 *Which arcs should be stratified (removed) to measure the un-confounded effect of Y → T?*

💡 **What is confounding here?**
We want to isolate the direct effect: **Y → T**

The confounding paths are all *backdoor paths* from Y to T that go through other variables:

<span class='formula'>Backdoor paths from Y to T:

Path 1: Y ← W → Z → T
  (goes backwards through W, then forward to T via Z)

Path 2: Y ← X → Z → T
  (goes backwards through X, then forward to T via Z)

Path 3: Y → Z → T
  (this is a FRONT-DOOR / mediator path — Y causes Z
   which causes T. This is a DIRECT causal path, not
   a backdoor path to block!)</span>

🚪 **To block backdoor paths, we stratify on (condition on) the confounders:**

<span class='formula'>To close Path 1: Y ← W → Z → T
  → Stratify/condition on W  (block at W)
  → OR condition on Z

To close Path 2: Y ← X → Z → T
  → Stratify/condition on X  (block at X)
  → OR condition on Z

Minimum adjustment set = {{W, X}}
  → Conditioning on W and X blocks ALL backdoor paths</span>

⚠️ **Important:** We should NOT condition on Z when measuring Y→T, because Z is also a *mediator* on the path Y→Z→T. Conditioning on a mediator blocks the indirect causal effect!

Which **arcs should be stratified** to measure the un-confounded effect of Y on T? 👇""",
}

# ═══════════════════════════════════════════════════════════════
# GRADERS
# ═══════════════════════════════════════════════════════════════
def normalize(s):
    return set(re.findall(r'[A-Z]', s.upper()))

def grade_q1(ans):
    correct = {"W", "X", "Z", "T"}
    got = normalize(ans)
    if correct == got:
        return "correct"
    if len(correct & got) >= 3:
        return "partial"
    return "incorrect"

def grade_q2(ans):
    correct = {"X", "Y", "Z"}
    got = normalize(ans)
    if correct == got:
        return "correct"
    if len(correct & got) >= 2:
        return "partial"
    return "incorrect"

def grade_q3(ans):
    correct = {"W", "X", "Y"}
    got = normalize(ans)
    if correct == got:
        return "correct"
    if len(correct & got) >= 2:
        return "partial"
    return "incorrect"

def grade_q4(ans):
    correct = {"W", "X", "Y"}
    got = normalize(ans)
    if correct == got:
        return "correct"
    if len(correct & got) >= 2:
        return "partial"
    return "incorrect"

def grade_q5(ans):
    s = ans.lower()
    got = normalize(ans)
    # Accept: W and X as adjustment set, or mention of backdoor/stratify W,X
    if {"W", "X"} <= got or {"W", "X", "Z"} <= got:
        if "z" not in s or "not z" in s or "avoid z" in s or "mediator" in s:
            return "correct"
        return "correct"  # accept W,X even if Z mentioned
    if "w" in s and "x" in s:
        return "correct"
    if "w" in s or "x" in s or "backdoor" in s or "confound" in s:
        return "partial"
    return "incorrect"

def get_feedback(q, grade, ans):
    got = normalize(ans)
    feedbacks = {
        "q1": {
            "correct":   f"✅ **Correct!** MB(Y) = {{W, X, Z, T}}\n\n• **Parents:** W, X (arrows into Y)\n• **Children:** Z, T (arrows out of Y)\n• **Spouses:** W, X, Z (co-parents of Z and T)\n• Combined (unique): **W, X, Z, T** ✓\n\nY is conditionally independent of every other node given these 4!",
            "partial":   f"⚠️ **Almost!** You got {got & {'W','X','Z','T'}} but the full answer is {{W, X, Z, T}}.\n\nRemember all 3 components:\n- Parents of Y = W, X\n- Children of Y = Z, T\n- Spouses (co-parents of Z, T) = W, X, Z\n→ Union = **W, X, Z, T**",
            "incorrect": f"❌ **Let me help!** MB(Y) = {{W, X, Z, T}}\n\n• Parents (→Y): W, X\n• Children (Y→): Z, T\n• Co-parents of Z: W, X | Co-parents of T: Z\n• All unique nodes: **W, X, Z, T**\n\nType **next** to continue! 👉",
        },
        "q2": {
            "correct":   f"✅ **Correct!** MB(W) = {{X, Y, Z}}\n\n• **Parents of W:** none (W has no incoming arrows)\n• **Children of W:** Y, Z\n• **Spouses:** X (co-parent of Y and Z with W)\n• Combined: **X, Y, Z** ✓\n\nNotice W has no parents — it's a root node!",
            "partial":   f"⚠️ **Almost!** You got {got & {'X','Y','Z'}} but the full answer is {{X, Y, Z}}.\n\n- W has NO parents\n- Children = Y, Z\n- Co-parents of Y & Z = X\n→ MB(W) = **X, Y, Z**",
            "incorrect": f"❌ **Answer:** MB(W) = {{X, Y, Z}}\n\n- Parents: none\n- Children: Y, Z (W→Y, W→Z)\n- Spouses: X (also a parent of Y and Z)\n→ **X, Y, Z**\n\nType **next** to continue! 👉",
        },
        "q3": {
            "correct":   f"✅ **Correct!** Parents of Z = {{W, X, Y}}\n\nAll three have direct arrows into Z:\n  W → Z ✓\n  X → Z ✓\n  Y → Z ✓\n\nThese are the direct causes of Z in the graph!",
            "partial":   f"⚠️ **Close!** You got {got & {'W','X','Y'}} but all three are correct: {{W, X, Y}}\n\nCheck all arrows pointing INTO Z:\n  W → Z, X → Z, Y → Z → Parents = **W, X, Y**",
            "incorrect": f"❌ **Answer:** Parents of Z = {{W, X, Y}}\n\nLook for arrows pointing directly INTO Z:\n  W → Z ✓  X → Z ✓  Y → Z ✓\n\nType **next** to continue! 👉",
        },
        "q4": {
            "correct":   f"✅ **Correct!** W, X, and Y will be statistically significant.\n\nThey are the **direct parents** of Z — they have causal arrows Z←W, Z←X, Z←Y.\n\nIn regression, direct parents explain variance in Z. Once parents are controlled, co-parents and children become redundant (insignificant).",
            "partial":   f"⚠️ **Almost!** All three parents (W, X, Y) should be significant.\n\nRule: In regression Z ~ X + W + Y, all **direct parents** of Z are significant.\n- W → Z ✅\n- X → Z ✅\n- Y → Z ✅\n→ All three: **W, X, Y**",
            "incorrect": f"❌ **Answer:** W, X, Y will all be statistically significant.\n\nThey are direct parents of Z (W→Z, X→Z, Y→Z).\nDirect parents have the strongest statistical relationship with the child node.\n\nType **next** to continue! 👉",
        },
        "q5": {
            "correct":   f"✅ **Correct!** To measure the un-confounded effect of Y→T, stratify on (condition on) **W and X**.\n\nThis blocks both backdoor paths:\n  Path 1: Y ← W → Z → T  (blocked by conditioning on W)\n  Path 2: Y ← X → Z → T  (blocked by conditioning on X)\n\n⚠️ Do NOT condition on Z — it's a mediator on Y→Z→T!\n\nMinimum adjustment set = **{{W, X}}** ✓",
            "partial":   f"⚠️ **Good thinking!** You identified part of the answer.\n\nThe complete adjustment set is **W and X** (both needed):\n- Block Y ← W → Z → T by conditioning on **W**\n- Block Y ← X → Z → T by conditioning on **X**\n\nAvoid conditioning on Z (it's a mediator)!",
            "incorrect": f"❌ **Answer:** Stratify on (condition on) **W and X**.\n\nBackdoor paths from Y to T:\n  Y ← W → Z → T → blocked by conditioning on W\n  Y ← X → Z → T → blocked by conditioning on X\n\nAdjustment set = {{W, X}}\n\nType **done** to see your final results! 🏁",
        },
    }
    return feedbacks[q][grade]

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
STAGE_ORDER = ["welcome","q1_ask","q2_ask","q3_ask","q4_ask","q5_ask","done"]
STAGE_LABELS = {
    "welcome": "Introduction — DAG Overview",
    "q1_ask":  "Q1 of 5 — Markov Blanket of Y",
    "q2_ask":  "Q2 of 5 — Markov Blanket of W",
    "q3_ask":  "Q3 of 5 — Parents in MB of Z",
    "q4_ask":  "Q4 of 5 — Regression Significance",
    "q5_ask":  "Q5 of 5 — Un-confounded Effect Y→T",
    "done":    "✅ Assignment Complete",
}

for k, v in {
    "messages": [],
    "stage": "welcome",
    "grades": {},
    "initialized": False,
    "awaiting_next": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def add_ai(t):   st.session_state.messages.append({"role":"ai",   "content":t})
def add_usr(t):  st.session_state.messages.append({"role":"user", "content":t})

if not st.session_state.initialized:
    add_ai(WELCOME)
    st.session_state.initialized = True

# ═══════════════════════════════════════════════════════════════
# INPUT HANDLER
# ═══════════════════════════════════════════════════════════════
NEXT_WORDS = {"next","yes","ok","sure","continue","ready","go","move","proceed","got it","understood"}

def handle(raw):
    txt = raw.strip()
    if not txt: return
    add_usr(txt)
    s   = st.session_state.stage
    low = txt.lower()

    # Restart
    if "restart" in low:
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    # Show DAG anytime
    if any(w in low for w in ["show graph","show dag","show diagram","graph","dag","diagram"]):
        add_ai(f"Here's the DAG again! 📊\n{DAG_SVG}")
        return

    # Welcome stage
    if s == "welcome":
        add_ai(TEACH["q1"])
        st.session_state.stage = "q1_ask"
        return

    # Hint handler
    if any(w in low for w in ["hint","help","how","explain","stuck","confused"]):
        hints = {
            "q1_ask": "💡 **Hint for Q1:**\n- Parents of Y (arrows →Y): W, X\n- Children of Y (arrows Y→): Z, T\n- Co-parents (spouses) of Y's children:\n  → Co-parents of Z: W, X\n  → Co-parents of T: Z\n- Union of all = **{W, X, Z, T}**",
            "q2_ask": "💡 **Hint for Q2:**\n- Parents of W: none! (W is a root node)\n- Children of W: Y, Z\n- Co-parents of Y & Z (besides W): X\n- MB(W) = **{X, Y, Z}**",
            "q3_ask": "💡 **Hint for Q3:**\n- Just find arrows pointing INTO Z\n- W→Z ✓, X→Z ✓, Y→Z ✓\n- Parents(Z) = **{W, X, Y}**",
            "q4_ask": "💡 **Hint for Q4:**\n- In regression Z~W+X+Y, the significant variables are Z's **direct parents**\n- Direct parents of Z = W, X, Y\n- Answer: **W, X, Y** are all significant",
            "q5_ask": "💡 **Hint for Q5:**\n- Find all backdoor paths from Y to T\n- Path 1: Y ← W → Z → T → condition on W\n- Path 2: Y ← X → Z → T → condition on X\n- Adjustment set = **{W, X}**\n- Do NOT condition on Z (it's a mediator!)",
        }
        if s in hints:
            add_ai(hints[s])
        return

    # Next navigation
    if any(w in low for w in NEXT_WORDS) or st.session_state.awaiting_next:
        if any(w in low for w in NEXT_WORDS):
            st.session_state.awaiting_next = False
            nxt = {
                "q1_ask": ("q2_ask", TEACH["q2"]),
                "q2_ask": ("q3_ask", TEACH["q3"]),
                "q3_ask": ("q4_ask", TEACH["q4"]),
                "q4_ask": ("q5_ask", TEACH["q5"]),
                "q5_ask": ("done",   None),
                "done":   ("done",   "Type **restart** to try again! 🔄"),
            }
            if s in nxt:
                new_stage, msg = nxt[s]
                if msg:
                    add_ai(msg)
                else:
                    # Build final results
                    g = st.session_state.grades
                    icons = {"correct":"✅","partial":"⚠️","incorrect":"❌","":"⬜"}
                    rows = [
                        ("Q1","MB of Y",         "{W, X, Z, T}",    g.get("q1","")),
                        ("Q2","MB of W",         "{X, Y, Z}",       g.get("q2","")),
                        ("Q3","Parents of Z",    "{W, X, Y}",       g.get("q3","")),
                        ("Q4","Regression sig.", "W, X, Y",         g.get("q4","")),
                        ("Q5","Adjust set Y→T",  "{W, X}",          g.get("q5","")),
                    ]
                    correct_n = sum(1 for _,_,_,gr in rows if gr=="correct")
                    partial_n = sum(1 for _,_,_,gr in rows if gr=="partial")
                    score_pct = int(((correct_n + 0.5*partial_n)/5)*100)
                    summary = "\n".join([f"{icons[gr]} {q} — {name}: {ans}" for q,name,ans,gr in rows])
                    add_ai(f"""🎓 **Assignment Complete! Here's your scorecard:**

{summary}

**Score: {correct_n}/5 correct — {score_pct}%**

{'🌟 Perfect score! You fully understand Markov Blankets and causal adjustment!' if score_pct == 100 else
 '🎉 Great work! Review the ⚠️/❌ questions above.' if score_pct >= 60 else
 '💪 Keep practising! Re-read the explanations and try again.'}

**Key Concepts Recap:**
1️⃣ **Markov Blanket** = Parents + Children + Co-parents (spouses)
2️⃣ **In regression**, only direct **parents** are statistically significant
3️⃣ **Backdoor adjustment** for Y→T: condition on {{W, X}} to block confounding paths
4️⃣ **Never** condition on a mediator (like Z on Y→Z→T path)

Type **restart** to try again! 🔄""")
                st.session_state.stage = new_stage
            return

    # Grade answers
    q_map = {
        "q1_ask": ("q1", grade_q1),
        "q2_ask": ("q2", grade_q2),
        "q3_ask": ("q3", grade_q3),
        "q4_ask": ("q4", grade_q4),
        "q5_ask": ("q5", grade_q5),
    }
    if s in q_map:
        qkey, grader = q_map[s]
        grade = grader(txt)
        st.session_state.grades[qkey] = grade
        fb = get_feedback(qkey, grade, txt)

        next_prompts = {
            "q1_ask": "Ready for Q2? Type **next** 👉",
            "q2_ask": "On to Q3! Type **next** 👉",
            "q3_ask": "Great — Q4 next! Type **next** 👉",
            "q4_ask": "Almost done — Q5! Type **next** 👉",
            "q5_ask": "That's all 5 questions! Type **done** to see your results 🏁",
        }
        if grade == "correct":
            add_ai(fb + "\n\n" + next_prompts.get(s, ""))
            st.session_state.awaiting_next = True
        elif grade == "partial":
            add_ai(fb + "\n\nWant to try again, or type **next** to move on?")
        else:
            add_ai(fb)
            st.session_state.awaiting_next = True

# ═══════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════
stage_list = STAGE_ORDER
idx = stage_list.index(st.session_state.stage) if st.session_state.stage in stage_list else 0
pct = int((idx / (len(stage_list)-1)) * 100)

st.markdown(f'<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct}%"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="top-bar"><h2>🎓 DAG & Markov Blanket Tutor &nbsp;·&nbsp; {STAGE_LABELS.get(st.session_state.stage,"")}</h2></div>', unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "ai":
        st.markdown(f'<div class="msg-ai"><div class="av">🎓</div><div class="bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-user"><div class="bubble">{msg["content"]}</div><div class="av">You</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Quick buttons
s = st.session_state.stage
cols = st.columns([1,1,1,3])
if s == "welcome":
    with cols[0]:
        if st.button("▶️ Let's begin!"):
            handle("yes"); st.rerun()
    with cols[1]:
        if st.button("📊 Show graph"):
            handle("show graph"); st.rerun()
elif s in ("q1_ask","q2_ask","q3_ask","q4_ask","q5_ask"):
    with cols[0]:
        if st.button("💡 Hint"):
            handle("hint"); st.rerun()
    with cols[1]:
        if st.button("📊 Show DAG"):
            handle("show graph"); st.rerun()
    with cols[2]:
        if st.button("⏭️ Next"):
            handle("next"); st.rerun()
elif s == "done":
    with cols[0]:
        if st.button("🔄 Restart"):
            handle("restart"); st.rerun()

user_input = st.chat_input("Type your answer or ask for a hint…")
if user_input:
    handle(user_input)
    st.rerun()
