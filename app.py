import streamlit as st
from anonymize import anonymize_cirs_report, detect_names_and_location
from stats import generate_statistics
import matplotlib.pyplot as plt

def main():
    st.title("MediGuard - CIRS Bericht Anonymisierung und Auswertung")

    if 'step' not in st.session_state:
        st.session_state.step = 1

    if st.session_state.step == 1:
        initial_input()
    elif st.session_state.step == 2:
        clean_report()
    elif st.session_state.step == 3:
        verify_details()
    elif st.session_state.step == 4:
        cirs_matrix()
    elif st.session_state.step == 5:
        show_cirs_matrix()
    elif st.session_state.step == 6:
        feedback()
    elif st.session_state.step == 7:
        dashboard()

def initial_input():
    st.header("Durch Teilen von Vorfällen können zukünftige Vorfälle verhindert werden!")
    st.subheader("Was war los?")
    st.session_state.full_report = st.text_area("Beschreiben Sie den Vorfall:", st.session_state.get('full_report', ''))
    if st.button("Bericht anonymisieren"):
        if st.session_state.full_report:
            try:
                names, location = detect_names_and_location(st.session_state.full_report)
                st.session_state.names = names
                st.session_state.location = location
                st.session_state.anonymized_report, details, cirs_details = anonymize_cirs_report(st.session_state.full_report)
                st.session_state.details = details
                st.session_state.cirs_details = cirs_details
                st.success("Bericht wurde anonymisiert!")
                st.session_state.step += 1
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Fehler bei der Anonymisierung: {str(e)}")
        else:
            st.error("Bitte geben Sie den vollständigen CIRS Bericht ein.")

def clean_report():
    st.header("Clean Bericht")
    st.write(st.session_state.anonymized_report)

    if st.session_state.names:
        st.subheader("Erkannte Namen")
        for name in st.session_state.names:
            st.write(f"Welche Bezeichnung beschreibt {name} am besten?")
            role = st.radio(f"Rolle von {name}", ("Pflegekraft", "Person", "Patient", "Arzt/Ärztin"), key=name)
            st.session_state[f"{name}_role"] = role

    if st.button("Weiter"):
        st.session_state.step += 1
        st.experimental_rerun()

def verify_details():
    st.header("Überprüfung der extrahierten Details")
    details = st.session_state.details

    st.subheader("Ort des Vorfalls")
    st.session_state.location = st.text_area("Ort:", details.get('ort', st.session_state.location))

    st.subheader("Wann war das Ereignis?")
    st.session_state.time_of_day = st.selectbox("Tageszeit:", ["Tag", "Nacht"], index=["Tag", "Nacht"].index(details.get('tageszeit', 'Tag') if 'tageszeit' in details else 'Tag'))
    st.session_state.day_of_week = st.selectbox("Tag:", ["Wochentag", "Wochenende"], index=["Wochentag", "Wochenende"].index(details.get('tag', 'Wochentag') if 'tag' in details else 'Wochentag'))
    st.session_state.operating_mode = st.selectbox("Betriebsmodus:", ["Routine", "Bereitschaft", "Schicht"], index=["Routine", "Bereitschaft", "Schicht"].index(details.get('betriebsmodus', 'Routine') if 'betriebsmodus' in details else 'Routine'))

    if st.button("Bestätigen und weiter zur CIRS-Matrix"):
        st.session_state.step += 1
        st.experimental_rerun()

def cirs_matrix():
    st.header("CIRS-Matrix Zuordnung")
    
    schaden_options = ["katastrophal", "schwer", "moderat/mäßig", "minimal/gering", "keine/vernachlässigbar"]
    wahrscheinlichkeits_options = ["selten (< als alle 1-2 Jahre)", "unwahrscheinlich (einmal/Jahr)", "denkbar (monatlich)", "wahrscheinlich (wöchentlich)", "fast sicher (täglich)"]

    schaden = st.session_state.cirs_details.get("schaden", "")
    wahrscheinlichkeiten = st.session_state.cirs_details.get("wahrscheinlichkeit", "")

    st.session_state.schaden = st.selectbox("Schadensausmaß:", schaden_options, index=schaden_options.index(schaden) if schaden in schaden_options else 0)
    st.session_state.wahrscheinlichkeit = st.selectbox("Auftretenswahrscheinlichkeit:", wahrscheinlichkeits_options, index=wahrscheinlichkeits_options.index(wahrscheinlichkeiten) if wahrscheinlichkeiten in wahrscheinlichkeits_options else 0)

    if st.button("CIRS-Matrix anzeigen"):
        st.session_state.step += 1
        st.experimental_rerun()

def show_cirs_matrix():
    st.header("CIRS-Matrix")

    schaden_mapping = {"katastrophal": 5, "schwer": 4, "moderat/mäßig": 3, "minimal/gering": 2, "keine/vernachlässigbar": 1}
    wahrscheinlichkeits_mapping = {"selten (< als alle 1-2 Jahre)": 1, "unwahrscheinlich (einmal/Jahr)": 2, "denkbar (monatlich)": 3, "wahrscheinlich (wöchentlich)": 4, "fast sicher (täglich)": 5}

    schaden_stufe = schaden_mapping[st.session_state.schaden]
    wahrscheinlichkeits_stufe = wahrscheinlichkeits_mapping[st.session_state.wahrscheinlichkeit]

    fig, ax = plt.subplots()
    ax.set_title('CIRS-Matrix')

    # Plot the grid
    for x in range(6):
        for y in range(6):
            ax.add_patch(plt.Rectangle((x, y), 1, 1, fill=None, edgecolor='black'))

    # Highlight the selected cell
    ax.add_patch(plt.Rectangle((wahrscheinlichkeits_stufe - 1, schaden_stufe - 1), 1, 1, fill=True, edgecolor='red', facecolor='red', alpha=0.3))

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_xticks(range(6))
    ax.set_yticks(range(6))
    ax.set_xticklabels(["", "1", "2", "3", "4", "5"])
    ax.set_yticklabels(["", "keine", "minimal", "moderat", "schwer", "katastrophal"])

    st.pyplot(fig)

    if st.button("Feedback geben"):
        st.session_state.step += 1
        st.experimental_rerun()

def feedback():
    st.header("Feedback zur KI-generierten Auswertung")
    st.text_area("Bitte geben Sie Ihr Feedback ein:", key='feedback')
    if st.button("Feedback absenden"):
        st.success("Vielen Dank für Ihr Feedback!")
        st.session_state.step += 1
        st.experimental_rerun()

def dashboard():
    st.header("Krankenhausmanagement Dashboard")
    generate_statistics()
    if st.button("Neuen Bericht erstellen"):
        st.session_state.step = 1
        st.experimental_rerun()

if __name__ == "__main__":
    main()
