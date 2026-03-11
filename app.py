"""
Ask Lionel — Portfolio V2.5 (Hugging Face deployment)
"""

import re, json
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from rag_pipeline import ask, create_chroma_collection
from agent import run_agent
from airtable_store import load_config, save_config, load_recos, add_reco, update_all_recos
from styles import CSS
from config import (PRIVATE_CODE, FALLBACK_CONFIG, WELCOME_FR, WELCOME_EN,
                    CHEVRON_SVG, get_config_context, swap)

st.set_page_config(page_title="Lionel TCHAMFONG — Senior PO", page_icon="🔷", layout="wide", initial_sidebar_state="collapsed")


st.markdown(CSS, unsafe_allow_html=True)


# --- Init ---
if "db_initialized" not in st.session_state:
    with st.spinner(""): create_chroma_collection(); st.session_state.db_initialized=True
if "is_private" not in st.session_state: st.session_state.is_private=False
if "admin_view" not in st.session_state: st.session_state.admin_view=False
if "lang" not in st.session_state: st.session_state.lang="fr"
if "messages" not in st.session_state: st.session_state.messages=[{"role":"assistant","content":WELCOME_FR}]
if "config" not in st.session_state:
    cfg_loaded=load_config(); merged=FALLBACK_CONFIG.copy()
    if cfg_loaded:
        for k,v in cfg_loaded.items():
            if not k.startswith("_"): merged[k]=v
        merged["_record_ids"]=cfg_loaded.get("_record_ids",{})
    # Ensure visibility flags exist
    for vk in ["show_profil","show_metrics","show_case_studies","show_parcours","show_recos"]:
        if vk not in merged: merged[vk]=True
    st.session_state.config=merged
if "recos" not in st.session_state: st.session_state.recos=load_recos()

is_private=st.session_state.is_private; cfg=st.session_state.config; recos=st.session_state.recos; lang=st.session_state.lang
chevron_svg=CHEVRON_SVG

# ================================================================
# ADMIN
# ================================================================
if st.session_state.admin_view:
    hc1,hc2=st.columns([3,1])
    with hc1: st.markdown('<div class="admin-header"><div class="admin-header-title">Panneau d&rsquo;administration</div><div class="admin-header-sub">Sauvegarde Airtable</div></div>',unsafe_allow_html=True)
    with hc2:
        if st.button("Retour au site",use_container_width=True,key="back"): st.session_state.admin_view=False; st.rerun()

    if "admin_exp" not in st.session_state: st.session_state.admin_exp=list(cfg.get("exp",[]))
    if "admin_cs" not in st.session_state: st.session_state.admin_cs=list(cfg.get("case_studies",[]))
    if "admin_v" not in st.session_state: st.session_state.admin_v=0
    av=st.session_state.admin_v  # version counter for widget keys

    at1,at2,at3,at4,at5,at6,at7=st.tabs(["📋 General","👁 Visibilite","📝 Profil","📊 Metriques","💼 Experiences","🎯 Case Studies","⭐ Recos"])

    with at1:
        st.markdown("**Hero**")
        new_hero_name=st.text_input("Nom affiche",value=cfg.get("hero_name","Lionel TCHAMFONG"),key="a_hname")
        new_hero_title=st.text_input("Titre (sous le nom)",value=cfg.get("hero_title",""),key="a_htitle")
        hc1,hc2=st.columns(2)
        with hc1: new_hero_tl_fr=st.text_area("Tagline FR",value=cfg.get("hero_tagline_fr",""),key="a_htlfr",height=80)
        with hc2: new_hero_tl_en=st.text_area("Tagline EN",value=cfg.get("hero_tagline_en",""),key="a_htlen",height=80)
        new_hero_badges=st.text_input("Badges (separes par des virgules)",value=cfg.get("hero_badges","CSPO,CSM,Cloud,Data,GenAI"),key="a_hbadges")
        st.caption("Ex: CSPO, CSM, Cloud, Data, GenAI")
        st.markdown("---")
        st.markdown("**Infos generales**")
        dispo_opts=["Immediat","Sous 2 semaines","Sous 1 mois","En mission"]; remote_opts=["IDF + Remote","Full Remote","Sur site uniquement","Hybride"]
        cur_dispo=cfg.get("disponibilite","Immediat"); cur_remote=cfg.get("remote","IDF + Remote")
        gc1,gc2=st.columns(2)
        with gc1: new_tjm=st.text_input("TJM",value=cfg.get("tjm",""),key="a_tjm"); new_dispo=st.selectbox("Disponibilite",dispo_opts,index=dispo_opts.index(cur_dispo) if cur_dispo in dispo_opts else 0,key="a_dispo"); new_remote=st.selectbox("Mode",remote_opts,index=remote_opts.index(cur_remote) if cur_remote in remote_opts else 0,key="a_remote")
        with gc2: new_linkedin=st.text_input("LinkedIn",value=cfg.get("linkedin",""),key="a_li"); new_email=st.text_input("Email",value=cfg.get("email",""),key="a_em"); new_phone=st.text_input("Tel",value=cfg.get("phone",""),key="a_ph"); new_calendly=st.text_input("Calendly",value=cfg.get("calendly",""),key="a_cal")
        vc1,vc2=st.columns(2)
        with vc1: new_show_tjm=st.checkbox("Afficher TJM",value=cfg.get("show_tjm",True),key="a_stjm")
        with vc2: new_show_phone=st.checkbox("Afficher tel",value=cfg.get("show_phone",True),key="a_sph")

    with at2:
        st.caption("Activez ou desactivez les sections visibles sur le site public.")
        v1,v2=st.columns(2)
        with v1:
            new_show_metrics=st.checkbox("Metriques",value=cfg.get("show_metrics",True),key="v_met")
            new_show_profil=st.checkbox("Profil / A propos",value=cfg.get("show_profil",True),key="v_pro")
            new_show_cs=st.checkbox("Etudes de cas",value=cfg.get("show_case_studies",True),key="v_cs")
        with v2:
            new_show_parcours=st.checkbox("Parcours professionnel",value=cfg.get("show_parcours",True),key="v_par")
            new_show_recos=st.checkbox("Recommandations",value=cfg.get("show_recos",True),key="v_rec")

    with at3:
        pc1,pc2=st.columns(2)
        with pc1:
            st.markdown("**Francais**")
            new_p1=st.text_area("P1 FR",value=cfg.get("profil_p1",""),key="a_p1",height=90); new_p2=st.text_area("P2 FR",value=cfg.get("profil_p2",""),key="a_p2",height=90); new_p3=st.text_area("P3 FR",value=cfg.get("profil_p3",""),key="a_p3",height=90); new_p4=st.text_area("P4 FR",value=cfg.get("profil_p4",""),key="a_p4",height=90)
        with pc2:
            st.markdown("**English**")
            new_p1en=st.text_area("P1 EN",value=cfg.get("profil_p1_en",""),key="a_p1en",height=90); new_p2en=st.text_area("P2 EN",value=cfg.get("profil_p2_en",""),key="a_p2en",height=90); new_p3en=st.text_area("P3 EN",value=cfg.get("profil_p3_en",""),key="a_p3en",height=90); new_p4en=st.text_area("P4 EN",value=cfg.get("profil_p4_en",""),key="a_p4en",height=90)

    with at4:
        mc1,mc2=st.columns(2)
        with mc1: st.markdown("**Carte 1**"); nm1l=st.text_input("Label",value=cfg.get("metric1_label",""),key="a_m1l"); nm1v=st.text_input("Valeur",value=cfg.get("metric1_value",""),key="a_m1v"); nm1d=st.text_input("Desc",value=cfg.get("metric1_desc",""),key="a_m1d"); st.markdown("**Carte 3**"); nm3l=st.text_input("Label ",value=cfg.get("metric3_label",""),key="a_m3l"); nm3v=st.text_input("Valeur ",value=cfg.get("metric3_value",""),key="a_m3v"); nm3d=st.text_input("Desc ",value=cfg.get("metric3_desc",""),key="a_m3d")
        with mc2: st.markdown("**Carte 2**"); nm2l=st.text_input("Label  ",value=cfg.get("metric2_label",""),key="a_m2l"); nm2v=st.text_input("Valeur  ",value=cfg.get("metric2_value",""),key="a_m2v"); nm2d=st.text_input("Desc  ",value=cfg.get("metric2_desc",""),key="a_m2d"); st.markdown("**Carte 4**"); nm4l=st.text_input("Label   ",value=cfg.get("metric4_label",""),key="a_m4l"); nm4v=st.text_input("Valeur   ",value=cfg.get("metric4_value",""),key="a_m4v"); nm4d=st.text_input("Desc   ",value=cfg.get("metric4_desc",""),key="a_m4d")

    # --- Experiences (add/remove/reorder) ---
    with at5:
        if st.button("+ Ajouter une experience",key="add_exp"):
            st.session_state.admin_exp.append({"date":"","role":"Nouveau role","company":"Entreprise","desc":"","status":"Terminee"})
            st.session_state.admin_v+=1; st.rerun()
        new_exp=[]; action_exp=None
        for i,e in enumerate(st.session_state.admin_exp):
            # Header row: number + title + move/delete buttons
            st.markdown(f"**{i+1}. {e.get('role','')}** — {e.get('company','')}")
            btn1,btn2,btn3,btn4=st.columns([1,1,1,8])
            with btn1:
                if i>0 and st.button("⬆",key=f"up_e{av}_{i}",use_container_width=True): action_exp=("up",i)
            with btn2:
                if i<len(st.session_state.admin_exp)-1 and st.button("⬇",key=f"dn_e{av}_{i}",use_container_width=True): action_exp=("dn",i)
            with btn3:
                if st.button("🗑",key=f"del_e{av}_{i}",use_container_width=True): action_exp=("del",i)
            # Fields
            fc1,fc2=st.columns([1,3])
            with fc1:
                nd=st.text_input("Date",value=e.get("date",""),key=f"aed{av}_{i}")
                ns=st.selectbox("Statut",["En cours","Terminee"],index=0 if e.get("status")=="En cours" else 1,key=f"aes{av}_{i}")
            with fc2:
                nr=st.text_input("Role",value=e.get("role",""),key=f"aer{av}_{i}")
                nc=st.text_input("Entreprise",value=e.get("company",""),key=f"aec{av}_{i}")
                nde=st.text_input("Description",value=e.get("desc",""),key=f"aede{av}_{i}")
            new_exp.append({"date":nd,"role":nr,"company":nc,"desc":nde,"status":ns})
            st.markdown("---")
        if action_exp:
            # Save current form values into admin list before reordering
            st.session_state.admin_exp=list(new_exp)
            a,idx=action_exp
            if a=="up": swap(st.session_state.admin_exp,idx,idx-1)
            elif a=="dn": swap(st.session_state.admin_exp,idx,idx+1)
            elif a=="del": st.session_state.admin_exp.pop(idx)
            st.session_state.admin_v+=1; st.rerun()

    # --- Case Studies (add/remove/reorder) ---
    with at6:
        st.caption("Impacts et stack separes par virgules.")
        if st.button("+ Ajouter une etude de cas",key="add_cs"):
            st.session_state.admin_cs.append({"title_fr":"Nouveau","title_en":"New","role_fr":"Role","role_en":"Role","period":"2025","challenge_fr":"","challenge_en":"","approach_fr":"","approach_en":"","impact_fr":[],"impact_en":[],"tech":[]})
            st.session_state.admin_v+=1; st.rerun()
        new_cs=[]; action_cs=None
        for i,cs in enumerate(st.session_state.admin_cs):
            st.markdown(f"**{i+1}. {cs.get('title_fr','')}**")
            btn1,btn2,btn3,btn4=st.columns([1,1,1,8])
            with btn1:
                if i>0 and st.button("⬆",key=f"up_c{av}_{i}",use_container_width=True): action_cs=("up",i)
            with btn2:
                if i<len(st.session_state.admin_cs)-1 and st.button("⬇",key=f"dn_c{av}_{i}",use_container_width=True): action_cs=("dn",i)
            with btn3:
                if st.button("🗑",key=f"del_c{av}_{i}",use_container_width=True): action_cs=("del",i)
            cc1,cc2=st.columns(2)
            with cc1:
                st.markdown("**FR**"); cs_tfr=st.text_input("Titre FR",value=cs.get("title_fr",""),key=f"ctfr{av}_{i}"); cs_rfr=st.text_input("Role FR",value=cs.get("role_fr",""),key=f"crfr{av}_{i}"); cs_chfr=st.text_area("Contexte FR",value=cs.get("challenge_fr",""),key=f"cchfr{av}_{i}",height=70); cs_apfr=st.text_area("Approche FR",value=cs.get("approach_fr",""),key=f"capfr{av}_{i}",height=70)
                imp_fr=", ".join(cs.get("impact_fr",[])) if isinstance(cs.get("impact_fr"),list) else ""; cs_impfr=st.text_area("Impacts FR",value=imp_fr,key=f"cifr{av}_{i}",height=50)
            with cc2:
                st.markdown("**EN**"); cs_ten=st.text_input("Title EN",value=cs.get("title_en",""),key=f"cten{av}_{i}"); cs_ren=st.text_input("Role EN",value=cs.get("role_en",""),key=f"cren{av}_{i}"); cs_chen=st.text_area("Challenge EN",value=cs.get("challenge_en",""),key=f"cchen{av}_{i}",height=70); cs_apen=st.text_area("Approach EN",value=cs.get("approach_en",""),key=f"capen{av}_{i}",height=70)
                imp_en=", ".join(cs.get("impact_en",[])) if isinstance(cs.get("impact_en"),list) else ""; cs_impen=st.text_area("Impacts EN",value=imp_en,key=f"cien{av}_{i}",height=50)
            cs_per=st.text_input("Periode",value=cs.get("period",""),key=f"cper{av}_{i}"); cs_tech=st.text_input("Stack",value=", ".join(cs.get("tech",[])) if isinstance(cs.get("tech"),list) else "",key=f"ctech{av}_{i}")
            new_cs.append({"title_fr":cs_tfr,"title_en":cs_ten,"role_fr":cs_rfr,"role_en":cs_ren,"period":cs_per,"challenge_fr":cs_chfr,"challenge_en":cs_chen,"approach_fr":cs_apfr,"approach_en":cs_apen,"impact_fr":[x.strip() for x in cs_impfr.split(",") if x.strip()],"impact_en":[x.strip() for x in cs_impen.split(",") if x.strip()],"tech":[x.strip() for x in cs_tech.split(",") if x.strip()]})
            st.markdown("---")
        if action_cs:
            st.session_state.admin_cs=list(new_cs)
            a,idx=action_cs
            if a=="up": swap(st.session_state.admin_cs,idx,idx-1)
            elif a=="dn": swap(st.session_state.admin_cs,idx,idx+1)
            elif a=="del": st.session_state.admin_cs.pop(idx)
            st.session_state.admin_v+=1; st.rerun()

    with at7:
        pending=[r for r in recos if not r.get("approved")]
        if pending: st.warning(f"{len(pending)} en attente")
        new_recos=[]
        for i,r in enumerate(recos):
            li_icon='🔗' if r.get('linkedin') else ''
            st.markdown(f"**{'✅' if r.get('approved') else '⏳'} {r.get('name','')}** {li_icon}")
            rc1,rc2,rc3=st.columns([2,2,1])
            with rc1: rn=st.text_input("Nom",value=r.get("name",""),key=f"arn{i}"); rt=st.text_input("Poste",value=r.get("title",""),key=f"art{i}"); rli=st.text_input("LinkedIn",value=r.get("linkedin",""),key=f"arli{i}")
            with rc2: rco=st.text_input("Entreprise",value=r.get("company",""),key=f"arco{i}"); rrl=st.selectbox("Relation",["Client","Collegue","Manager","Autre"],index=["Client","Collegue","Manager","Autre"].index(r.get("relation","Autre")) if r.get("relation","Autre") in ["Client","Collegue","Manager","Autre"] else 3,key=f"arrl{i}"); rcp=st.text_input("Periode",value=r.get("collab_period",""),key=f"arcp{i}")
            with rc3: rap=st.checkbox("Approuvee",value=r.get("approved",False),key=f"arap{i}")
            rtx=st.text_area("Texte",value=r.get("text",""),key=f"artx{i}",height=80)
            new_recos.append({"id":r.get("id"),"name":rn,"title":rt,"company":rco,"relation":rrl,"text":rtx,"approved":rap,"date":r.get("date",""),"linkedin":rli,"collab_period":rcp}); st.markdown("---")

    if st.button("Sauvegarder dans Airtable",use_container_width=True,type="primary",key="a_save"):
        nc={"tjm":new_tjm,"disponibilite":new_dispo,"remote":new_remote,"show_tjm":new_show_tjm,"show_phone":new_show_phone,"linkedin":new_linkedin,"email":new_email,"phone":new_phone,"calendly":new_calendly,"hero_name":new_hero_name,"hero_title":new_hero_title,"hero_tagline_fr":new_hero_tl_fr,"hero_tagline_en":new_hero_tl_en,"hero_badges":new_hero_badges,"profil_p1":new_p1,"profil_p2":new_p2,"profil_p3":new_p3,"profil_p4":new_p4,"profil_p1_en":new_p1en,"profil_p2_en":new_p2en,"profil_p3_en":new_p3en,"profil_p4_en":new_p4en,"metric1_label":nm1l,"metric1_value":nm1v,"metric1_desc":nm1d,"metric2_label":nm2l,"metric2_value":nm2v,"metric2_desc":nm2d,"metric3_label":nm3l,"metric3_value":nm3v,"metric3_desc":nm3d,"metric4_label":nm4l,"metric4_value":nm4v,"metric4_desc":nm4d,"exp":new_exp,"case_studies":new_cs,"show_profil":new_show_profil,"show_metrics":new_show_metrics,"show_case_studies":new_show_cs,"show_parcours":new_show_parcours,"show_recos":new_show_recos,"_record_ids":cfg.get("_record_ids",{})}
        save_config(nc); update_all_recos(new_recos); st.session_state.config=nc; st.session_state.recos=new_recos
        st.session_state.admin_exp=new_exp; st.session_state.admin_cs=new_cs
        st.session_state.messages=[{"role":"assistant","content":WELCOME_FR}]
        if "agent_results" in st.session_state: del st.session_state.agent_results
        st.session_state.save_ok=True; st.rerun()
    if st.session_state.get("save_ok"):
        st.toast("Sauvegarde Airtable reussie !", icon="✅")
        del st.session_state.save_ok
    st.stop()

# ================================================================
# PUBLIC SITE
# ================================================================

# LANG TOGGLE
st.markdown('<div class="lang-toggle">',unsafe_allow_html=True)
new_lang=st.radio("lang",["FR","EN"],index=0 if lang=="fr" else 1,horizontal=True,label_visibility="collapsed",key="lang_radio")
st.markdown('</div>',unsafe_allow_html=True)
if (new_lang=="EN" and lang=="fr") or (new_lang=="FR" and lang=="en"):
    st.session_state.lang="en" if new_lang=="EN" else "fr"
    st.session_state.messages=[{"role":"assistant","content":WELCOME_EN if new_lang=="EN" else WELCOME_FR}]
    if "agent_results" in st.session_state: del st.session_state.agent_results
    st.rerun()

# HERO (dynamic from config)
badges_extra=f'<span class="h-badge">{cfg.get("remote","")}</span>'
if cfg.get("show_tjm"): badges_extra+=f'<span class="h-badge">TJM {cfg.get("tjm","")} &euro;</span>'
tagline=cfg.get("hero_tagline_en","") if lang=="en" else cfg.get("hero_tagline_fr","")
hero_name=cfg.get("hero_name","Lionel TCHAMFONG")
hero_title=cfg.get("hero_title","Senior Product Owner")
badges_list=[b.strip() for b in cfg.get("hero_badges","CSPO,CSM,Cloud,Data,GenAI").split(",") if b.strip()]
badges_html="".join(f'<span class="h-badge">{b}</span>' for b in badges_list)
st.markdown(f'<div class="hero-section"><div class="hero-name">{hero_name}</div><div class="hero-title">{hero_title}</div><div class="hero-tagline">{tagline}</div><div class="hero-badges"><span class="h-badge green">{"Available" if lang=="en" else "Disponibilit&eacute;"} : {cfg.get("disponibilite","")}</span>{badges_html}{badges_extra}</div></div>',unsafe_allow_html=True)

# CONTACT
phone_html=f'<a href="tel:{cfg.get("phone","")}">{cfg.get("phone","")}</a>' if cfg.get("show_phone") else ""
cal_btn=f'<a href="{cfg.get("calendly","")}" target="_blank" class="rdv">{"Book a call" if lang=="en" else "Prendre rendez-vous"}</a>' if cfg.get("calendly") else ""
st.markdown(f'<div class="contact-bar"><a href="{cfg.get("linkedin","")}" target="_blank">LinkedIn</a><a href="mailto:{cfg.get("email","")}">{cfg.get("email","")}</a>{phone_html}{cal_btn}</div>',unsafe_allow_html=True)

# METRICS
if cfg.get("show_metrics",True):
    c1,c2,c3,c4=st.columns(4)
    for col,i in zip([c1,c2,c3,c4],[1,2,3,4]):
        with col: st.markdown(f'<div class="m-card"><div class="m-label">{cfg.get(f"metric{i}_label","")}</div><div class="m-value">{cfg.get(f"metric{i}_value","")}</div><div class="m-desc">{cfg.get(f"metric{i}_desc","")}</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

# ============================================================
# MAIN NAVIGATION TABS
# ============================================================
if lang=="en":
    main_tabs=["About me","Ask a question","Matching","Book a call","Recommendations"]
else:
    main_tabs=["Profil","Poser une question","Matching","Rendez-vous","Recommandations"]

# Auto-click tab after rerun
active_tab=st.session_state.pop("active_tab",None)

tab_profil, tab_chat, tab_agent, tab_rdv, tab_recos = st.tabs(main_tabs)

# --- TAB 1 : PROFIL ---
with tab_profil:
    # Profil paragraphs
    if cfg.get("show_profil",True):
        pk="_en" if lang=="en" else ""
        st.markdown(f'<div class="profil-card"><p>{cfg.get(f"profil_p1{pk}","")}</p><p>{cfg.get(f"profil_p2{pk}","")}</p><p>{cfg.get(f"profil_p3{pk}","")}</p><p>{cfg.get(f"profil_p4{pk}","")}</p></div>',unsafe_allow_html=True)

    # Experiences marquantes (case studies)
    if cfg.get("show_case_studies",True):
        cs_list=cfg.get("case_studies",[]); lk="en" if lang=="en" else "fr"
        if not isinstance(cs_list,list): cs_list=[]
        cs_html=""
        for cs in cs_list:
            impacts="".join(f'<div class="cs-impact">{i}</div>' for i in (cs.get(f"impact_{lk}",[]) if isinstance(cs.get(f"impact_{lk}"),list) else []))
            techs="".join(f'<span class="cs-tech">{t}</span>' for t in (cs.get("tech",[]) if isinstance(cs.get("tech"),list) else []))
            cs_html+=f'<div class="cs-card"><div class="cs-title">{cs.get(f"title_{lk}","")}</div><div class="cs-role">{cs.get(f"role_{lk}","")} · <span class="cs-period">{cs.get("period","")}</span></div><div class="cs-section-title">{"Challenge" if lang=="en" else "Contexte"}</div><div class="cs-text">{cs.get(f"challenge_{lk}","")}</div><div class="cs-section-title">{"Approach" if lang=="en" else "Approche"}</div><div class="cs-text">{cs.get(f"approach_{lk}","")}</div><div class="cs-section-title">Impact</div>{impacts}<div class="cs-section-title">Stack</div><div>{techs}</div></div>'
        if cs_html:
            st.markdown(f'<div class="collapse-section"><details open><summary><div class="sec-chevron">{chevron_svg}</div><span class="sec-title">{"Key Projects" if lang=="en" else "Projets Cles"} ({len(cs_list)})</span></summary><div style="padding-top:1.2rem">{cs_html}</div></details></div>',unsafe_allow_html=True)

    # Parcours
    if cfg.get("show_parcours",True):
        exp_list=cfg.get("exp",[]); tl_html=""
        if isinstance(exp_list,list):
            for e in exp_list:
                badge='<span class="exp-badge-on">En cours</span>' if e.get("status")=="En cours" else '<span class="exp-badge-off">Terminee</span>'
                tl_html+=f'<div class="tl-item"><div style="flex:1"><div class="tl-role">{e.get("role","")} {badge}</div><div class="tl-company">{e.get("company","")}</div><div class="tl-desc">{e.get("date","")} · {e.get("desc","")}</div></div></div>'
        if tl_html:
            st.markdown(f'<div class="collapse-section"><details><summary><div class="sec-chevron">{chevron_svg}</div><span class="sec-title">{"Career Path" if lang=="en" else "Parcours professionnel"}</span></summary><div style="padding-top:1.2rem">{tl_html}</div></details></div>',unsafe_allow_html=True)

# --- TAB 2 : CHAT RAG ---
with tab_chat:
    st.markdown(f'<div class="info-box"><div class="info-title">{"Ask me anything about my profile" if lang=="en" else "Posez-moi vos questions sur mon parcours"}</div><div class="info-desc">{"This AI assistant answers based on my real career history, projects and certifications." if lang=="en" else "Cet assistant IA repond en se basant sur mon parcours reel, mes projets et mes certifications."}</div></div>',unsafe_allow_html=True)
    chat_html='<div class="chat-box" id="chat-box">'
    for msg in st.session_state.messages:
        cls=msg["role"]; who="Lionel" if cls=="assistant" else ("You" if lang=="en" else "Vous")
        c=msg["content"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        c=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',c); c=re.sub(r'^#+\s*','',c,flags=re.MULTILINE); c=c.replace("\n","<br>")
        chat_html+=f'<div class="chat-msg {cls}"><div class="msg-who">{who}</div>{c}</div>'
    chat_html+='</div><script>setTimeout(function(){var b=document.getElementById("chat-box");if(b)b.scrollTop=b.scrollHeight;},150);</script>'
    st.markdown(chat_html,unsafe_allow_html=True)
    typed=st.chat_input("Ex: Quelle est son experience AWS ?" if lang=="fr" else "Ex: What is his experience with cloud platforms?")
    if typed:
        st.session_state.messages.append({"role":"user","content":typed})
        try: resp=ask(typed+get_config_context())
        except Exception as e: resp=f"Error: {e}"
        st.session_state.messages.append({"role":"assistant","content":resp}); st.session_state.active_tab=1; st.rerun()

# --- TAB 3 : MATCHING ---
with tab_agent:
    if is_private: st.markdown('<span style="font-family:JetBrains Mono;font-size:.7rem;padding:4px 12px;border-radius:100px;border:1px solid rgba(239,68,68,.3);color:#ef4444;background:rgba(239,68,68,.06)">PRIVATE</span>',unsafe_allow_html=True)
    matching_title = "Profile Matching — How compatible am I with your position?" if lang=="en" else "Matching de profil — Suis-je le bon candidat pour votre poste ?"
    matching_desc = "Copy-paste your job description below. The AI agent will analyze the requirements, compare them with my skills and experience, and generate a compatibility score with key arguments." if lang=="en" else "Copiez-collez votre fiche de poste ci-dessous. L'agent IA va analyser les exigences, les comparer avec mes competences et mon experience, et generer un score de compatibilite avec les arguments cles."
    st.markdown(f'<div class="info-box"><div class="info-title">{matching_title}</div><div class="info-desc">{matching_desc}</div></div>',unsafe_allow_html=True)
    ci,co=st.columns([1,1.5])
    with ci:
        job=st.text_area("x",height=350,placeholder="Paste your full job description here: title, responsibilities, required skills, experience level, tech stack..." if lang=="en" else "Collez ici votre fiche de poste complete : intitule, responsabilites, competences requises, niveau d'experience, stack technique...",key="job_input",label_visibility="collapsed")
        if is_private: rtype=st.radio("Format",["email","pitch"],horizontal=True,key="rtype")
        else: rtype="email"
        run=st.button("Analyze" if lang=="en" else "Analyser",type="primary",use_container_width=True)
    with co:
        if run and job.strip():
            with st.spinner("..."): st.session_state.agent_results=run_agent(job+get_config_context(),rtype)
        if "agent_results" in st.session_state:
            res=st.session_state.agent_results; matching=res.get("matching")
            if matching and not matching.get("error"):
                score=matching.get("score_global",0); sc="low" if score<60 else ("mid" if score<80 else "high")
                st.markdown(f'<div class="score-box {sc}"><div class="score-num">{score}/100</div><div class="score-sub">Match</div></div>',unsafe_allow_html=True)
                if is_private:
                    m1,m2=st.columns(2)
                    with m1:
                        for p in matching.get("points_forts",[]): st.markdown(f'<div class="pt-fort">{p}</div>',unsafe_allow_html=True)
                    with m2:
                        for p in matching.get("points_attention",[]): st.markdown(f'<div class="pt-att">{p}</div>',unsafe_allow_html=True)
                    st.markdown("---"); st.code(res.get("response",""),language=None)
                else:
                    for p in matching.get("points_forts",[]): st.markdown(f'<div class="pt-fort">{p}</div>',unsafe_allow_html=True)
        elif run: st.warning("Please paste a complete job description above." if lang=="en" else "Veuillez coller une fiche de poste complete ci-dessus.")

# --- TAB 4 : RDV ---
with tab_rdv:
    cal=cfg.get("calendly","")
    if cal:
        st.markdown(f'<div class="info-box"><div class="info-title">{"Book a discovery call" if lang=="en" else "Reservez un appel decouverte"}</div><div class="info-desc">{"Pick a time slot that works for you. 30 minutes to discuss your needs and my approach." if lang=="en" else "Choisissez un creneau qui vous convient. 30 minutes pour echanger sur votre besoin et mon approche."}</div></div>',unsafe_allow_html=True)
        components.html(f'<iframe src="{cal}" width="100%" height="680" frameborder="0" style="border-radius:16px;"></iframe>',height=700)

# --- TAB 5 : RECOMMANDATIONS ---
with tab_recos:
    if cfg.get("show_recos",True):
        approved=[r for r in recos if r.get("approved")]
        reco_html=""
        for r in approved:
            li=r.get("linkedin","")
            name_html=f'<a href="{li}" target="_blank" class="reco-name-link">{r["name"]}</a>' if li else f'<span class="reco-name">{r["name"]}</span>'
            verified='<span class="reco-verified">&#10003; Profil verifie</span>' if li else ''
            collab=f'<span class="reco-collab">{r.get("collab_period","")}</span>' if r.get("collab_period") else ""
            reco_html+=f'<div class="reco-card"><div class="reco-text">{r["text"]}</div><div class="reco-author">{name_html}{verified}<span class="reco-relation">{r.get("relation","")}</span><br><span class="reco-info">{r.get("title","")} — {r.get("company","")}</span>{collab}</div></div>'
        if reco_html:
            st.markdown(reco_html,unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="color:#94a3b8;padding:2rem 0">{"No recommendations yet. Be the first!" if lang=="en" else "Aucune recommandation pour le moment. Soyez le premier !"}</p>',unsafe_allow_html=True)

    st.markdown("---")
    with st.form("reco_form",clear_on_submit=True):
        st.markdown(f"**{'Leave a recommendation' if lang=='en' else 'Laisser une recommandation'}**")
        rc1,rc2=st.columns(2)
        with rc1: rf_n=st.text_input("Name" if lang=="en" else "Nom",key="rf_n"); rf_t=st.text_input("Title" if lang=="en" else "Poste",key="rf_t"); rf_li=st.text_input("LinkedIn URL",key="rf_li",placeholder="https://linkedin.com/in/..."); st.caption("💡 Recommended: your LinkedIn profile strengthens your testimonial credibility" if lang=="en" else "💡 Recommande : votre profil LinkedIn renforce la credibilite de votre temoignage")
        with rc2: rf_c=st.text_input("Company" if lang=="en" else "Entreprise",key="rf_c"); rf_r=st.selectbox("Relation",["Client","Collegue","Manager","Autre"],key="rf_r"); rf_cp=st.text_input("Collaboration period" if lang=="en" else "Periode de collaboration",key="rf_cp",placeholder="2023-2024")
        rf_tx=st.text_area("Your recommendation" if lang=="en" else "Votre recommandation",height=80,key="rf_tx")
        submitted=st.form_submit_button("Submit" if lang=="en" else "Envoyer",use_container_width=True)
        if submitted:
            if rf_n and rf_tx:
                add_reco({"name":rf_n,"title":rf_t,"company":rf_c,"relation":rf_r,"text":rf_tx,"linkedin":rf_li,"collab_period":rf_cp,"date":datetime.now().strftime("%Y-%m")})
                st.session_state.reco_submitted=True
                st.session_state.active_tab=4; st.rerun()
            else:
                st.warning("Please fill in your name and recommendation." if lang=="en" else "Veuillez renseigner votre nom et votre recommandation.")
    if st.session_state.get("reco_submitted"):
        st.success("Thank you! Your recommendation has been submitted and will appear after validation." if lang=="en" else "Merci ! Votre recommandation a ete soumise et apparaitra apres validation.")
        del st.session_state.reco_submitted

# AUTO-CLICK TAB after rerun
if active_tab is not None:
    st.markdown(f"""<script>
    function clickTab() {{
        var tabs = document.querySelectorAll('[data-baseweb="tab"]');
        if (tabs.length > {active_tab}) {{ tabs[{active_tab}].click(); }}
        else {{ setTimeout(clickTab, 100); }}
    }}
    setTimeout(clickTab, 300);
    </script>""", unsafe_allow_html=True)

# FOOTER
st.markdown("---")
st.markdown(f'<div class="site-footer"><p><a href="{cfg.get("linkedin","")}" target="_blank">LinkedIn</a> &middot; <a href="mailto:{cfg.get("email","")}">{cfg.get("email","")}</a> &middot; {cfg.get("phone","")}</p><p style="margin-top:.5rem">Lionel TCHAMFONG &copy; 2026</p></div>',unsafe_allow_html=True)

# ADMIN — hidden: only shows if ?admin=1 in URL or via session
query_params = st.query_params
if query_params.get("admin") == "1" or st.session_state.get("show_admin_login"):
    st.session_state.show_admin_login = True
    st.markdown('<div style="max-width:200px;margin:0 auto;opacity:.5">', unsafe_allow_html=True)
    ac = st.text_input("x", type="password", label_visibility="collapsed", placeholder="Code", key="admin_code")
    if ac == PRIVATE_CODE:
        st.session_state.is_private = True; st.session_state.admin_view = True; st.session_state.recos = load_recos()
        st.session_state.pop("admin_exp", None); st.session_state.pop("admin_cs", None); st.session_state.pop("admin_v", None)
        st.session_state.show_admin_login = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
