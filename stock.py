import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime
import plotly.express as px

DATA_FILE = 'stok_barang.csv'
LOG_FILE = 'log_stok.csv'

# ===== Fungsi Load & Simpan =====
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'Kategori' not in df.columns:
            df['Kategori'] = 'Lainnya'
        return df
    else:
        return pd.DataFrame(columns=['Nama Barang', 'Kategori', 'Stok'])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def log_perubahan(aksi, nama_barang, jumlah):
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_data = pd.DataFrame([[waktu, aksi, nama_barang, jumlah]], columns=['Waktu', 'Aksi', 'Nama Barang', 'Jumlah'])
    if os.path.exists(LOG_FILE):
        log_data.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        log_data.to_csv(LOG_FILE, index=False)

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='StokBarang')
    return output.getvalue()

# ===== Mulai Aplikasi =====
st.title("📦 Aplikasi Stock Opname Barang")

df_stok = load_data()

# === Sidebar Upload Excel ===
st.sidebar.header("📥 Upload Data Excel")
uploaded_file = st.sidebar.file_uploader("Pilih file Excel", type=["xlsx", "xls"])
if uploaded_file:
    try:
        df_uploaded = pd.read_excel(uploaded_file)
        if set(['Nama Barang', 'Stok', 'Kategori']).issubset(df_uploaded.columns):
            df_stok = df_uploaded[['Nama Barang', 'Kategori', 'Stok']]
            save_data(df_stok)
            st.sidebar.success("Data berhasil dimuat.")
        else:
            st.sidebar.error("Kolom wajib: 'Nama Barang', 'Kategori', dan 'Stok'")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file: {e}")

# === Filter Nama & Kategori ===
st.subheader("🔎 Filter Barang")

search = st.text_input("Cari nama barang:")

kategori_options = ["Semua"] + sorted(df_stok['Kategori'].dropna().unique())
selected_kategori = st.selectbox("Filter kategori:", kategori_options)

if selected_kategori != "Semua":
    df_filtered = df_stok[df_stok['Kategori'] == selected_kategori]
else:
    df_filtered = df_stok

if search:
    df_filtered = df_filtered[df_filtered['Nama Barang'].str.contains(search, case=False, na=False)]

st.dataframe(df_filtered)

# === Tambah / Update Barang ===
st.markdown("---")
st.subheader("➕ Tambah / Update Barang")

nama_barang = st.text_input("Nama Barang")
kategori = st.selectbox("Kategori", ["Bubuk", "Saos", "Minuman", "Lainnya"])
jumlah_stok = st.number_input("Jumlah Stok", min_value=0, step=1)

if st.button("Simpan"):
    if nama_barang.strip() == "":
        st.warning("Nama barang tidak boleh kosong.")
    else:
        if nama_barang in df_stok['Nama Barang'].values:
            df_stok.loc[df_stok['Nama Barang'] == nama_barang, ['Stok', 'Kategori']] = [jumlah_stok, kategori]
            log_perubahan("Update", nama_barang, jumlah_stok)
            st.success(f"Stok '{nama_barang}' diperbarui.")
        else:
            df_stok = pd.concat([
                df_stok,
                pd.DataFrame([{'Nama Barang': nama_barang, 'Kategori': kategori, 'Stok': jumlah_stok}])
            ], ignore_index=True)
            log_perubahan("Tambah", nama_barang, jumlah_stok)
            st.success(f"Barang '{nama_barang}' ditambahkan.")
        save_data(df_stok)

# === Hapus Barang ===
st.subheader("🗑️ Hapus Barang")
if not df_stok.empty:
    barang_hapus = st.selectbox("Pilih barang yang ingin dihapus", df_stok['Nama Barang'].unique())
    if st.button("Hapus"):
        df_stok = df_stok[df_stok['Nama Barang'] != barang_hapus]
        log_perubahan("Hapus", barang_hapus, 0)
        save_data(df_stok)
        st.success(f"Barang '{barang_hapus}' dihapus.")
else:
    st.info("Tidak ada data untuk dihapus.")

# === Export ke Excel ===
st.markdown("---")
st.subheader("⬇️ Export Data ke Excel")
excel_data = convert_df_to_excel(df_stok)
st.download_button(
    label="Download Excel",
    data=excel_data,
    file_name="stok_barang.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# === Grafik Stok Barang dengan Filter ===
st.markdown("---")
st.subheader("📊 Grafik Stok Barang")

# Pilihan kategori untuk grafik
kategori_grafik = st.multiselect(
    "Pilih kategori yang ingin ditampilkan di grafik:",
    options=sorted(df_stok['Kategori'].dropna().unique()),
    default=sorted(df_stok['Kategori'].dropna().unique())
)

df_grafik = df_stok[df_stok['Kategori'].isin(kategori_grafik)]

if not df_grafik.empty:
    st.markdown("#### 🔝 Barang dengan Stok Tertinggi")
    top5 = df_grafik.sort_values(by='Stok', ascending=False).head(5)
    fig_top = px.bar(top5, x='Nama Barang', y='Stok', color='Kategori', title="Top 5 Stok Barang Tertinggi")
    st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("#### 🔻 Barang dengan Stok Terendah")
    low5 = df_grafik.sort_values(by='Stok', ascending=True).head(5)
    fig_low = px.bar(low5, x='Nama Barang', y='Stok', color='Kategori', title="Top 5 Stok Barang Terendah")
    st.plotly_chart(fig_low, use_container_width=True)
else:
    st.info("Tidak ada data dalam kategori terpilih untuk ditampilkan.")

# === Log Histori Perubahan ===
st.markdown("---")
st.subheader("📚 Riwayat Perubahan Stok")

if os.path.exists(LOG_FILE):
    df_log = pd.read_csv(LOG_FILE)
    st.dataframe(df_log.sort_values(by="Waktu", ascending=False))
    st.download_button(
        label="Download Log CSV",
        data=df_log.to_csv(index=False),
        file_name="log_stok.csv",
        mime="text/csv"
    )
else:
    st.info("Belum ada log perubahan stok.")
