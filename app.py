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
    page_title="AI Asisten UT", 
    page_icon="🎓", 
    layout="wide"
)

# Custom CSS: Tema "Clean Modern SaaS" (Sesuai Referensi UI/UX)
st.markdown("""
    <style>
    /* Mengimpor font Inter ke dalam blok CSS agar tidak bocor ke layar */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Latar Belakang Gradasi Soft (Peach ke Light Blue) */
    .stApp {
        background: linear-gradient(135deg, #fff3e0 0%, #f3e8ff 50%, #e0f2fe 100%);
        font-family: 'Inter', sans-serif !important;
        color: #1e293b;
    }
    
    /* Warna Teks Global */
    h1, h2, h3, p, label, .st-emotion-cache-16idsys p {
        color: #334155 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Judul Utama */
    h1 {
        font-weight: 700 !important;
        font-size: 2.8rem !important;
        color: #0f172a !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        font-weight: 500;
        color: #64748b !important;
        margin-bottom: 3rem;
    }

    /* Styling Subheader */
    h3 {
        font-weight: 600 !important;
        color: #1e293b !important;
        font-size: 1.2rem !important;
        margin-top: 1rem !important;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 8px;
    }

    /* Tombol Utama (Solid Blue, Clean) */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        width: 100%;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3) !important;
    }

    /* Styling Kotak Input (Putih Bersih, Border Halus) */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        padding: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* Efek Saat Kotak Input Diklik (Focus) - Garis Biru */
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stTextArea>div>div>textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
        outline: none !important;
    }

    /* Styling Kotak Upload File (Dropzone) */
    [data-testid="stFileUploadDropzone"] {
        background-color: #ffffff !important;
        border: 2px dashed #94a3b8 !important;
        border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Mengambil API Key dari Brankas (Secrets)
api_key_input = st.secrets["GEMINI_API_KEY"]

# Header
st.title("AI Asisten Akademik UT")
st.markdown("<div class='subtitle'>Sistem perumusan draf tugas & diskusi forum terstruktur</div>", unsafe_allow_html=True)

# Layout Form
st.subheader("Informasi Mahasiswa")
col1, col2 = st.columns(2)
with col1:
  nama_mhs = st.text_input("Nama Lengkap", placeholder="Contoh: Aditia Lindra Agasta")
  prodi = st.text_input("Program Studi", placeholder="Contoh: Ilmu Hukum")
with col2:
  upbjj = st.text_input("Asal UPBJJ", placeholder="Contoh: UPBJJ Semarang")
  mata_kuliah = st.text_input("Mata Kuliah", placeholder="Contoh: Pengantar Ilmu Hukum")

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("Pengaturan Draf Jawaban")
col3, col4, col5, col6 = st.columns(4)
with col3:
  jenis_tugas = st.selectbox("Jenis Kegiatan", ["Diskusi Sesi 1", "Diskusi Sesi 2", "Diskusi Sesi 3", "Diskusi Sesi 4", "Diskusi Sesi 5", "Diskusi Sesi 6", "Diskusi Sesi 7", "Diskusi Sesi 8", "Tugas 1", "Tugas 2", "Tugas 3"])
with col4:
  mode_jawaban = st.selectbox("Kualitas Jawaban", ["Standar", "Komprehensif", "Studi Referensi BMP"])
with col5:
  gaya_penulisan = st.selectbox("Gaya Bahasa", ["Natural & Mengalir", "Analitis & Kritis", "Praktis (Banyak Contoh)"])
with col6:
  target_kata = st.selectbox("Target Panjang", ["Singkat (±150 Kata)", "Menengah (±300 Kata)", "Panjang (600+ Kata)"])

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("Input Pertanyaan")
soal_topik = st.text_area("Teks Pertanyaan / Soal:", placeholder="Paste soal diskusi dari e-learning ke sini...", height=120)
uploaded_file = st.file_uploader("Unggah File Pendukung (Opsional)", type=["pdf", "png", "jpg", "jpeg"])

st.markdown("<br><br>", unsafe_allow_html=True)

# Tombol Eksekusi
if st.button("Generate Draf Jawaban", type="primary"):
  if not soal_topik and not uploaded_file:
    st.warning("Mohon masukkan pertanyaan atau unggah file terlebih dahulu.")
  else:
    with st.spinner("Memproses data dan menyusun referensi akademik..."):
      try:
        client = genai.Client(api_key=api_key_input)
        contents_payload = []
        
        if uploaded_file is not None:
          contents_payload.append({"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()})

        prompt_sistem = f"""
        Anda adalah asisten akademik cerdas untuk mahasiswa Universitas Terbuka. 
        Tugas Anda adalah membuat draf jawaban untuk mata kuliah {mata_kuliah} pada bagian {jenis_tugas}.
        
        ATURAN MUTLAK:
        1. DILARANG KERAS menggunakan emoji agar rapi saat disalin ke e-learning.
        2. Dilarang menggunakan format bintang (**) berlebihan. Gunakan penomoran/paragraf biasa.
        3. Gaya penulisan: {gaya_penulisan}. Harus menggunakan bahasa Indonesia yang baik, logis, dan khas mahasiswa.
        4. WAJIB menyertakan "Sumber Referensi" di bagian paling bawah (mencakup Buku Materi Pokok (BMP) {mata_kuliah}).
        5. Mode: {mode_jawaban}, Panjang: {target_kata}.
        
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
        time.sleep(0.5)

      except Exception as e:
        st.error(f"Terjadi kendala sistem: {e}")

if "current_result" in st.session_state:
  st.markdown("---")
  st.subheader("Hasil Draf Jawaban")
  st.text_area("Silakan salin teks di bawah ini:", value=st.session_state.current_result, height=400)

  col_dl1, col_dl2 = st.columns(2)
  with col_dl1:
    doc = Document()
    doc.add_paragraph(st.session_state.current_result)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    st.download_button("Download Dokumen (.docx)", data=doc_io, file_name=f"Tugas_{mata_kuliah}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

  with col_dl2:
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    text_object = c.beginText(40, 750)
    text_object.setFont("Helvetica", 10)
    
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
    st.download_button("Download Dokumen (.pdf)", data=pdf_io, file_name=f"Tugas_{mata_kuliah}.pdf", mime="application/pdf", use_container_width=True)
