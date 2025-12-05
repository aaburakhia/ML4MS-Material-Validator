import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from rapidfuzz import process, fuzz
from pymatgen.core import Composition
from langchain_google_genai import ChatGoogleGenerativeAI

# ==========================================
# 1. APP CONFIG
# ==========================================
st.set_page_config(page_title="ML4MS: MaterialValidator Pro", page_icon="🏗️", layout="wide")

@dataclass
class MaterialRecord:
    name: str
    uns: str
    formula: str
    source: str
    confidence: str 

# ==========================================
# 2. DATA LAYER (Connecting to CSV Database)
# ==========================================
@st.cache_data # Caches the data for speed (Professional Optimization)
def load_database():
    try:
        # Connect to the local CSV file (Acting as our SQL Table)
        df = pd.read_csv("materials.csv")
        return df
    except FileNotFoundError:
        st.error("🚨 CRITICAL ERROR: Database file 'materials.csv' not found.")
        return pd.DataFrame() # Return empty if failed

df_materials = load_database()

# ==========================================
# 3. SERVICE LAYER (Logic)
# ==========================================

class MaterialService:
    def __init__(self, api_key):
        self.api_key = api_key
        # Fallback AI (Only used if DB search fails)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", google_api_key=api_key, temperature=0)

    def search_database(self, query: str) -> Optional[MaterialRecord]:
        """Fuzzy Search against the CSV Database"""
        if df_materials.empty: return None

        # Search against Name and UNS columns
        choices = df_materials['Name'].tolist() + df_materials['UNS'].tolist()
        match = process.extractOne(query, choices, scorer=fuzz.WRatio)
        
        if match and match[1] > 85: 
            found_val = match[0]
            # Query the DataFrame (Like an SQL SELECT WHERE)
            record = df_materials[
                (df_materials['Name'] == found_val) | 
                (df_materials['UNS'] == found_val)
            ].iloc[0]
            
            return MaterialRecord(
                name=record['Name'],
                uns=record['UNS'],
                formula=record['Formula'],
                source=f"Internal Database ({record['Standard']})",
                confidence="HIGH"
            )
        return None

    def ask_ai_for_formula(self, query: str) -> MaterialRecord:
        """Fallback: AI Estimation"""
        prompt = f"""
        Act as a Metallurgist. The user asked for '{query}'.
        1. Identify the most likely UNS number and Chemical Formula.
        2. Return ONLY a JSON object. No text.
        Format: {{"name": "Standard Name", "uns": "UNS Code", "formula": "ChemicalString"}}
        """
        try:
            response = self.llm.invoke(prompt)
            import json
            clean_json = response.content.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            return MaterialRecord(
                name=data.get('name', 'Unknown'),
                uns=data.get('uns', 'Unknown'),
                formula=data.get('formula', ''),
                source="AI Estimate (Verify Required)",
                confidence="LOW"
            )
        except:
            return None

class PhysicsEngine:
    @staticmethod
    def calculate_pren(formula: str) -> Dict[str, Any]:
        """Deterministic Physics Calculation (Pymatgen)"""
        try:
            comp = Composition(formula)
            cr = comp.get_wt_fraction("Cr") * 100
            mo = comp.get_wt_fraction("Mo") * 100
            n = comp.get_wt_fraction("N") * 100
            ni = comp.get_wt_fraction("Ni") * 100
            
            pren = cr + (3.3 * mo) + (16 * n)
            
            # NACE MR0175 Logic
            if pren > 40:
                verdict = "PASS (Severe Service)"
                color = "#28a745" # Green
            elif pren > 30:
                verdict = "CONDITIONAL (Mild Service)"
                color = "#ffc107" # Orange
            else:
                verdict = "FAIL (Standard Only)"
                color = "#dc3545" # Red
                
            return {
                "pren": round(pren, 2),
                "breakdown": {"Cr": round(cr,1), "Mo": round(mo,1), "N": round(n,2), "Ni": round(ni,1)},
                "verdict": verdict,
                "color": color,
                "weight": round(comp.weight, 2)
            }
        except Exception as e:
            return {"error": str(e)}

# ==========================================
# 4. PROVENANCE (Audit Trail)
# ==========================================
def generate_audit_trail(record: MaterialRecord, physics_result: Dict):
    timestamp = datetime.now().isoformat()
    raw_data = f"{record.uns}|{record.formula}|{physics_result['pren']}|{timestamp}"
    token = hashlib.sha256(raw_data.encode()).hexdigest()[:12]
    return token, timestamp

# ==========================================
# 5. FRONTEND UI
# ==========================================
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key: st.stop()

material_service = MaterialService(api_key)

if 'material_record' not in st.session_state:
    st.session_state.material_record = None

# Header
st.title("🛡️ NACE Compliance Agent")
st.caption("Architecture: Hybrid RAG (Database + AI Fallback) with Deterministic Physics")

# Search
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Material Database Search", placeholder="Type 'Duplex', 'L80', 'Titanium'...")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_btn = st.button("🔍 Search", type="primary")

if search_btn and query:
    with st.spinner("Searching Internal Database..."):
        result = material_service.search_database(query)
        
        if result:
            st.success(f"Match Found: {result.name}")
            st.session_state.material_record = result
        else:
            with st.spinner("Not found in DB. Asking AI for Estimate..."):
                result = material_service.ask_ai_for_formula(query)
                if result:
                    st.warning("AI Estimation Generated.")
                    st.session_state.material_record = result
                else:
                    st.error("Material not identified.")

# Analysis View
if st.session_state.material_record:
    rec = st.session_state.material_record
    
    st.markdown("---")
    
    # 1. Verification Section
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Material Specification")
        st.info(f"**{rec.name}**\n\nCode: {rec.uns}\n\nStandard: {rec.source}")
    with c2:
        st.subheader("2. Chemical Composition")
        # Human-in-the-Loop: Editable Formula
        confirmed_formula = st.text_input("Verify Formula", rec.formula, help="You can edit this if the MTR differs.")
        
        if st.button("Run Engineering Analysis ⚡"):
            res = PhysicsEngine.calculate_pren(confirmed_formula)
            
            if "error" in res:
                st.error("Invalid Chemical Formula")
            else:
                token, ts = generate_audit_trail(rec, res)
                
                # 3. Results Section
                st.markdown("---")
                st.subheader("3. Engineering Analysis Results")
                
                # Visual Verdict
                st.markdown(f"""
                <div style="background-color:{res['color']}; color:white; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
                    <h2 style="margin:0;">{res['verdict']}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("PREN", res['pren'])
                k2.metric("Chromium", f"{res['breakdown']['Cr']}%")
                k3.metric("Molybdenum", f"{res['breakdown']['Mo']}%")
                k4.metric("Nitrogen", f"{res['breakdown']['N']}%")
                
                # Audit Footer
                st.caption(f"🔒 Provenance Hash: {token} | 🕒 Timestamp: {ts}")
                with st.expander("View JSON Output"):
                    st.json(res)