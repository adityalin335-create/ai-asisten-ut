from datetime import datetime
import io
import os
import streamlit as st
from docx import Document
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Konfigurasi Halaman Web App
st.set_page_config(
    page_title="AI Asisten Diskusi & Tugas UT", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk UI/UX Profesional & Elegan
st.markdown("""
    <style>
    /* Global Styling & Background */
    .main {
        background-color: #f4f6f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Utama */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        font-size: 2.2rem !important;
        letter-spacing: -0.5px;
    }
    
    h3 {
        color: #334155;
        font-weight: 600;
        font-size: 1.25rem !important;
        margin-top: 1rem !important;
    }

    /* Styling Tombol Utama */
    .stButton>button {
        background-color: #1e3a8a;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1rem;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    }

    /* Kotak Input dan Selectbox */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        background-color: #ffffff;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Session State untuk Riwayat
if "history" not in st.session_state:
  st.session_state.history = []

# Judul Utama Aplikasi dengan Tata Letak Bersih
st.title("AI Asisten Diskusi & Tugas UT")
st.markdown(
    "Portal akademik cerdas terintegrasi untuk menyusun draf diskusi dan tugas "
    "Universitas Terbuka dengan standar penulisan ilmiah yang natural dan terstruktur."
)
st.markdown("---")

# Sidebar untuk Pengaturan dan Riwayat
with st.sidebar:
  st.header("Pengaturan & Kunci")
  api_key_input = st.secrets["GEMINI_API_KEY"]
  
  st.markdown("---")
  st.header("Riwayat Sesi")
  
  if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
      # Menggunakan expander kecil untuk riwayat agar rapi
      with st.expander(f"{item['matkul']} ({item['jenis']})"):
        st.caption(f"Waktu: {item['waktu']}")
        if st.button("Muat Ulang Teks", key=f"hist_{i}"):
          st.session_state.current_result = item["teks"]
  else:
    st.info("Belum ada riwayat tersimpan.")

# Form Input Identitas Mahasiswa
st.subheader("1. Identitas Mahasiswa")
col1, col2 = st.columns(2)
with col1:
  nama_mhs = st.text_input(
      "Nama Lengkap", placeholder="Contoh: Aditia Lindra Agasta"
  )
  prodi = st.text_input("Program Studi", placeholder="Contoh: Ilmu Hukum")
with col2:
  upbjj = st.text_input(
      "UPBJJ-UT", placeholder="Contoh: UPBJJ-UT Semarang"
  )
  nama_tutor = st.text_input(
      "Nama Tutor (Opsional)", placeholder="Contoh: Dr. Budi Santoso, S.H., M.H."
  )

st.markdown("---")

# Form Detail Tugas / Diskusi
st.subheader("2. Detail Tugas & Gaya Penulisan")
col3, col4, col5 = st.columns(3)
with col3:
  jenis_tugas = st.selectbox(
      "Jenis Kegiatan",
      [
          "Diskusi Sesi 1", "Diskusi Sesi 2", "Diskusi Sesi 3", "Diskusi Sesi 4",
          "Diskusi Sesi 5", "Diskusi Sesi 6", "Diskusi Sesi 7", "Diskusi Sesi 8",
          "Tugas 1", "Tugas 2", "Tugas 3",
      ],
  )
  mata_kuliah = st.text_input(
      "Mata Kuliah", placeholder="Contoh: Pengantar Ilmu Hukum"
  )
with col4:
  mode_jawaban = st.selectbox(
      "Mode Jawaban",
      [
          "Basic (Ringkas & Langsung)",
          "Pro (Mendalam & Komprehensif)",
          "Jurnal Asli (Gaya Ilmiah/Referensi BMP)",
      ],
  )
  gaya_penulisan = st.selectbox(
      "Gaya Penulisan",
      [
          "Standar / Natural",
          "Analisis & Kritis (Mendalam)",
          "Praktis & Studi Kasus (Banyak Contoh)",
      ],
  )
with col5:
  target_kata = st.selectbox(
      "Target Panjang Kata",
      ["Standar (± 150-250 kata)", "Medium (± 300-500 kata)", "Panjang (600+ kata)"],
  )

st.markdown("---")

# Tempat Input Pertanyaan / File
st.subheader("3. Input Materi / Pertanyaan")
soal_topik = st.text_area(
    "Salin Pertanyaan Topik / Soal Diskusi:",
    placeholder="Tempel teks soal atau bahan diskusi forum tuton di sini...",
    height=120
)

uploaded_file = st.file_uploader(
    "Unggah File Pendukung (Opsional: PDF Modul / Gambar Soal)",
    type=["pdf", "png", "jpg", "jpeg"],
)

st.markdown("---")

# Tombol Eksekusi Utama
if st.button("Buat Draf Jawaban Akademik", type="primary"):
  if not api_key_input:
    st.error("Mohon masukkan Google Gemini API Key terlebih dahulu pada menu di sidebar.")
  elif not soal_topik and not uploaded_file:
    st.warning("Mohon masukkan pertanyaan atau unggah file pendukung terlebih dahulu.")
  else:
    with st.spinner("Sistem sedang merumuskan draf akademik dan menelaah referensi BMP..."):
      try:
        client = genai.Client(api_key=api_key_input)
        contents_payload = []
        
        if uploaded_file is not None:
          bytes_data = uploaded_file.getvalue()
          file_part = {"mime_type": uploaded_file.type, "data": bytes_data}
          contents_payload.append(file_part)

        prompt_sistem = f"""
        Anda adalah asisten akademik cerdas untuk mahasiswa Universitas Terbuka. 
        Tugas Anda adalah membuat draf jawaban untuk mata kuliah {mata_kuliah} pada bagian {jenis_tugas}.
        
        ATURAN MUTLAK GAYA BAHASA & STRUKTUR:
        1. DILARANG KERAS menggunakan emoji, ikon, atau simbol dekoratif apa pun.
        2. Dilarang menggunakan format markdown atau karakter bintang (**) yang berlebihan pada kalimat utama. Gunakan teks paragraf biasa atau penomoran angka biasa (1., 2., 3.) yang rapi.
        3. Gaya penulisan harus natural, mengalir layaknya mahasiswa aktif UT yang sedang berdiskusi, menggunakan tata bahasa Indonesia formal yang baik, analitis, dan mendalam.
        4. WAJIB menyertakan bagian "Sumber Referensi" atau "Daftar Pustaka" di bagian paling bawah jawaban, mencantumkan sumber nyata seperti Buku Materi Pokok (BMP) UT mata kuliah {mata_kuliah} dan pasal/undang-undang terkait.
        5. Mode jawaban dipilih: {mode_jawaban} dengan gaya {gaya_penulisan} dan target panjang kata: {target_kata}.
        
        Pertanyaan/Soal yang harus dijawab:
        {soal_topik}
        """
        
        contents_payload.append(prompt_sistem)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents_payload,
        )

        header_identitas = (
            f"NAMA : {nama_mhs if nama_mhs else '[Nama Mahasiswa]'}\n"
            f"NIM / PRODI : {prodi if prodi else '[Program Studi]'}\n"
            f"UPBJJ-UT : {upbjj if upbjj else '[UPBJJ]'}\n"
            f"MATA KULIAH : {mata_kuliah if mata_kuliah else '[Mata Kuliah]'}\n"
            f"KEGIATAN : {jenis_tugas}\n"
            f"{'='*50}\n\n"
        )

        hasil_final = header_identitas + response.text
        st.session_state.current_result = hasil_final
        
        st.session_state.history.append({
            "matkul": mata_kuliah if mata_kuliah else "Tanpa Matkul",
            "jenis": jenis_tugas,
            "teks": hasil_final,
            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

      except Exception as e:
        st.error(f"Terjadi kesalahan teknis saat memproses: {e}")

# Tampilkan Hasil Jika Sudah Tersedia
if "current_result" in st.session_state:
  st.markdown("---")
  st.subheader("Hasil Draf Siap Pakai")
  
  st.text_area(
      "Pratinjau Dokumen:",
      value=st.session_state.current_result,
      height=380,
  )

  col_dl1, col_dl2 = st.columns(2)
  
  with col_dl1:
    doc = Document()
    doc.add_paragraph(st.session_state.current_result)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    st.download_button(
        label="Unduh Dokumen Word (.docx)",
        data=doc_io,
        file_name=f"Tugas_{jenis_tugas}_{mata_kuliah}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

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

    st.download_button(
        label="Unduh Dokumen PDF",
        data=pdf_io,
        file_name=f"Tugas_{jenis_tugas}_{mata_kuliah}.pdf",
        mime="application/pdf",
    )
