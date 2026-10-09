import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# Configuration de la page
st.set_page_config(page_title="✈️ Ryanair Tracker", page_icon="✈️", layout="wide")

st.title("✈️ Suivi des prix Ryanair")

@st.cache_data(ttl=600) # Recharge les données toutes les 10 minutes max
def load_data():
    if not os.path.exists("vols_ryanair.db"):
        return pd.DataFrame()
        
    conn = sqlite3.connect("vols_ryanair.db")
    df = pd.read_sql_query("SELECT * FROM vols", conn)
    conn.close()
    
    if not df.empty:
        df['date_vol'] = pd.to_datetime(df['date_vol'])
        # On ne garde que la requête la plus récente par vol
        df = df.sort_values('heure_requete').drop_duplicates(subset=['date_vol', 'origine', 'numero_vol'], keep='last')
        df = df.sort_values('date_vol')
        
        # --- ASTUCE POUR FORCER LE FRANÇAIS SUR LE CLOUD ---
        # Les serveurs Cloud sont souvent en anglais, on traduit manuellement les jours
        jours_fr = {0: 'Lun', 1: 'Mar', 2: 'Mer', 3: 'Jeu', 4: 'Ven', 5: 'Sam', 6: 'Dim'}
        mois_fr = {1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'}
        
        df['date_francaise'] = (
            df['date_vol'].dt.dayofweek.map(jours_fr) + " " + 
            df['date_vol'].dt.day.astype(str) + " " + 
            df['date_vol'].dt.month.map(mois_fr)
        )
        # ---------------------------------------------------
        
    return df

df = load_data()

if df.empty:
    st.warning("⏳ La base de données est vide ou en cours de mise à jour...")
else:
    # 1. Sélection du Mode (Thibault ou Sofia)
    st.markdown("### 👤 Qui organise son voyage ?")
    mode = st.radio(
        "Choix du profil :", 
        ["👨 Mode Thibault (Départ : Toulouse)", "👩 Mode Sofia (Départ : Séville)"],
        horizontal=True
    )
    
    # 2. Adaptation des libellés (Aller / Retour) selon la personne
    if "Thibault" in mode:
        df['Sens du trajet'] = df.apply(
            lambda r: "✈️ ALLER (Toulouse ➔ Séville)" if r['origine'] == "TLS" else "🛬 RETOUR (Séville ➔ Toulouse)", 
            axis=1
        )
        couleurs = {"✈️ ALLER (Toulouse ➔ Séville)": "#1f77b4", "🛬 RETOUR (Séville ➔ Toulouse)": "#ff7f0e"} # Bleu / Orange
    else:
        df['Sens du trajet'] = df.apply(
            lambda r: "✈️ ALLER (Séville ➔ Toulouse)" if r['origine'] == "SVQ" else "🛬 RETOUR (Toulouse ➔ Séville)", 
            axis=1
        )
        couleurs = {"✈️ ALLER (Séville ➔ Toulouse)": "#e377c2", "🛬 RETOUR (Toulouse ➔ Séville)": "#2ca02c"} # Rose / Vert

    st.divider()

    # 3. Tracé du graphique avec les 2 courbes simultanées
    fig = px.line(
        df, 
        x='date_vol', 
        y='prix', 
        color='Sens du trajet',
        color_discrete_map=couleurs,
        markers=True,
        hover_data={
            "date_vol": False,          # Masque la date brute (2026-11-03)
            "date_francaise": True,     # Affiche la date propre (Mar 3 Nov)
            "horaire_vol": True, 
            "numero_vol": True,
            "prix": ":.0f"              # Affiche sans virgule
        },
        labels={'date_vol': 'Date', 'prix': 'Prix du billet (€)', 'date_francaise': 'Date'}
    )
    
    # Configuration poussée de l'axe X
    fig.update_xaxes(
        dtick="86400000",           # Force l'affichage d'un trait tous les jours (86 400 000 millisecondes)
        tickformat="%a %d %b",      # Formatage du texte de l'axe
        tickangle=-45               # Inclinaison du texte pour éviter le chevauchement
    )
    
    # Ajout d'une ligne de repère visuel
    fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Bon plan < 50€", annotation_position="bottom right")
    
    # Affichage du graphique sur le site
    st.plotly_chart(fig, use_container_width=True)
    
    # 4. Tableau de données formaté sous le graphique
    st.subheader("Détail des vols affichés")
    df_affichage = df[['date_francaise', 'Sens du trajet', 'horaire_vol', 'numero_vol', 'prix']].copy()
    df_affichage.columns = ['Date', 'Trajet', 'Heure', 'N° Vol', 'Prix (€)']
    
    # Affiche un tableau que tu peux trier en cliquant sur les colonnes
    st.dataframe(df_affichage, hide_index=True, use_container_width=True)