import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Configuration de la page web
st.set_page_config(page_title="✈️ Ryanair Tracker", page_icon="✈️", layout="wide")

st.title("✈️ Suivi des prix Ryanair")
st.markdown("**Trajets :** Toulouse (TLS) ↔ Séville (SVQ)")

# Fonction pour charger les données (mise en cache pour accélérer le site)
@st.cache_data(ttl=600) # Se rafraîchit toutes les 10 minutes max
def load_data():
    try:
        conn = sqlite3.connect("vols_ryanair.db")
        df = pd.read_sql_query("SELECT * FROM vols", conn)
        conn.close()
        
        if not df.empty:
            # Nettoyage et formatage
            df['date_vol'] = pd.to_datetime(df['date_vol'])
            # On garde le dernier prix relevé pour chaque vol
            df = df.sort_values('heure_requete').drop_duplicates(subset=['date_vol', 'origine', 'numero_vol'], keep='last')
            df = df.sort_values('date_vol')
            
            # Création du libellé
            df['Trajet'] = df.apply(
                lambda row: "Aller (Toulouse ➔ Séville)" if row['origine'] == "TLS" else "Retour (Séville ➔ Toulouse)", 
                axis=1
            )
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⏳ La base de données est vide ou en cours de mise à jour par le robot...")
else:
    # 1. Menu déroulant pour choisir le sens du trajet
    trajets = df['Trajet'].unique()
    trajet_choisi = st.selectbox("Choisissez le trajet à afficher :", trajets)
    
    df_filtre = df[df['Trajet'] == trajet_choisi]
    
    # 2. Graphique interactif
    fig = px.line(
        df_filtre, x='date_vol', y='prix', markers=True,
        hover_data={"horaire_vol": True, "numero_vol": True, "date_vol": "|%d %b %Y"},
        title=f"Évolution des prix - {trajet_choisi}",
        labels={'date_vol': 'Date du vol', 'prix': 'Prix du billet (€)'}
    )
    # Ligne rouge pointillée à 50€ pour repérer les bons plans
    fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Bon plan < 50€")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Tableau détaillé sous le graphique
    st.subheader("Détail des vols")
    # On affiche un tableau propre
    df_affichage = df_filtre[['date_vol', 'horaire_vol', 'numero_vol', 'prix']].copy()
    df_affichage['date_vol'] = df_affichage['date_vol'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_affichage, hide_index=True, use_container_width=True)