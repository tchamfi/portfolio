"""
styles.py — All CSS for Ask Lionel portfolio
"""

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    .stApp{background:linear-gradient(180deg,#f8fafc,#eef2f7);font-family:'Inter',sans-serif;}
    #MainMenu,footer,header{visibility:hidden;} .stDeployButton{display:none;}
    .block-container{max-width:1200px;padding-top:.5rem;}
    section[data-testid="stSidebar"]{display:none;}
    h1,h2,h3,h4{font-family:'Inter',sans-serif!important;color:#1a1a2e!important;}
    p,li,span,label,div{font-family:'Inter',sans-serif!important;}

    /* FORCE all text dark by default */
    .stApp p, .stApp span, .stApp label, .stApp div{color:#334155;}
    .stApp strong, .stApp b{color:#1e293b;}

    .hero-section{text-align:center;padding:3rem 2rem 2rem;background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);border-radius:24px;margin-bottom:0;position:relative;overflow:hidden;}
    .hero-section::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 50%,rgba(99,102,241,.15) 0%,transparent 50%),radial-gradient(circle at 70% 50%,rgba(236,72,153,.1) 0%,transparent 50%);}
    .hero-name{font-size:3rem;font-weight:800;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.3rem;position:relative;letter-spacing:-.03em;}
    .hero-title{font-size:1.15rem;color:rgba(255,255,255,.85)!important;margin-bottom:.5rem;position:relative;}
    .hero-title *{color:rgba(255,255,255,.85)!important;}
    .hero-tagline{font-size:.9rem;color:rgba(255,255,255,.5)!important;margin-bottom:1.2rem;position:relative;max-width:640px;margin-left:auto;margin-right:auto;line-height:1.6;}
    .hero-tagline *{color:rgba(255,255,255,.5)!important;}
    .hero-badges{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;position:relative;}
    .h-badge{font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:500;padding:5px 14px;border-radius:100px;border:1px solid rgba(255,255,255,.15);color:rgba(255,255,255,.75)!important;background:rgba(255,255,255,.05);}
    .h-badge *{color:inherit!important;}
    .h-badge.green{border-color:rgba(34,197,94,.5);color:#4ade80!important;background:rgba(34,197,94,.1);}

    /* LANG TOGGLE */
    div.lang-toggle{margin-bottom:.5rem!important;position:relative;z-index:5;pointer-events:auto;}
    div.lang-toggle [data-testid="stRadio"] > label{display:none!important;}
    div.lang-toggle [role="radiogroup"]{flex-direction:row!important;gap:0!important;justify-content:flex-end!important;}
    div.lang-toggle [role="radiogroup"] > label,
    div.lang-toggle [role="radiogroup"] > div{
        background:white!important;color:#64748b!important;padding:5px 16px!important;font-size:.75rem!important;
        font-weight:700!important;font-family:'JetBrains Mono',monospace!important;
        border:1px solid rgba(0,0,0,.12)!important;margin:0!important;cursor:pointer!important;
        min-height:0!important;line-height:1.2!important;
    }
    div.lang-toggle [role="radiogroup"] > label:first-of-type,
    div.lang-toggle [role="radiogroup"] > div:first-of-type{border-radius:100px 0 0 100px!important;}
    div.lang-toggle [role="radiogroup"] > label:last-of-type,
    div.lang-toggle [role="radiogroup"] > div:last-of-type{border-radius:0 100px 100px 0!important;border-left:0!important;}
    div.lang-toggle [role="radiogroup"] > label[data-checked="true"],
    div.lang-toggle [role="radiogroup"] > div[data-checked="true"],
    div.lang-toggle [role="radiogroup"] > label[aria-checked="true"],
    div.lang-toggle [role="radiogroup"] > div[aria-checked="true"]{
        background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;
        border-color:rgba(99,102,241,.3)!important;
    }
    div.lang-toggle [role="radiogroup"] p,
    div.lang-toggle [role="radiogroup"] span,
    div.lang-toggle [role="radiogroup"] div[data-testid="stMarkdownContainer"] p{
        color:#64748b!important;font-size:.75rem!important;font-weight:700!important;
        font-family:'JetBrains Mono',monospace!important;margin:0!important;padding:0!important;
    }
    div.lang-toggle [role="radiogroup"] > label[data-checked="true"] p,
    div.lang-toggle [role="radiogroup"] > label[data-checked="true"] span,
    div.lang-toggle [role="radiogroup"] > div[data-checked="true"] p,
    div.lang-toggle [role="radiogroup"] > div[data-checked="true"] span,
    div.lang-toggle [role="radiogroup"] > label[aria-checked="true"] p,
    div.lang-toggle [role="radiogroup"] > label[aria-checked="true"] span{
        color:white!important;
    }
    div.lang-toggle [role="radiogroup"] input[type="radio"]{display:none!important;}

    .contact-bar{display:flex;justify-content:center;align-items:center;gap:1.5rem;padding:1rem 2rem;background:white;border-radius:0 0 24px 24px;border:1px solid rgba(0,0,0,.04);border-top:none;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(0,0,0,.03);flex-wrap:wrap;}
    .contact-bar a{display:inline-flex;align-items:center;font-size:.85rem;font-weight:600;color:#6366f1!important;text-decoration:none;padding:8px 18px;border-radius:10px;border:1px solid rgba(99,102,241,.2);background:rgba(99,102,241,.04);transition:all .2s;}
    .contact-bar a *{color:#6366f1!important;}
    .contact-bar a:hover{background:rgba(99,102,241,.1);transform:translateY(-1px);}
    .contact-bar a.rdv{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white!important;border:none;box-shadow:0 4px 12px rgba(99,102,241,.3);}
    .contact-bar a.rdv, .contact-bar a.rdv *{color:white!important;}

    .profil-card{background:white;border-radius:20px;padding:2rem 2.5rem;margin-bottom:2rem;box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 20px rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.04);line-height:1.75;}
    .profil-card p{color:#475569!important;}
    .collapse-section{background:white;border-radius:20px;padding:2rem 2.5rem;margin-bottom:2rem;box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 20px rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.04);}
    .collapse-section details summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:12px;padding:.3rem 0;user-select:none;}
    .collapse-section details summary::-webkit-details-marker{display:none;}
    .collapse-section details summary .sec-title{font-size:1.1rem;color:#6366f1!important;text-transform:uppercase;letter-spacing:.08em;font-weight:700;}
    .sec-chevron{width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;transition:transform .4s cubic-bezier(.4,0,.2,1);box-shadow:0 2px 8px rgba(99,102,241,.3);}
    .sec-chevron svg{fill:white;width:14px;height:14px;}
    .collapse-section details[open] .sec-chevron{transform:rotate(180deg);}
    .tl-item{padding:1.2rem 0;border-left:2px solid rgba(99,102,241,.15);margin-left:14px;padding-left:2rem;position:relative;}
    .tl-item::before{content:'';position:absolute;left:-7px;top:1.4rem;width:12px;height:12px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);box-shadow:0 0 0 4px rgba(99,102,241,.12);}
    .tl-item:last-child{border-left-color:transparent;}
    .tl-role{font-weight:700;color:#1e293b!important;font-size:.93rem;}
    .tl-company{font-weight:600;color:#6366f1!important;font-size:.85rem;}
    .tl-desc{color:#64748b!important;font-size:.82rem;margin-top:2px;}
    .exp-badge-on{display:inline-block;font-size:.6rem;padding:2px 8px;border-radius:100px;background:rgba(34,197,94,.1);color:#16a34a!important;border:1px solid rgba(34,197,94,.3);margin-left:6px;font-weight:600;}
    .exp-badge-off{display:inline-block;font-size:.6rem;padding:2px 8px;border-radius:100px;background:rgba(148,163,184,.1);color:#94a3b8!important;border:1px solid rgba(148,163,184,.3);margin-left:6px;font-weight:600;}
    .cs-card{background:white;border:1px solid rgba(0,0,0,.05);border-radius:20px;padding:2rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.03);}
    .cs-card:hover{box-shadow:0 8px 30px rgba(99,102,241,.08);border-color:rgba(99,102,241,.15);}
    .cs-title{font-size:1.1rem;font-weight:800;color:#1e293b!important;}
    .cs-role{font-size:.82rem;color:#6366f1!important;font-weight:600;}
    .cs-period{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:#94a3b8!important;}
    .cs-section-title{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8!important;font-weight:700;margin:1rem 0 .5rem;}
    .cs-text{font-size:.88rem;color:#475569!important;line-height:1.6;}
    .cs-impact{background:rgba(34,197,94,.04);border-left:3px solid #22c55e;padding:.4rem .8rem;border-radius:0 8px 8px 0;margin-bottom:.3rem;font-size:.84rem;color:#334155!important;}
    .cs-tech{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.68rem;padding:3px 10px;border-radius:6px;background:rgba(99,102,241,.06);color:#6366f1!important;border:1px solid rgba(99,102,241,.12);margin:2px;}
    .reco-card{background:white;border:1px solid rgba(0,0,0,.05);border-radius:16px;padding:1.3rem 1.5rem;margin-bottom:.8rem;position:relative;}
    .reco-card::before{content:open-quote;font-size:3rem;color:rgba(99,102,241,.15);position:absolute;top:8px;left:16px;font-family:Georgia,serif;line-height:1;}
    .reco-text{color:#475569!important;font-size:.9rem;line-height:1.6;padding-left:1.5rem;font-style:italic;}
    .reco-author{margin-top:.8rem;padding-left:1.5rem;}
    .reco-name{font-weight:700;color:#1e293b!important;font-size:.85rem;}
    .reco-name-link{font-weight:700;color:#6366f1!important;font-size:.85rem;text-decoration:none;border-bottom:1px solid rgba(99,102,241,.3);}
    .reco-name-link:hover{color:#4f46e5!important;border-bottom-color:#4f46e5;}
    .reco-verified{display:inline-block;font-size:.62rem;padding:2px 8px;border-radius:100px;background:rgba(34,197,94,.08);color:#16a34a!important;border:1px solid rgba(34,197,94,.25);font-weight:600;margin-left:8px;letter-spacing:.02em;}
    .reco-collab{display:block;font-size:.72rem;color:#94a3b8!important;margin-top:2px;font-style:italic;}
    .reco-info{color:#94a3b8!important;font-size:.78rem;}
    .reco-relation{display:inline-block;font-size:.65rem;padding:2px 8px;border-radius:100px;background:rgba(99,102,241,.08);color:#6366f1!important;border:1px solid rgba(99,102,241,.15);font-weight:600;margin-left:6px;}
    .m-card{background:white;border-radius:16px;padding:1.3rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 15px rgba(0,0,0,.02);border:1px solid rgba(0,0,0,.05);transition:all .3s;}
    .m-card:hover{transform:translateY(-3px);box-shadow:0 8px 30px rgba(99,102,241,.12);border-color:rgba(99,102,241,.2);}
    .m-card .m-label{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8!important;font-weight:600;margin-bottom:.4rem;}
    .m-card .m-value{font-size:1.4rem;font-weight:800;color:#6366f1!important;}
    .m-card .m-desc{font-size:.78rem;color:#94a3b8!important;margin-top:.2rem;}

    /* TABS */
    .stTabs [data-baseweb="tab-list"]{background:white;border-radius:20px;padding:10px;gap:10px;border:3px solid rgba(99,102,241,.2);box-shadow:0 6px 30px rgba(99,102,241,.1);justify-content:center;}
    .stTabs [data-baseweb="tab"]{font-weight:800;font-size:1.1rem;color:#94a3b8!important;border-radius:14px;padding:18px 40px;background:transparent;border:none;transition:all .2s;}
    .stTabs [data-baseweb="tab"]:hover{color:#6366f1!important;background:rgba(99,102,241,.04);}
    .stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;border:none!important;box-shadow:0 8px 25px rgba(99,102,241,.35);}
    .stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
    .stTabs [data-baseweb="tab-panel"]{padding-top:2rem;}

    /* CHAT */
    .chat-box{background:white;border:1px solid rgba(0,0,0,.06);border-radius:20px;padding:1.5rem;margin-bottom:1rem;max-height:480px;overflow-y:auto;position:relative;z-index:1;}
    .chat-box::-webkit-scrollbar{width:8px;} .chat-box::-webkit-scrollbar-track{background:#f1f5f9;border-radius:4px;} .chat-box::-webkit-scrollbar-thumb{background:#6366f1;border-radius:4px;}
    .chat-msg{padding:.7rem 1rem;margin-bottom:.5rem;border-radius:12px;font-size:.9rem;line-height:1.65;color:#334155!important;}
    .chat-msg *{color:#334155!important;}
    .chat-msg.user{background:rgba(99,102,241,.07);border:1px solid rgba(99,102,241,.12);}
    .chat-msg.assistant{background:#f8fafc;border:1px solid rgba(0,0,0,.04);}
    .chat-msg .msg-who{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.2rem;}
    .chat-msg.user .msg-who{color:#6366f1!important;}
    .chat-msg.assistant .msg-who{color:#94a3b8!important;}

    /* INPUTS — force dark text, visible placeholders, clickable, focus visible */
    .stChatInput{position:relative;z-index:10;}
    .stChatInput > div{background:white!important;border:2px solid rgba(0,0,0,.1)!important;border-radius:14px!important;transition:border-color .2s;}
    .stChatInput > div:focus-within{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.15)!important;}
    .stChatInput input, .stChatInput textarea{color:#1e293b!important;-webkit-text-fill-color:#1e293b!important;cursor:text!important;caret-color:#6366f1!important;}
    .stChatInput input::placeholder, .stChatInput textarea::placeholder{color:#94a3b8!important;-webkit-text-fill-color:#94a3b8!important;opacity:1!important;}
    [data-testid="stChatInput"]{position:relative;z-index:10;}
    [data-testid="stChatInput"] input, [data-testid="stChatInput"] textarea{color:#1e293b!important;-webkit-text-fill-color:#1e293b!important;cursor:text!important;caret-color:#6366f1!important;}
    [data-testid="stChatInput"] input::placeholder, [data-testid="stChatInput"] textarea::placeholder{color:#94a3b8!important;-webkit-text-fill-color:#94a3b8!important;opacity:1!important;}
    /* All text inputs focus state */
    .stTextInput input:focus, .stTextArea textarea:focus, input[type="text"]:focus, input[type="password"]:focus, textarea:focus{
        border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.12)!important;outline:none!important;caret-color:#6366f1!important;
    }
    .stTextInput input, input[type="text"], input[type="password"]{cursor:text!important;caret-color:#6366f1!important;}
    .stTextInput input,.stTextArea textarea,[data-baseweb="select"] > div,input[type="text"],input[type="password"],textarea{background:white!important;color:#1e293b!important;-webkit-text-fill-color:#1e293b!important;}
    .stTextInput input::placeholder,.stTextArea textarea::placeholder,input::placeholder,textarea::placeholder{color:#94a3b8!important;-webkit-text-fill-color:#94a3b8!important;opacity:1!important;}
    [data-baseweb="select"] span,[data-baseweb="select"] div{color:#1e293b!important;}
    .stTextInput label,.stTextArea label,.stSelectbox label,.stCheckbox label,[data-testid="stWidgetLabel"]{color:#475569!important;}
    .stCheckbox label span p{color:#475569!important;}

    /* BUTTONS */
    .stButton > button{font-weight:600!important;border-radius:12px!important;padding:.7rem 1.5rem!important;border:none!important;background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;box-shadow:0 4px 15px rgba(99,102,241,.25)!important;}
    .stButton > button:hover{transform:translateY(-1px)!important;box-shadow:0 8px 25px rgba(99,102,241,.35)!important;}
    .stButton > button span, .stButton > button p{color:white!important;}
    .stFormSubmitButton > button{font-weight:600!important;border-radius:12px!important;padding:.7rem 1.5rem!important;border:none!important;background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;box-shadow:0 4px 15px rgba(99,102,241,.25)!important;}
    .stFormSubmitButton > button:hover{transform:translateY(-1px)!important;box-shadow:0 8px 25px rgba(99,102,241,.35)!important;}
    .stFormSubmitButton > button span, .stFormSubmitButton > button p, .stFormSubmitButton > button div{color:white!important;-webkit-text-fill-color:white!important;}

    .tag{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.72rem;padding:4px 12px;border-radius:8px;border:1px solid rgba(99,102,241,.15);color:#6366f1!important;background:rgba(99,102,241,.06);}
    .score-box{border-radius:20px;padding:2rem;text-align:center;margin:1.5rem 0;}
    .score-box.high{background:linear-gradient(135deg,rgba(34,197,94,.08),rgba(34,197,94,.02));border:1px solid rgba(34,197,94,.15);}
    .score-box.mid{background:linear-gradient(135deg,rgba(234,179,8,.08),rgba(234,179,8,.02));border:1px solid rgba(234,179,8,.15);}
    .score-box.low{background:linear-gradient(135deg,rgba(239,68,68,.08),rgba(239,68,68,.02));border:1px solid rgba(239,68,68,.15);}
    .score-num{font-size:3.5rem;font-weight:800;}
    .score-box.high .score-num{color:#16a34a!important;} .score-box.mid .score-num{color:#ca8a04!important;} .score-box.low .score-num{color:#dc2626!important;}
    .score-sub{font-size:.85rem;color:#94a3b8!important;}
    .pt-fort{background:rgba(34,197,94,.05);border-left:3px solid #22c55e;padding:.6rem 1rem;border-radius:0 10px 10px 0;margin-bottom:.5rem;font-size:.88rem;color:#334155!important;}
    .pt-att{background:rgba(234,179,8,.05);border-left:3px solid #eab308;padding:.6rem 1rem;border-radius:0 10px 10px 0;margin-bottom:.5rem;font-size:.88rem;color:#334155!important;}
    .info-box{background:rgba(99,102,241,.04);border:1px solid rgba(99,102,241,.12);border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;}
    .info-box .info-title{color:#6366f1!important;font-weight:700;font-size:.9rem;}
    .info-box .info-desc{color:#64748b!important;font-size:.85rem;}
    hr{border-color:rgba(0,0,0,.06)!important;margin:1.5rem 0!important;}
    .site-footer{text-align:center;padding:2.5rem 0 1rem;font-size:.8rem;color:#94a3b8!important;}
    .site-footer *{color:#94a3b8!important;}
    .site-footer a, .site-footer a *{color:#6366f1!important;}
    .admin-zone input{font-size:.75rem!important;padding:6px 10px!important;background:white!important;border:2px solid rgba(0,0,0,.08)!important;border-radius:8px!important;caret-color:#6366f1!important;cursor:text!important;}
    .admin-zone input:focus{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.12)!important;outline:none!important;}
    .admin-zone button{font-size:.7rem!important;padding:4px 10px!important;background:#e2e8f0!important;color:#64748b!important;box-shadow:none!important;border:1px solid rgba(0,0,0,.08)!important;}
    .admin-zone button span, .admin-zone button p{color:#64748b!important;}
    .admin-header{background:linear-gradient(135deg,#dc2626,#ef4444);border-radius:16px;padding:1rem 2rem;margin-bottom:2rem;}
    .admin-header-title{color:white!important;font-size:1.3rem;font-weight:800;}
    .admin-header-sub{color:rgba(255,255,255,.7)!important;font-size:.8rem;}
    /* Admin tabs — smaller, wrap instead of scroll */
    .admin-header + div .stTabs [data-baseweb="tab-list"],
    div:has(> .admin-header) ~ div .stTabs [data-baseweb="tab-list"]{
        flex-wrap:wrap!important;overflow:visible!important;padding:6px!important;gap:4px!important;border-width:2px!important;
    }
    .admin-header + div .stTabs [data-baseweb="tab"],
    div:has(> .admin-header) ~ div .stTabs [data-baseweb="tab"]{
        font-size:.85rem!important;padding:10px 18px!important;font-weight:600!important;
    }
    /* Hide scroll arrows globally on tabs */
    .stTabs [data-baseweb="tab-list"] button[aria-label]{
        background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:white!important;
        border:none!important;border-radius:50%!important;width:28px!important;height:28px!important;
        min-width:28px!important;box-shadow:0 2px 8px rgba(99,102,241,.3)!important;
    }
</style>
"""
