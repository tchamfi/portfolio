"""
styles.py — Premium CSS for Ask Lionel portfolio
"""

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
    .stApp{background:#f4f2ee;font-family:'Outfit',sans-serif;}
    #MainMenu,footer,header{visibility:hidden;} .stDeployButton{display:none;}
    .block-container{max-width:1200px;padding-top:.5rem;}
    section[data-testid="stSidebar"]{display:none;}
    h1,h2,h3,h4{font-family:'Outfit',sans-serif!important;color:#1a1a2e!important;}
    p,li,span,label,div{font-family:'Outfit',sans-serif!important;}
    .stApp p, .stApp span, .stApp label, .stApp div{color:#334155;}
    .stApp strong, .stApp b{color:#1e293b;}

    .hero-section{text-align:center;padding:2.5rem 2rem 2rem;background:linear-gradient(160deg,#0c0a1d,#1a1145,#0d1b3e);border-radius:28px;margin-bottom:0;position:relative;overflow:hidden;}
    .hero-glow{position:absolute;top:-80px;right:-80px;width:300px;height:300px;background:radial-gradient(circle,rgba(99,102,241,.25) 0%,transparent 70%);border-radius:50%;pointer-events:none;}
    .hero-section::after{content:'';position:absolute;bottom:-60px;left:-60px;width:250px;height:250px;background:radial-gradient(circle,rgba(236,72,153,.12) 0%,transparent 70%);border-radius:50%;pointer-events:none;}
    .hero-inner{display:flex;align-items:center;justify-content:center;gap:20px;position:relative;z-index:2;margin-bottom:12px;}
    .hero-avatar{width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#a855f7);display:flex;align-items:center;justify-content:center;font-size:1.6rem;font-weight:800;color:white;border:3px solid rgba(255,255,255,.15);box-shadow:0 8px 32px rgba(99,102,241,.4);flex-shrink:0;letter-spacing:-.02em;}
    .hero-text{text-align:left;}
    .hero-name{font-size:2.4rem;font-weight:900;background:linear-gradient(135deg,#e0e7ff,#c7d2fe,#a5b4fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.04em;line-height:1.1;}
    .hero-title{font-size:1rem;color:rgba(255,255,255,.6)!important;margin-top:4px;font-weight:400;letter-spacing:.02em;}
    .hero-title *{color:rgba(255,255,255,.6)!important;}
    .hero-tagline{font-size:.85rem;color:rgba(255,255,255,.4)!important;margin-bottom:1rem;position:relative;z-index:2;max-width:600px;margin-left:auto;margin-right:auto;line-height:1.65;}
    .hero-tagline *{color:rgba(255,255,255,.4)!important;}
    .hero-badges{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;position:relative;z-index:2;}
    .h-badge{font-family:'JetBrains Mono',monospace;font-size:.68rem;font-weight:500;padding:5px 14px;border-radius:100px;border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6)!important;background:rgba(255,255,255,.04);backdrop-filter:blur(4px);transition:all .3s;}
    .h-badge:hover{border-color:rgba(255,255,255,.25);background:rgba(255,255,255,.08);}
    .h-badge *{color:inherit!important;}
    .h-badge.green{border-color:rgba(34,197,94,.4);color:#4ade80!important;background:rgba(34,197,94,.08);}

    div.lang-toggle{margin-bottom:.5rem!important;position:relative;z-index:5;pointer-events:auto;}
    div.lang-toggle [data-testid="stRadio"] > label{display:none!important;}
    div.lang-toggle [role="radiogroup"]{flex-direction:row!important;gap:0!important;justify-content:flex-end!important;}
    div.lang-toggle [role="radiogroup"] > label, div.lang-toggle [role="radiogroup"] > div{background:white!important;color:#64748b!important;padding:5px 16px!important;font-size:.72rem!important;font-weight:600!important;font-family:'JetBrains Mono',monospace!important;border:1px solid rgba(0,0,0,.1)!important;margin:0!important;cursor:pointer!important;min-height:0!important;line-height:1.2!important;transition:all .2s!important;}
    div.lang-toggle [role="radiogroup"] > label:first-of-type, div.lang-toggle [role="radiogroup"] > div:first-of-type{border-radius:100px 0 0 100px!important;}
    div.lang-toggle [role="radiogroup"] > label:last-of-type, div.lang-toggle [role="radiogroup"] > div:last-of-type{border-radius:0 100px 100px 0!important;border-left:0!important;}
    div.lang-toggle [role="radiogroup"] > label[data-checked="true"], div.lang-toggle [role="radiogroup"] > div[data-checked="true"], div.lang-toggle [role="radiogroup"] > label[aria-checked="true"], div.lang-toggle [role="radiogroup"] > div[aria-checked="true"]{background:#1e293b!important;color:white!important;border-color:#1e293b!important;}
    div.lang-toggle [role="radiogroup"] p, div.lang-toggle [role="radiogroup"] span, div.lang-toggle [role="radiogroup"] div[data-testid="stMarkdownContainer"] p{color:#64748b!important;font-size:.72rem!important;font-weight:600!important;font-family:'JetBrains Mono',monospace!important;margin:0!important;padding:0!important;}
    div.lang-toggle [role="radiogroup"] > label[data-checked="true"] p, div.lang-toggle [role="radiogroup"] > label[data-checked="true"] span, div.lang-toggle [role="radiogroup"] > div[data-checked="true"] p, div.lang-toggle [role="radiogroup"] > div[data-checked="true"] span, div.lang-toggle [role="radiogroup"] > label[aria-checked="true"] p, div.lang-toggle [role="radiogroup"] > label[aria-checked="true"] span{color:white!important;}
    div.lang-toggle [role="radiogroup"] input[type="radio"]{display:none!important;}

    .contact-bar{display:flex;justify-content:center;align-items:center;gap:1.2rem;padding:.8rem 2rem;background:white;border-radius:0 0 20px 20px;border:1px solid rgba(0,0,0,.04);border-top:none;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(0,0,0,.04);flex-wrap:wrap;}
    .contact-bar a{display:inline-flex;align-items:center;font-size:.82rem;font-weight:600;color:#475569!important;text-decoration:none;padding:6px 14px;border-radius:8px;transition:all .25s;}
    .contact-bar a *{color:#475569!important;}
    .contact-bar a:hover{background:#f1f5f9;color:#1e293b!important;transform:translateY(-1px);}
    .contact-bar a.rdv{background:#1e293b;color:white!important;border:none;box-shadow:0 4px 12px rgba(30,41,59,.2);padding:8px 20px;border-radius:10px;}
    .contact-bar a.rdv, .contact-bar a.rdv *{color:white!important;}
    .contact-bar a.rdv:hover{background:#0f172a;box-shadow:0 6px 20px rgba(30,41,59,.3);}

    .profil-card{background:white;border-radius:20px;padding:2rem 2.5rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.04);line-height:1.8;}
    .profil-card p{color:#475569!important;font-size:.92rem;}
    .collapse-section{background:white;border-radius:20px;padding:2rem 2.5rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.04);}
    .collapse-section details summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:12px;padding:.3rem 0;user-select:none;}
    .collapse-section details summary::-webkit-details-marker{display:none;}
    .collapse-section details summary .sec-title{font-size:1rem;color:#1e293b!important;letter-spacing:.02em;font-weight:700;}
    .sec-chevron{width:28px;height:28px;border-radius:50%;background:#1e293b;display:flex;align-items:center;justify-content:center;transition:transform .4s cubic-bezier(.4,0,.2,1);}
    .sec-chevron svg{fill:white;width:14px;height:14px;}
    .collapse-section details[open] .sec-chevron{transform:rotate(180deg);}

    .tl-item{padding:1.2rem 0;border-left:2px solid rgba(30,41,59,.1);margin-left:14px;padding-left:2rem;position:relative;}
    .tl-item::before{content:'';position:absolute;left:-7px;top:1.4rem;width:12px;height:12px;border-radius:50%;background:#1e293b;box-shadow:0 0 0 4px rgba(30,41,59,.08);}
    .tl-item:last-child{border-left-color:transparent;}
    .tl-role{font-weight:700;color:#1e293b!important;font-size:.93rem;}
    .tl-company{font-weight:600;color:#6366f1!important;font-size:.85rem;}
    .tl-desc{color:#64748b!important;font-size:.82rem;margin-top:2px;}
    .exp-badge-on{display:inline-block;font-size:.6rem;padding:2px 8px;border-radius:100px;background:rgba(34,197,94,.1);color:#16a34a!important;border:1px solid rgba(34,197,94,.3);margin-left:6px;font-weight:600;}
    .exp-badge-off{display:inline-block;font-size:.6rem;padding:2px 8px;border-radius:100px;background:rgba(148,163,184,.1);color:#94a3b8!important;border:1px solid rgba(148,163,184,.3);margin-left:6px;font-weight:600;}

    .cs-card{background:white;border:1px solid rgba(0,0,0,.04);border-radius:20px;padding:2rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.03);transition:all .3s;}
    .cs-card:hover{box-shadow:0 8px 30px rgba(0,0,0,.06);transform:translateY(-2px);}
    .cs-title{font-size:1.1rem;font-weight:800;color:#1e293b!important;}
    .cs-role{font-size:.82rem;color:#6366f1!important;font-weight:600;}
    .cs-period{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:#94a3b8!important;}
    .cs-section-title{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8!important;font-weight:700;margin:1rem 0 .5rem;}
    .cs-text{font-size:.88rem;color:#475569!important;line-height:1.6;}
    .cs-impact{background:rgba(34,197,94,.04);border-left:3px solid #22c55e;padding:.4rem .8rem;border-radius:0 8px 8px 0;margin-bottom:.3rem;font-size:.84rem;color:#334155!important;}
    .cs-tech{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.68rem;padding:3px 10px;border-radius:6px;background:rgba(30,41,59,.04);color:#475569!important;border:1px solid rgba(30,41,59,.08);margin:2px;}

    .reco-card{background:white;border:1px solid rgba(0,0,0,.04);border-radius:20px;padding:1.5rem 1.8rem;margin-bottom:1rem;position:relative;box-shadow:0 1px 3px rgba(0,0,0,.03);transition:all .3s;}
    .reco-card:hover{box-shadow:0 8px 30px rgba(0,0,0,.06);transform:translateY(-2px);}
    .reco-card::before{content:open-quote;font-size:3.5rem;color:rgba(99,102,241,.1);position:absolute;top:4px;left:18px;font-family:Georgia,serif;line-height:1;}
    .reco-text{color:#475569!important;font-size:.9rem;line-height:1.7;padding-left:1.5rem;font-style:italic;}
    .reco-author{margin-top:.8rem;padding-left:1.5rem;}
    .reco-author-row{display:flex;align-items:center;gap:12px;margin-top:1rem;padding-top:.8rem;border-top:1px solid rgba(0,0,0,.05);padding-left:1.5rem;}
    .reco-avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#e0e7ff,#c7d2fe);display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:700;color:#4338ca!important;flex-shrink:0;}
    .reco-author-info{flex:1;}
    .reco-name{font-weight:700;color:#1e293b!important;font-size:.85rem;}
    .reco-name-link{font-weight:700;color:#1e293b!important;font-size:.85rem;text-decoration:none;border-bottom:1px solid rgba(30,41,59,.2);}
    .reco-name-link:hover{color:#6366f1!important;border-bottom-color:#6366f1;}
    .reco-verified{display:inline-block;font-size:.6rem;padding:2px 8px;border-radius:100px;background:rgba(34,197,94,.08);color:#16a34a!important;border:1px solid rgba(34,197,94,.2);font-weight:600;margin-left:8px;}
    .reco-collab{display:block;font-size:.72rem;color:#94a3b8!important;margin-top:2px;font-style:italic;}
    .reco-info{color:#94a3b8!important;font-size:.78rem;}
    .reco-relation{display:inline-block;font-size:.62rem;padding:2px 8px;border-radius:100px;background:rgba(30,41,59,.04);color:#64748b!important;border:1px solid rgba(30,41,59,.08);font-weight:600;margin-left:6px;}

    .m-card{background:white;border-radius:16px;padding:1.3rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.04);transition:all .3s;}
    .m-card:hover{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,.06);}
    .m-card .m-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8!important;font-weight:600;margin-bottom:.4rem;}
    .m-card .m-value{font-size:1.4rem;font-weight:800;color:#1e293b!important;}
    .m-card .m-desc{font-size:.75rem;color:#94a3b8!important;margin-top:.2rem;}

    .stTabs [data-baseweb="tab-list"]{background:white;border-radius:16px;padding:8px;gap:6px;border:1px solid rgba(0,0,0,.09)!important;box-shadow:0 2px 10px rgba(0,0,0,.07);justify-content:center;outline:none!important;}
    .stTabs [data-baseweb="tab"]{font-weight:600!important;font-size:.88rem!important;color:#334155!important;border-radius:10px!important;padding:12px 24px!important;background:#f1f5f9!important;border:1px solid #cbd5e1!important;transition:all .25s ease!important;}
    .stTabs [data-baseweb="tab"] p,.stTabs [data-baseweb="tab"] span,.stTabs [data-baseweb="tab"] div{font-weight:600!important;color:#334155!important;}
    .stTabs [data-baseweb="tab"]:hover{color:#1e293b!important;background:#e2e8f0!important;border-color:#94a3b8!important;}
    .stTabs [data-baseweb="tab"]:hover p,.stTabs [data-baseweb="tab"]:hover span{color:#1e293b!important;}
    .stTabs [aria-selected="true"]{background:#1e293b!important;color:#ffffff!important;border:1px solid #1e293b!important;box-shadow:0 4px 12px rgba(30,41,59,.2)!important;-webkit-text-fill-color:#ffffff!important;}
    .stTabs [aria-selected="true"] p,.stTabs [aria-selected="true"] span,.stTabs [aria-selected="true"] div{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:600!important;}
    .stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none!important;}
    .stTabs [data-baseweb="tab-panel"]{padding-top:2rem!important;}

    .chat-box{background:white;border:1px solid rgba(0,0,0,.04);border-radius:20px;padding:1.5rem;margin-bottom:1rem;max-height:480px;overflow-y:auto;position:relative;z-index:1;}
    .chat-box::-webkit-scrollbar{width:6px;} .chat-box::-webkit-scrollbar-track{background:transparent;} .chat-box::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px;}
    .chat-row{display:flex;gap:10px;align-items:flex-start;margin-bottom:14px;}
    .chat-row.user{flex-direction:row-reverse;}
    .chat-avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;flex-shrink:0;}
    .av-bot{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;}
    .av-user{background:#e2e8f0;color:#64748b;}
    .chat-bubble{padding:.75rem 1rem;border-radius:16px;font-size:.88rem;line-height:1.7;color:#334155!important;max-width:80%;}
    .chat-bubble *{color:#334155!important;}
    .bubble-bot{background:#f8fafc;border:1px solid rgba(0,0,0,.04);border-top-left-radius:4px;}
    .bubble-user{background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.1);border-top-right-radius:4px;}

    .stChatInput{position:relative;z-index:10;}
    .stChatInput > div{background:white!important;border:1.5px solid rgba(0,0,0,.08)!important;border-radius:14px!important;transition:border-color .2s;}
    .stChatInput > div:focus-within{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.1)!important;}
    .stChatInput input, .stChatInput textarea{color:#1e293b!important;-webkit-text-fill-color:#1e293b!important;cursor:text!important;caret-color:#6366f1!important;}
    .stChatInput input::placeholder, .stChatInput textarea::placeholder{color:#94a3b8!important;-webkit-text-fill-color:#94a3b8!important;opacity:1!important;}
    [data-testid="stChatInput"]{position:relative;z-index:10;}
    [data-testid="stChatInput"] input, [data-testid="stChatInput"] textarea{color:#1e293b!important;-webkit-text-fill-color:#1e293b!important;cursor:text!important;caret-color:#6366f1!important;}
    [data-testid="stChatInput"] input::placeholder, [data-testid="stChatInput"] textarea::placeholder{color:#94a3b8!important;-webkit-text-fill-color:#94a3b8!important;opacity:1!important;}
    .stTextInput input:focus, .stTextArea textarea:focus, input[type="text"]:focus, input[type="password"]:focus, textarea:focus{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.08)!important;outline:none!important;caret-color:#6366f1!important;}
    .stTextInput input, input[type="text"], input[type="password"]{cursor:text!important;caret-color:#6366f1!important;}
    .stTextInput input,.stTextArea textarea,[data-baseweb="select"] > div,input[type="text"],input[type="password"],textarea{background:white!important;color:#1e293b!important;-webkit-text-fill-color:#1e293b!important;border-radius:10px!important;}
    .stTextInput input::placeholder,.stTextArea textarea::placeholder,input::placeholder,textarea::placeholder{color:#94a3b8!important;-webkit-text-fill-color:#94a3b8!important;opacity:1!important;}
    [data-baseweb="select"] span,[data-baseweb="select"] div{color:#1e293b!important;}
    .stTextInput label,.stTextArea label,.stSelectbox label,.stCheckbox label,[data-testid="stWidgetLabel"]{color:#475569!important;}
    .stCheckbox label span p{color:#475569!important;}

    .stButton > button{font-weight:600!important;border-radius:12px!important;padding:.7rem 1.5rem!important;border:none!important;background:#1e293b!important;color:white!important;box-shadow:0 4px 12px rgba(30,41,59,.12)!important;transition:all .25s!important;}
    .stButton > button:hover{transform:translateY(-1px)!important;box-shadow:0 8px 20px rgba(30,41,59,.2)!important;background:#0f172a!important;}
    .stButton > button span, .stButton > button p{color:white!important;}
    .stFormSubmitButton > button{font-weight:600!important;border-radius:12px!important;padding:.7rem 1.5rem!important;border:none!important;background:#1e293b!important;color:white!important;box-shadow:0 4px 12px rgba(30,41,59,.12)!important;transition:all .25s!important;}
    .stFormSubmitButton > button:hover{transform:translateY(-1px)!important;box-shadow:0 8px 20px rgba(30,41,59,.2)!important;background:#0f172a!important;}
    .stFormSubmitButton > button span, .stFormSubmitButton > button p, .stFormSubmitButton > button div{color:white!important;-webkit-text-fill-color:white!important;}

    .tag{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.72rem;padding:4px 12px;border-radius:8px;border:1px solid rgba(30,41,59,.08);color:#475569!important;background:rgba(30,41,59,.03);}
    .score-box{border-radius:20px;padding:2rem;text-align:center;margin:1.5rem 0;}
    .score-box.high{background:rgba(34,197,94,.04);border:1px solid rgba(34,197,94,.12);}
    .score-box.mid{background:rgba(234,179,8,.04);border:1px solid rgba(234,179,8,.12);}
    .score-box.low{background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.12);}
    .score-num{font-size:3.5rem;font-weight:800;}
    .score-box.high .score-num{color:#16a34a!important;} .score-box.mid .score-num{color:#ca8a04!important;} .score-box.low .score-num{color:#dc2626!important;}
    .score-sub{font-size:.85rem;color:#94a3b8!important;}
    .pt-fort{background:rgba(34,197,94,.04);border-left:3px solid #22c55e;padding:.6rem 1rem;border-radius:0 10px 10px 0;margin-bottom:.5rem;font-size:.88rem;color:#334155!important;}
    .pt-att{background:rgba(234,179,8,.04);border-left:3px solid #eab308;padding:.6rem 1rem;border-radius:0 10px 10px 0;margin-bottom:.5rem;font-size:.88rem;color:#334155!important;}
    .pt-gap-red{background:rgba(220,38,38,.04);border-left:3px solid #dc2626;padding:.6rem 1rem;border-radius:0 10px 10px 0;margin-bottom:.5rem;font-size:.88rem;color:#334155!important;}
    .pt-gap-orange{background:rgba(217,119,6,.04);border-left:3px solid #d97706;padding:.6rem 1rem;border-radius:0 10px 10px 0;margin-bottom:.5rem;font-size:.88rem;color:#334155!important;}
    .gap-section-title{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:1rem 0 .5rem;}

    .info-box{background:white;border:1px solid rgba(0,0,0,.04);border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.03);}
    .info-box .info-title{color:#1e293b!important;font-weight:700;font-size:.92rem;}
    .info-box .info-desc{color:#64748b!important;font-size:.84rem;margin-top:4px;line-height:1.5;}
    hr{border-color:rgba(0,0,0,.06)!important;margin:1.5rem 0!important;}
    .site-footer{text-align:center;padding:2rem 0 1rem;font-size:.8rem;color:#94a3b8!important;}
    .site-footer *{color:#94a3b8!important;}
    .site-footer a, .site-footer a *{color:#475569!important;}

    .admin-zone input{font-size:.75rem!important;padding:6px 10px!important;background:white!important;border:2px solid rgba(0,0,0,.08)!important;border-radius:8px!important;caret-color:#6366f1!important;cursor:text!important;}
    .admin-zone input:focus{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.12)!important;outline:none!important;}
    .admin-zone button{font-size:.7rem!important;padding:4px 10px!important;background:#e2e8f0!important;color:#64748b!important;box-shadow:none!important;border:1px solid rgba(0,0,0,.08)!important;}
    .admin-zone button span, .admin-zone button p{color:#64748b!important;}
    .admin-header{background:#1e293b;border-radius:16px;padding:1rem 2rem;margin-bottom:2rem;}
    .admin-header-title{color:white!important;font-size:1.3rem;font-weight:800;}
    .admin-header-sub{color:rgba(255,255,255,.6)!important;font-size:.8rem;}
    .admin-header + div .stTabs [data-baseweb="tab-list"], div:has(> .admin-header) ~ div .stTabs [data-baseweb="tab-list"]{flex-wrap:wrap!important;overflow:visible!important;padding:6px!important;gap:4px!important;}
    .admin-header + div .stTabs [data-baseweb="tab"], div:has(> .admin-header) ~ div .stTabs [data-baseweb="tab"]{font-size:.82rem!important;padding:8px 16px!important;font-weight:600!important;}
    .stTabs [data-baseweb="tab-list"] button[aria-label]{background:#1e293b!important;color:white!important;border:none!important;border-radius:50%!important;width:28px!important;height:28px!important;min-width:28px!important;box-shadow:0 2px 8px rgba(30,41,59,.2)!important;}

    @media (max-width: 768px) {
        .block-container{padding:0 .5rem!important;}
        .hero-section{padding:1.5rem 1rem;border-radius:16px;}
        .hero-inner{flex-direction:column;gap:10px;}
        .hero-text{text-align:center;}
        .hero-avatar{width:56px;height:56px;font-size:1.2rem;}
        .hero-name{font-size:1.6rem!important;}
        .hero-title{font-size:.85rem!important;}
        .hero-tagline{font-size:.78rem!important;}
        .hero-badges{gap:4px;}
        .h-badge{font-size:.58rem!important;padding:3px 8px!important;}
        .contact-bar{flex-direction:column;gap:6px!important;padding:10px!important;}
        .contact-bar a{font-size:.75rem!important;padding:6px 12px!important;}
        .m-card{padding:10px 8px!important;}
        .m-card .m-value{font-size:1.2rem!important;}
        .m-card .m-label{font-size:.6rem!important;}
        .stTabs [data-baseweb="tab-list"]{padding:6px!important;gap:3px!important;border-radius:12px!important;overflow-x:auto!important;flex-wrap:nowrap!important;justify-content:flex-start!important;}
        .stTabs [data-baseweb="tab"]{font-size:.72rem!important;padding:10px 14px!important;white-space:nowrap!important;min-width:auto!important;}
        .chat-box{max-height:350px!important;}
        .chat-bubble{font-size:.82rem!important;padding:8px 10px!important;}
        .chat-avatar{width:26px!important;height:26px!important;font-size:.6rem!important;}
        .info-box{padding:14px!important;}
        .info-title{font-size:.9rem!important;}
        .info-desc{font-size:.78rem!important;}
        .cs-card{padding:16px!important;}
        .reco-card{padding:14px!important;}
        .profil-card{padding:16px!important;}
        .profil-card p{font-size:.85rem!important;}
        .pt-fort,.pt-att,.pt-gap-red,.pt-gap-orange{font-size:.8rem!important;padding:8px 10px!important;}
    }
    @media (max-width: 480px) {
        .hero-name{font-size:1.3rem!important;}
        .hero-title{font-size:.75rem!important;}
        .hero-avatar{width:44px;height:44px;font-size:1rem;}
        .hero-badges{gap:3px;}
        .h-badge{font-size:.52rem!important;padding:2px 6px!important;}
        .stTabs [data-baseweb="tab"]{font-size:.62rem!important;padding:8px 10px!important;}
    }
</style>
"""
