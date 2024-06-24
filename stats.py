import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def generate_statistics():
    st.header("Krankenhausmanagement Dashboard")

    try:
        # Beispiel-Daten laden (ersetzt durch echte Daten)
        data = pd.read_csv('cirs_reports.csv')

        if data.empty:
            st.error("Die Datei 'cirs_reports.csv' ist leer.")
            return

        # Gesamtanzahl der Vorfälle
        total_incidents = len(data)
        st.metric("Gesamtanzahl der Vorfälle", total_incidents)

        # Verteilung nach Abteilungen
        st.subheader("Verteilung nach Abteilungen")
        department_counts = data['Abteilung'].value_counts()
        st.bar_chart(department_counts)

        # Verteilung nach Vorfallarten
        st.subheader("Verteilung nach Vorfallarten")
        incident_type_counts = data['Vorfallart'].value_counts()
        st.bar_chart(incident_type_counts)

        # Schweregrad der Vorfälle
        st.subheader("Schweregrad der Vorfälle")
        severity_counts = data['Schweregrad'].value_counts()
        st.bar_chart(severity_counts)

        # Zeitliche Verteilung
        st.subheader("Zeitliche Verteilung der Vorfälle")
        data['Datum'] = pd.to_datetime(data['Datum'])
        data.set_index('Datum', inplace=True)
        monthly_counts = data.resample('M').size()
        st.line_chart(monthly_counts)

        # Ursachenanalyse
        st.subheader("Ursachenanalyse")
        cause_counts = data['Ursache'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(cause_counts, labels=cause_counts.index, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        st.pyplot(fig)

        # Maßnahmen
        st.subheader("Maßnahmen zur Vermeidung")
        actions_counts = data['Maßnahmen'].value_counts()
        st.bar_chart(actions_counts)

    except FileNotFoundError:
        st.error("Die Datei 'cirs_reports.csv' wurde nicht gefunden.")
    except pd.errors.EmptyDataError:
        st.error("Die Datei 'cirs_reports.csv' ist leer.")
