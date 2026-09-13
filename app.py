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
    page_icon="✌️", 
    layout="wide"
)

# Custom CSS: Tema "Aesthetic Playful Gen-Z"
st.markdown("""
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

    <style>
    /* Animasi Latar Belakang Bergerak Soft Pastel */
    @keyframes gradientBG {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Animasi Elemen Muncul / Bouncy */
    @keyframes popIn {
        0% {opacity: 0; transform: scale(0.95) translateY(20px);}
        100% {opacity: 1; transform: scale(1) translateY(0);}
    }

    /* Terapkan Latar Belakang & Font Poppins ke Seluruh Aplikasi */
    .stApp {
        background: linear-gradient(-45deg, #ff9a9e, #fecfef, #a1c4fd, #b2fcca);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Poppins', sans-serif !important;
        color: #1e293b;
    }
    
    /* Warna Teks Global agar kontras di background terang */
    h1, h2, h3, p, label, .st-emotion-cache-16idsys p {
        color: #334155 !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Judul Utama Bergaya Kekinian */
    h1 {
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        background: linear-gradient(45deg, #ff0844 0%, #ffb199 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: -1px;
        animation: popIn 0.6s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    }
    
    .subtitle-container {
        text-align: center;
        margin-bottom: 2rem;
        animation: popIn 0.8s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    }
    .subtitle {
        font-size: 1.1rem;
        font-weight: 600;
        color: #475569 !important;
        background: rgba(255, 255, 255, 0.6);
        padding: 8px 24px;
        border-radius: 30px;
        display: inline-block;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Tombol Utama (Bouncy & Membulat/Pill Shape) */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 50px; /* Bentuk kapsul/pill */
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
        width: 100%;
        animation: popIn 1s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    }
    .stButton>button:hover {
        transform: translateY(-5px) scale(1.03);
        box-shadow: 0 10px 25px rgba(118, 75, 162, 0.5);
    }

    /* Styling Kotak Input (Frosted Glass Cerah) */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.7) !important;
        border: 2px solid rgba(255, 255, 255, 0.5) !important;
        color: #1e293b !important;
        border-radius: 15px;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea !important;
        background: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Mengambil API Key dari Brankas (Secrets)
api_key_input = st.secrets["GEMINI_API_KEY"]

# Bagian Judul Tengah 
st.title("✨ AI Asisten UT")
st.markdown("<div class='subtitle-container'><div class='subtitle'>Bikin draf diskusi & tugas jadi lebih cepat, santai, dan rapi! 🚀</div></div>", unsafe_allow_html=True)
st.markdown("---")

# Layout Parameter Pengguna
st.subheader("👤 Info Mahasiswa")
col1, col2 = st.columns(2)
with col1:
  nama_mhs = st.text_input("Nama Kamu", placeholder="Contoh: Aditia Lindra Agasta")
  prodi = st.text_input("Program Studi", placeholder="Contoh: Ilmu Hukum")
with col2:
  upbjj = st.text_input("Asal UPBJJ", placeholder="Contoh: UPBJJ Semarang")
  mata_kuliah = st.text_input("Mata Kuliah", placeholder="Contoh: Pengantar Ilmu Hukum")

st.markdown("---")

# Layout Konfigurasi AI
st.subheader("⚙️ Atur Gaya Jawaban")
col3, col4, col5, col6 = st.columns(4)
with col3:
  jenis_tugas = st.selectbox("Ini Untuk Apa?", ["Diskusi Sesi 1", "Diskusi Sesi 2", "Diskusi Sesi 3", "Diskusi Sesi 4", "Diskusi Sesi 5", "Diskusi Sesi 6", "Diskusi Sesi 7", "Diskusi Sesi 8", "Tugas 1", "Tugas 2", "Tugas 3"])
with col4:
  mode_jawaban = st.selectbox("Level Jawaban", ["Standar (Aman)", "Pro (Mendalam)", "Full Jurnal/BMP"])
with col5:
  gaya_penulisan = st.selectbox("Gaya Bahasa", ["Asik & Natural", "Kritis (Kaya Anak BEM)", "Banyak Contoh Kasus"])
with col6:
  target_kata = st.selectbox("Panjang Teks", ["Pendek Aja (±150)", "Sedang (±300)", "Panjang (600+)"])

st.markdown("---")

st.subheader("📚 Masukin Soalnya Di Sini")
soal_topik = st.text_area("Copy-Paste Pertanyaan / Bahan Diskusi:", placeholder="Paste soal dari e-learning UT ke sini ya...", height=120)
uploaded_file = st.file_uploader("Atau Upload Gambar Soal/PDF (Opsional)", type=["pdf", "png", "jpg", "jpeg"])

st.markdown("<br>", unsafe_allow_html=True)

# Tombol Eksekusi
if st.button("✨ BIKIN JAWABAN SEKARANG ✨", type="primary"):
  if not soal_topik and not uploaded_file:
    st.warning("Eits, masukin soalnya dulu dong sebelum klik tombol! 😅")
  else:
    with st.spinner("⏳ Bentar ya, AI lagi mikir keras sambil buka-buka BMP..."):
      try:
        client = genai.Client(api_key=api_key_input)
        contents_payload = []
        
        if uploaded_file is not None:
          contents_payload.append({"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()})

        prompt_sistem = f"""
        Anda adalah asisten akademik super cerdas dan santai untuk mahasiswa Universitas Terbuka. 
        Tugas Anda adalah membuat draf jawaban untuk mata kuliah {mata_kuliah} pada bagian {jenis_tugas}.
        
        ATURAN MUTLAK:
        1. DILARANG KERAS menggunakan emoji pada isi jawaban akademik agar bisa langsung di-copy-paste ke web e-learning.
        2. Dilarang menggunakan format bintang (**) berlebihan. Gunakan format paragraf/penomoran yang sangat rapi.
        3. Gaya penulisan: {gaya_penulisan}. Harus natural seolah-olah mahasiswa sungguhan yang menulis, tidak kaku seperti robot, tapi tetap formal dan berbobot secara akademik.
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
        
        st.balloons()
        time.sleep(1)

      except Exception as e:
        st.error(f"Yah, ada error dari sistemnya: {e}")

if "current_result" in st.session_state:
  st.markdown("---")
  st.subheader("🎉 Yeay! Draf Jawaban Udah Jadi")
  st.text_area("Silakan Copy dari sini:", value=st.session_state.current_result, height=400)

  col_dl1, col_dl2 = st.columns(2)
  with col_dl1:
    doc = Document()
    doc.add_paragraph(st.session_state.current_result)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    st.download_button("📝 Download format Word", data=doc_io, file_name=f"Tugas_{mata_kuliah}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

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
    st.download_button("📄 Download format PDF", data=pdf_io, file_name=f"Tugas_{mata_kuliah}.pdf", mime="application/pdf", use_container_width=True)
