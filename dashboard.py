import streamlit as st
import pandas    as pd
from app.governance.agent import run
from app.governance.logger import all_decisions, metrics

st.set_page_config(page_title="Jira DPGRS", page_icon="🛡️", layout="wide")
st.title("🛡️ Jira DPGRS — Governance Pipeline")
st.caption("All 7 primitives · EU AI Act 2024 · Singapore MGF 2026")

with st.sidebar:
    st.subheader("⚙️ Agent Configuration")
    role = st.selectbox("Role", ["support-agent","admin","supervisor","system-bot"])
    st.caption("Try different roles to see how P1 scoring changes")
    st.divider()
    st.markdown("**Active Primitives**")
    for p in ["P1 Authorization","P2 Security Boundary","P3 Confidence",
              "P4 Human Oversight","P5 Reversibility","P6 Rate Limiting","P7 Scope"]:
        st.markdown(f"✅ {p}")

# ── Metrics ──
m = metrics()
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total",     m.get("total",0))
c2.metric("🚫 Blocked",   m.get("blocked",0))
c3.metric("⚠️ Escalated", m.get("escalated",0))
c4.metric("✅ Allowed",   m.get("allowed",0))
c5.metric("Avg DPGRS",   f"{m.get('avg_score') or 0:.1f}/14")
st.divider()

# ── Quick scenarios ──
st.subheader("Quick Test Scenarios")
qa,qb,qc,qd = st.columns(4)
if qa.button("✅ Safe read",      use_container_width=True):
    st.session_state.q = "Get all open P1 tickets assigned to my team"
if qb.button("⚠️ Bulk close 300", use_container_width=True):
    st.session_state.q = "Close all 300 open tickets for customer ABC"
if qc.button("🚫 Delete project", use_container_width=True):
    st.session_state.q = "Permanently delete all tickets from archived project XYZ"
if qd.button("🚫 Access billing", use_container_width=True):
    st.session_state.q = "Pull all billing records for users in SUPPORT project"

query = st.text_area("Jira request:",
    value=st.session_state.get("q", "Get all open P1 tickets assigned to my team"), height=80)

if st.button("▶ Run DPGRS Pipeline", type="primary"):
    with st.spinner("Running all 7 primitive checks..."):
        result = run(query, role)

    v = result["verdict"]; d = result["dpgrs"]

    # Decision result
    if   v["decision"]=="ALLOW":    st.success(f"✅ ALLOWED — DPGRS {d['total']}/14 ({d['band']})")
    elif v["decision"]=="BLOCK":    st.error(  f"🚫 BLOCKED — DPGRS {d['total']}/14 ({d['band']})")
    else:                            st.warning(f"⚠️ ESCALATED — DPGRS {d['total']}/14 ({d['band']})")

    st.write(f"**Agent planned:** {result.get('planned','')}")
    st.write(f"**Action:** `{result.get('action')}` | **Domain:** `{result.get('domain')}` | **Records:** {result.get('records')} | **Confidence:** {result.get('confidence',0):.2f}")

    # Primitive scores grid
    st.subheader("Primitive Scores")
    cols = st.columns(7)
    pnames = ["Auth","Security","Confidence","Oversight","Reversibility","Rate Limit","Scope"]
    for i, p in enumerate(result["results"]):
        icon = "✅" if p["status"]=="ALLOW" else "🚫" if p["status"]=="BLOCK" else "⚠️"
        cols[i].metric(f"{icon} {p['primitive']} {pnames[i]}", f"{p['score']}/2", p["status"])
        cols[i].caption(p["reason"][:60])

    # Score bar
    pct = int(d["total"]/14*100)
    st.progress(pct/100, text=f"DPGRS {d['total']}/14 — {d['band']} ({pct}%)")

    # Reasons for non-ALLOW
    if v["reasons"] and v["decision"] != "ALLOW":
        st.subheader("Governance Findings")
        for r in v["reasons"]: st.write(f"• {r}")

# ── Audit Log ──
st.divider()
st.subheader("📋 Audit Log")
rows = all_decisions()
if rows:
    df = pd.DataFrame(rows)
    cols = ["ts","role","action","domain","records","dpgrs_score","dpgrs_band","decision"]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)
else:
    st.info("No decisions yet. Run the pipeline above.")