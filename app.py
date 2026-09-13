from datetime import datetime
import io
import time
import streamlit as st
from docx import Document
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Konfigurasi Halaman Web App
st.set_page_config(
    page_title="COMMAND CENTER UT", 
    page_icon="⚡", 
    layout="wide"
)

# Custom CSS: Tema "Masculine Tech & Sleek Dark"
st.markdown("""
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');

    <style>
    /* Animasi Latar Belakang Gelap Bergerak Halus */
    @keyframes darkPan {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Animasi Fade In Tajam */
    @keyframes sharpFade {
        0% {opacity: 0; transform: translateY(15px);}
        100% {opacity: 1; transform: translateY(0);}
    }

    /* Terapkan Font Montserrat & Background Dark Slate */
    .stApp {
        background: linear-gradient(-45deg, #09090b, #0f172a, #020617, #082f49);
        background-size: 300% 300%;
        animation: darkPan 15s ease infinite;
        font-family: 'Montserrat', sans-serif !important;
        color: #f1f5f9;
    }
    
    /* Styling Semua Label Teks (Warna abu-abu terang, huruf kapital kecil) */
    label, p, .st-emotion-cache-16idsys p {
        color: #94a3b8 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px;
    }
    
    /* Judul Utama - Gaya Cyberpunk Clean */
    h1 {
        font-weight: 800 !important;
        font-size: 3.2rem !important;
        background: linear-gradient(90deg, #38bdf8 0%, #3b82f6 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: 1px;
        text-transform: uppercase;
        animation: sharpFade 0.6s ease-out forwards;
        margin-bottom: 0 !important;
    }
    
    .subtitle-container {
        text-align: center;
        margin-bottom: 2.5rem;
        animation: sharpFade 0.8s ease-out forwards;
    }
    .subtitle {
        font-size: 1rem;
        font-weight: 600;
        color: #38bdf8 !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        border-bottom: 2px solid #38bdf8;
        display: inline-block;
        padding-bottom: 5px;
    }

    /* Subheader (H3) - Label Bagian */
    h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
        margin-top: 1rem !important;
    }

    /* Tombol Utama (Sleek Tactical Button) */
    .stButton>button {
        background: transparent;
        color: #38bdf8 !important;
        border: 2px solid #38bdf8;
        border-radius: 6px; /* Sudut agak tajam (Maskulin) */
        padding: 0.8rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        width: 100%;
        animation: sharpFade 1s ease-out forwards;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.1);
    }
    .stButton>button:hover {
        background: #38bdf8;
        color: #020617 !important; /* Teks jadi gelap saat di-hover */
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.6);
        transform: translateY(-2px);
    }

    /* Styling Kotak Input (Taktis, Gelap, Garis Nyala) */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        background: rgba(15, 23, 42, 0.7) !important; /* Biru sangat gelap transparan */
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        color: #f8fafc !important;
        border-radius: 6px; /* Sudut taktis */
        padding: 10px;
        transition: all 0.3s ease;
    }
    /* Efek Menyala (Glow) Neon Saat Diklik/Fokus */
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #38bdf8 !important;
        background: rgba(15, 23, 42, 0.9) !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4) !important;
    }
    
    /* Styling Garis Pembatas (Divider) */
    hr {
        border-color: rgba(56, 189, 248, 0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Mengambil API Key dari Brankas (Secrets)
api_key_input = st.secrets["GEMINI_API_KEY"]

# Bagian Judul Tengah 
st.markdown("<h1>COMMAND CENTER UT</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-container'><div class='subtitle'>Sistem Eksekusi Tugas & Diskusi Akademik</div></div>", unsafe_allow_html=True)

# Layout Parameter Pengguna
st.subheader("I. PARAMETER IDENTITAS")
col1, col2 = st.columns(2)
with col1:
  nama_mhs = st.text_input("NAMA OPERATOR / MAHASISWA", placeholder="Aditia Lindra Agasta")
  prodi = st.text_input("DEPARTEMEN / PRODI", placeholder="Ilmu Hukum")
with col2:
  upbjj = st.text_input("STASIUN / UPBJJ", placeholder="UPBJJ Semarang")
  mata_kuliah = st.text_input("SUBJEK MATA KULIAH", placeholder="Pengantar Ilmu Hukum")

st.markdown("---")

# Layout Konfigurasi AI
st.subheader("II. KONFIGURASI ENGINE")
col3, col4, col5, col6 = st.columns(4)
with col3:
  jenis_tugas = st.selectbox("TIPE MISI", ["Diskusi Sesi 1", "Diskusi Sesi 2", "Diskusi Sesi 3", "Diskusi Sesi 4", "Diskusi Sesi 5", "Diskusi Sesi 6", "Diskusi Sesi 7", "Diskusi Sesi 8", "Tugas 1", "Tugas 2", "Tugas 3"])
with col4:
  mode_jawaban = st.selectbox("ALGORITMA", ["Taktis (Standar)", "Analisis Mendalam", "Full Jurnal / BMP"])
with col5:
  gaya_penulisan = st.selectbox("GAYA BAHASA", ["Formal Akademik", "Kritis & Agresif (Gaya Debat)", "Fokus Studi Kasus"])
with col6:
  target_kata = st.selectbox("VOLUME OUTPUT", ["Ringkas (±150 Kata)", "Standar (±300 Kata)", "Maksimal (600+ Kata)"])

st.markdown("---")

st.subheader("III. INPUT DATA MENTAH")
soal_topik = st.text_area("PINDAI SOAL / TOPIK DISKUSI:", placeholder="Tempelkan instruksi soal dari e-learning di sini...", height=120)
uploaded_file = st.file_uploader("UNGGAH DOKUMEN PENDUKUNG (OPSIONAL)", type=["pdf", "png", "jpg", "jpeg"])

st.markdown("<br>", unsafe_allow_html=True)

# Tombol Eksekusi
if st.button("INITIATE GENERATE SEQUENCE", type="primary"):
  if not soal_topik and not uploaded_file:
    st.warning("SYSTEM ERROR: Data input tidak ditemukan. Harap masukkan soal terlebih dahulu.")
  else:
    with st.spinner("MEMPROSES DATA... MENYUSUN REFERENSI... MENGANALISIS..."):
      try:
        client = genai.Client(api_key=api_key_input)
        contents_payload = []
        
        if uploaded_file is not None:
          contents_payload.append({"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()})

        prompt_sistem = f"""
        Anda adalah asisten akademik super cerdas dan profesional untuk mahasiswa Universitas Terbuka. 
        Tugas Anda adalah membuat draf jawaban untuk mata kuliah {mata_kuliah} pada bagian {jenis_tugas}.
        
        ATURAN MUTLAK:
        1. DILARANG KERAS menggunakan emoji pada isi jawaban akademik agar bisa langsung disalin ke web e-learning.
        2. Dilarang menggunakan format bintang (**) berlebihan. Gunakan format paragraf/penomoran yang sangat rapi, lugas, dan tegas.
        3. Gaya penulisan: {gaya_penulisan}. Harus menggunakan bahasa Indonesia formal yang berwibawa, berbobot, analitis, dan khas mahasiswa hukum/akademisi.
        4. WAJIB menyertakan "Sumber Referensi" di bagian paling bawah (Buku Materi Pokok (BMP) {mata_kuliah} dan perundangan terkait).
        5. Mode: {mode_jawaban}, Volume: {target_kata}.
        
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
        
        # Animasi balon ditiadakan agar lebih "macho", diganti loading selesai saja
        time.sleep(0.5)

      except Exception as e:
        st.error(f"SYSTEM FAILURE: {e}")

if "current_result" in st.session_state:
  st.markdown("---")
  st.subheader("IV. TERMINAL OUTPUT (SIAP DISALIN)")
  st.text_area("HASIL ANALISIS:", value=st.session_state.current_result, height=400)

  col_dl1, col_dl2 = st.columns(2)
  with col_dl1:
    doc = Document()
    doc.add_paragraph(st.session_state.current_result)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    st.download_button("DOWNLOAD FORMAT .DOCX (WORD)", data=doc_io, file_name=f"Tugas_{mata_kuliah}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

  with col_dl2:
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    text_object = c.beginText(40, 750)
    text_object.setFont("Helvetica", 10)
    
    # Text Wrapping Otomatis
    from textwrap import wrap
    lines = []
    for line in st.session_state.current_result.split("\n"):
        wrapped = wrap(line, 95)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
            
    for line in lines:
        text_object.textLine(line)
        if text_object.getY() < 50:
            c.drawText(text_object)
            c.showPage()
            text_object = c.beginText(40, 750)
            text_object.setFont("Helvetica", 10)
            
    c.drawText(text_object)
    c.showPage()
    c.save()
    pdf_io.seek(0)
    st.download_button("DOWNLOAD FORMAT .PDF", data=pdf_io, file_name=f"Tugas_{mata_kuliah}.pdf", mime="application/pdf", use_container_width=True)
