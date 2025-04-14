import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import pgeocode

# Page setup
st.set_page_config(page_title="Donor Demographics Dashboard", layout="wide", page_icon="🌍")
st.title("🌍 Donor Demographics Dashboard")

# Style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Nunito Sans', sans-serif;
        background-color: #ffffff;
        color: #1F3C4C !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
# Load data  
if 'donor_data' not in st.session_state:
    st.warning("Please upload a donation file on the Home page first.")
    st.stop()
else:
    st.success("✅ Data loaded!")
    st.sidebar.markdown("### 📂 Files Processed:")
    for fname in st.session_state['uploaded_file_names']:
        st.sidebar.markdown(f"• `{fname}`")
        
df = st.session_state['donor_data'].copy()
df = df.dropna(subset=['Donation Amount'])

# ----- Donor Type Pie Chart -----
st.subheader("🧑‍🤝‍🧑 Donor Type Distribution")

if 'Donor Type' in df.columns:
    type_counts = df['Donor Type'].value_counts().reset_index()
    type_counts.columns = ['Donor Type', 'Count']

    type_pie = alt.Chart(type_counts).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Count", type="quantitative"),
        color=alt.Color(field="Donor Type", type="nominal"),
        tooltip=['Donor Type', 'Count']
    ).properties(height=300)

    st.altair_chart(type_pie.configure_legend(labelColor='#1F3C4C'), use_container_width=True)

# ----- ZIP Code Analytics -----
st.subheader("📍 ZIP Code-Based Donation Insights")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 💵 Top ZIP Codes by Donation Amount")
    if 'ZIP' in df.columns:
        df['ZIP'] = df['ZIP'].astype(str).str.zfill(5)
        zip_df = df.groupby('ZIP')['Donation Amount'].sum().reset_index()
        zip_df = zip_df.sort_values(by='Donation Amount', ascending=False).head(20)

        bar = alt.Chart(zip_df).mark_bar().encode(
            y=alt.Y('ZIP:N', sort='-x'),
            x=alt.X('Donation Amount:Q'),
            tooltip=['ZIP', 'Donation Amount']
        ).properties(height=400)

        st.altair_chart(bar, use_container_width=True)
    else:
        st.warning("ZIP column not found in data.")

with col2:
    st.markdown("#### 🗺️ Geographic Distribution of Donations")

    if 'ZIP' in df.columns:
        df['ZIP'] = df['ZIP'].astype(str).str.zfill(5)
        nomi = pgeocode.Nominatim('us')
        zip_list = df['ZIP'].unique()

        geo_data = pd.DataFrame([nomi.query_postal_code(z) for z in zip_list])
        geo_data = geo_data[['postal_code', 'latitude', 'longitude']].dropna()
        geo_data.columns = ['ZIP', 'Latitude', 'Longitude']
        geo_data['ZIP'] = geo_data['ZIP'].astype(str).str.zfill(5)

        donation_by_zip = df.groupby('ZIP')['Donation Amount'].sum().reset_index()
        geo_df = pd.merge(donation_by_zip, geo_data, on='ZIP', how='inner')

        fig = px.scatter_geo(
            geo_df,
            lat='Latitude',
            lon='Longitude',
            scope="usa",
            color='Donation Amount',
            hover_name='ZIP',
            size='Donation Amount',
            color_continuous_scale='Oranges',
        )

        fig.update_layout(height=400, margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ZIP code data not available.")
