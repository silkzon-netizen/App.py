import streamlit as st
import requests
import json
import pandas as pd
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Silkzon Store Assistant",
    page_icon="🛍️",
    layout="wide"
)

# Sidebar Configuration
st.sidebar.title("⚙️ Store Setup")
store_url = st.sidebar.text_input("Shopify Store URL", value="silkzon.in.myshopify.com")
api_version = st.sidebar.selectbox("API Version", ["2024-07", "2024-10", "2025-01"])
access_token = st.sidebar.text_input("Admin API Access Token", type="password")
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

def get_shopify_headers():
    return {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }

def get_gemini_client():
    if gemini_api_key:
        return genai.Client(api_key=gemini_api_key)
    return None

st.title("🛍️ Silkzon Shopify & Marketing Engine")

tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Products & Pricing", 
    "🎨 Liquid & Theme AI", 
    "📢 Google & Meta Ads", 
    "📊 Quick Store Check"
])

# TAB 1: Bulk Products & Price Update
with tab1:
    st.subheader("Bulk Product & Price Manager")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Fetch Latest Products"):
            if not store_url or not access_token:
                st.error("Store URL aur Access Token sidebar me dalein.")
            else:
                endpoint = f"https://{store_url}/admin/api/{api_version}/products.json?limit=50"
                try:
                    res = requests.get(endpoint, headers=get_shopify_headers())
                    if res.status_code == 200:
                        products = res.json().get("products", [])
                        prod_list = []
                        for p in products:
                            for v in p.get("variants", []):
                                prod_list.append({
                                    "Product ID": p["id"],
                                    "Variant ID": v["id"],
                                    "Title": p["title"],
                                    "SKU": v.get("sku", ""),
                                    "Price (₹)": v.get("price", "0"),
                                    "Inventory": v.get("inventory_quantity", 0)
                                })
                        st.session_state["products_df"] = pd.DataFrame(prod_list)
                        st.success(f"{len(prod_list)} items load ho gaye!")
                    else:
                        st.error(f"Error: {res.status_code} - {res.text}")
                except Exception as e:
                    st.error(f"Failed to fetch: {e}")

    if "products_df" in st.session_state:
        st.dataframe(st.session_state["products_df"], use_container_width=True)
        
        st.write("### Bulk Price Update")
        col_a, col_b = st.columns(2)
        with col_a:
            target_variant = st.text_input("Variant ID to Update")
        with col_b:
            new_price = st.text_input("New Price (₹)")
            
        if st.button("Update Price Now"):
            if target_variant and new_price:
                update_url = f"https://{store_url}/admin/api/{api_version}/variants/{target_variant}.json"
                payload = {"variant": {"id": int(target_variant), "price": str(new_price)}}
                res = requests.put(update_url, headers=get_shopify_headers(), json=payload)
                if res.status_code == 200:
                    st.success("Price successfully update ho gaya!")
                else:
                    st.error(f"Failed: {res.text}")

# TAB 2: AI Liquid & Theme Code Generator
with tab2:
    st.subheader("Gemini Liquid Theme Assistant")
    liquid_prompt = st.text_area(
        "Aap theme me kya feature ya design banana chahte hain?",
        placeholder="Jaise: Create a high-converting announcement bar with marquee effect and countdown timer for silk saree sale in pure Liquid and CSS."
    )
    if st.button("✨ Generate Liquid Code"):
        client = get_gemini_client()
        if not client:
            st.error("Sidebar me Gemini API Key dalein.")
        elif not liquid_prompt:
            st.warning("Pehle prompt likhein.")
        else:
            with st.spinner("Generating code with Gemini 2.5 Flash..."):
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"You are an expert Shopify Liquid developer. Generate clean, copy-paste ready Liquid, HTML, and CSS for this requirement: {liquid_prompt}. Return code with concise instructions on which file to paste it in."
                )
                st.code(response.text, language="html")

# TAB 3: AI Ads Campaign Generator
with tab3:
    st.subheader("Google & Instagram Ad Copy Engine")
    item_title = st.text_input("Product or Collection Name", value="Tussar Silk Sarees")
    usp = st.text_area("Key Features / USPs", value="Pure handloom, festive discounts, pan-India free shipping, COD available")
    
    if st.button("🚀 Generate High-ROI Ad Copies"):
        client = get_gemini_client()
        if not client:
            st.error("Sidebar me Gemini API Key dalein.")
        else:
            with st.spinner("Generating compelling ad creatives..."):
                ad_prompt = f"""
                Create high-performing e-commerce ad copies for an apparel brand:
                Product: {item_title}
                USPs: {usp}
                
                Deliver:
                1. 3 Instagram Ad Hooks + Captions + Hashtags (Hinglish/English conversational).
                2. 3 Google Search Ad Headlines (Under 30 chars) and 2 Descriptions (Under 90 chars).
                3. High-converting CTA buttons.
                """
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=ad_prompt
                )
                st.markdown(res.text)

# TAB 4: Quick Connection Verification
with tab4:
    st.subheader("Verify Store & API Connection")
    if st.button("Check Connectivity"):
        if not store_url or not access_token:
            st.warning("Store URL aur Access Token verify karne ke liye dono daalna zaroori hai.")
        else:
            test_endpoint = f"https://{store_url}/admin/api/{api_version}/shop.json"
            try:
                res = requests.get(test_endpoint, headers=get_shopify_headers())
                if res.status_code == 200:
                    shop_data = res.json().get("shop", {})
                    st.success(f"Connected to: {shop_data.get('name')} ({shop_data.get('domain')})")
                    st.json(shop_data)
                else:
                    st.error(f"Shopify Error ({res.status_code}): {res.text}")
            except Exception as ex:
                st.error(f"Connection test failed: {ex}")
