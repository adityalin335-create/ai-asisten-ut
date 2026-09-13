from datetime import datetime
import io
import time
import streamlit as st
from docx import Document
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Konfigurasi Halaman Web App (Wajib paling atas)
st.set_page_config(
    page_title="AI Asisten Diskusi & Tugas UT", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS TINGKAT TINGGI (Futuristic Animated UI)
st.markdown("""
    <style>
    /* Animasi Latar Belakang Bergerak */
    @keyframes gradientBG {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Animasi Elemen Muncul */
    @keyframes fadeInUp {
        from {opacity: 0; transform: translateY(30px);}
        to {opacity: 1; transform: translateY(0);}
    }

    /* Terapkan Latar Belakang ke Seluruh Aplikasi */
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e1b4b, #000000, #172554);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Warna Teks Global */
    h1, h2, h3, p, label {
        color: #ffffff !important;
        animation: fadeInUp 0.8s ease-out forwards;
    }
    
    h1 {
        font-size: 3rem !important;
        background: -webkit-linear-gradient(45deg, #3b82f6, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 20px rgba(168, 85, 247, 0.4);
    }

    /* Efek Kaca (Glassmorphism) untuk Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Glowing Button (Tombol Menyala) */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.4s ease;
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.5);
        animation: fadeInUp 1s ease-out forwards;
    }
    .stButton>button:hover {
        transform: scale(1.02) translateY(-3px);
        box-shadow: 0 0 30px rgba(124, 58, 237, 0.9);
        border: 1px solid rgba(255,255,255,0.6);
    }

    /* Styling Kotak Input */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
        border-radius: 10px;
        transition: all 0.3s;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.5) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Mengambil API Key dari Brankas (Secrets)
api_key_input = st.secrets["GEMINI_API_KEY"]

# Inisialisasi Session State
if "history" not in st.session_state:
  st.session_state.history = []

st.title("AI ASISTEN DISKUSI & TUGAS")
st.markdown("🚀 **Sistem Pemrosesan Bahasa Akademik Terintegrasi** - Universitas Terbuka")
st.markdown("---")

with st.sidebar:
  st.header("📂 LOG RIWAYAT SESI")
  if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
      with st.expander(f"Data: {item['matkul']} ({item['jenis']})"):
        st.caption(f"Timestamp: {item['waktu']}")
        if st.button("Muat Data", key=f"hist_{i}"):
          st.session_state.current_result = item["teks"]
  else:
    st.info("Log sistem masih kosong.")

st.subheader("1. PARAMETER PENGGUNA")
col1, col2 = st.columns(2)
with col1:
  nama_mhs = st.text_input("Nama Pengguna", placeholder="Aditia Lindra Agasta")
  prodi = st.text_input("Departemen/Prodi", placeholder="Ilmu Hukum")
with col2:
  upbjj = st.text_input("Region/UPBJJ", placeholder="UPBJJ-UT")
  nama_tutor = st.text_input("Tutor Target (Opsional)", placeholder="Nama Tutor")

st.markdown("---")

st.subheader("2. KONFIGURASI ENGINE AI")
col3, col4, col5 = st.columns(3)
with col3:
  jenis_tugas = st.selectbox(
      "Tipe Tugas",
      ["Diskusi Sesi 1", "Diskusi Sesi 2", "Diskusi Sesi 3", "Diskusi Sesi 4", "Diskusi Sesi 5", "Diskusi Sesi 6", "Diskusi Sesi 7", "Diskusi Sesi 8", "Tugas 1", "Tugas 2", "Tugas 3"],
  )
  mata_kuliah = st.text_input("Subjek Mata Kuliah", placeholder="Contoh: Pengantar Ilmu Hukum")
with col4:
  mode_jawaban = st.selectbox("Algoritma Jawaban", ["Standar", "Analisis Komprehensif", "Studi Literatur BMP"])
  gaya_penulisan = st.selectbox("Gaya Bahasa", ["Akademik Natural", "Kritis Mendalam", "Praktis & Kasus"])
with col5:
  target_kata = st.selectbox("Volume Output", ["Pendek (±150 kata)", "Menengah (±300 kata)", "Maksimal (600+ kata)"])

st.markdown("---")

st.subheader("3. INPUT DATA MENTAH")
soal_topik = st.text_area("Pindai Pertanyaan Topik:", placeholder="Tempelkan soal diskusi atau tugas di sini...", height=120)
uploaded_file = st.file_uploader("Upload Dokumen Pendukung (Opsional)", type=["pdf", "png", "jpg", "jpeg"])
st.markdown("---")

# Tombol Eksekusi dengan Animasi
if st.button("⚡ GENERATE DRAF AKADEMIK SEKARANG", type="primary"):
  if not soal_topik and not uploaded_file:
    st.warning("ERROR: Input data mentah tidak ditemukan.")
  else:
    with st.spinner("🤖 Mengkalibrasi data... Menyusun referensi BMP... Menganalisis..."):
      try:
        client = genai.Client(api_key=api_key_input)
        contents_payload = []
        
        if uploaded_file is not None:
          contents_payload.append({"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()})

        prompt_sistem = f"""
        Anda adalah asisten akademik cerdas untuk mahasiswa Universitas Terbuka. 
        Tugas Anda adalah membuat draf jawaban untuk mata kuliah {mata_kuliah} pada bagian {jenis_tugas}.
        
        ATURAN MUTLAK:
        1. DILARANG KERAS menggunakan emoji atau format bintang (**) berlebihan. Gunakan teks paragraf/penomoran rapi.
        2. Gaya penulisan harus natural mahasiswa UT, tata bahasa formal, analitis, mendalam.
        3. WAJIB menyertakan "Sumber Referensi" di bagian paling bawah (Buku Materi Pokok (BMP) {mata_kuliah} dan perundangan terkait).
        4. Mode: {mode_jawaban}, Gaya: {gaya_penulisan}, Volume: {target_kata}.
        
        Soal:
        {soal_topik}
        """
        
        contents_payload.append(prompt_sistem)
        response = client.models.generate_content(model="gemini-3.6-flash", contents=contents_payload)

        header_identitas = (
            f"NAMA : {nama_mhs if nama_mhs else '[Nama Mahasiswa]'}\n"
            f"NIM / PRODI : {prodi if prodi else '[Program Studi]'}\n"
            f"UPBJJ-UT : {upbjj if upbjj else '[UPBJJ]'}\n"
            f"MATA KULIAH : {mata_kuliah if mata_kuliah else '[Mata Kuliah]'}\n"
            f"KEGIATAN : {jenis_tugas}\n"
            f"{'='*50}\n\n"
        )

        st.session_state.current_result = header_identitas + response.text
        st.session_state.history.append({"matkul": mata_kuliah, "jenis": jenis_tugas, "teks": st.session_state.current_result, "waktu": datetime.now().strftime("%Y-%m-%d %H:%M")})
        
        # Animasi native Streamlit saat sukses!
        st.balloons()
        time.sleep(1)

      except Exception as e:
        st.error(f"SYSTEM FAILURE: {e}")

if "current_result" in st.session_state:
  st.markdown("---")
  st.subheader("TERMINAL OUTPUT: SIAP DISALIN")
  st.text_area("Pratinjau Hasil Generate:", value=st.session_state.current_result, height=400)

  col_dl1, col_dl2 = st.columns(2)
  with col_dl1:
    doc = Document()
    doc.add_paragraph(st.session_state.current_result)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    st.download_button("💾 EXPORT TO WORD", data=doc_io, file_name=f"Tugas_{mata_kuliah}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

  with col_dl2:
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    text_object = c.beginText(40, 750)
    text_object.setFont("Helvetica", 10)
    for line in st.session_state.current_result.split("\n"):
      text_object.textLine(line)
    c.drawText(text_object)
    c.showPage()
    c.save()
    pdf_io.seek(0)
    st.download_button("💾 EXPORT TO PDF", data=pdf_io, file_name=f"Tugas_{mata_kuliah}.pdf", mime="application/pdf")
