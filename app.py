import streamlit as st
import requests
from bs4 import BeautifulSoup

# -------------------------
# Load API KEY 
# -------------------------
if "SCRAPER_API_KEY" not in st.secrets:
    st.error("❌ SCRAPER_API_KEY missing! Add it in Streamlit → Settings → Secrets.")
    st.stop()

API_KEY = st.secrets["SCRAPER_API_KEY"]

# -------------------------
# Scraper Function (with API key error detection)
# -------------------------
def scrape_jumia(product_name):
    search = product_name.replace(" ", "+")
    jumia_url = f"https://www.jumia.com.ng/catalog/?q={search}"

    scraper_url = (
        f"http://api.scraperapi.com?"
        f"api_key={API_KEY}&url={jumia_url}&country=ng"
    )

    try:
        response = requests.get(scraper_url, timeout=30)

        # -------------------------
        # API key error handling
        # -------------------------
        text_lower = response.text.lower()
        if response.status_code == 401 or "invalid api key" in text_lower:
            return {"error": "❌ Your API key is invalid or expired. Update it in Streamlit Secrets."}
        if "exceeded" in text_lower or "quota" in text_lower:
            return {"error": "⚠️ Your ScraperAPI monthly quota has been used up. Get a new key."}

        if response.status_code != 200:
            return {"error": f"Failed to reach Jumia (Status {response.status_code}). Try again."}

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("article", class_="prd")

        results = []

        for item in items[:12]:
            title_tag = item.find("h3", class_="name")
            price_tag = item.find("div", class_="prc")
            link_tag = item.find("a")
            img_tag = item.find("img")

            if title_tag and price_tag and link_tag:
                title = title_tag.text.strip()
                price = price_tag.text.strip()

                # Safe link
                href = link_tag.get("href")
                link = "https://www.jumia.com.ng" + href if href else "Link not available"

                # Safe image
                img_url = None
                if img_tag:
                    img_url = img_tag.get("data-src") or img_tag.get("src")
                    if img_url and img_url.startswith("//"):
                        img_url = "https:" + img_url
                img_url = img_url or "https://via.placeholder.com/200?text=No+Image"

                results.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": img_url
                })

        if not results:
            return {"message": "No products found. Try another word."}

        return results

    except Exception as e:
        return {"error": f"❌ Error: {str(e)}"}


# -------------------------
# Streamlit Frontend
# -------------------------
st.set_page_config(page_title="Product Price Scraper", layout="wide")

st.title("🛒 Jumia Price Tracker")
st.caption("Get up-to-date prices, images, and links for your favorite products")

popular_products = [
    "iPhone", "Infinix", "Air Fryer", "Rice Cooker",
    "Refrigerator", "Laptop", "Perfume", "Television",
    "Blender", "Microwave", "Standing Fan"
]

col1, col2 = st.columns([3, 1])

with col1:
    product_input = st.text_input(
        "Enter product name:",
        placeholder="e.g. iPhone 11"
    )

with col2:
    selected_product = st.selectbox("Or choose:", [""] + popular_products)

product = product_input if product_input else selected_product

if st.button("Search"):
    if not product:
        st.warning("Please type or choose a product.")
    else:
        with st.spinner(f"🔄 Searching for {product}..."):
            results = scrape_jumia(product)

        if "error" in results:
            st.error(results["error"])
        elif "message" in results:
            st.warning(results["message"])
        else:
            # Display products in a 3-column grid
            cols = st.columns(3)
            for idx, r in enumerate(results):
                with cols[idx % 3]:
                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #ddd;
                            border-radius:10px;
                            padding:10px;
                            margin-bottom:10px;
                            text-align:center;
                            box-shadow:2px 2px 5px rgba(0,0,0,0.1);
                        ">
                            <img src="{r['image']}" width="150"><br>
                            <b>{r['title']}</b><br>
                            <span style="color:green; font-weight:bold;">
                                {r['price']}
                            </span><br><br>
                            <a href="{r['link']}" target="_blank" style="
                                text-decoration:none;
                                color:white;
                                background-color:#4CAF50;
                                padding:5px 10px;
                                border-radius:5px;
                            ">View Product</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
