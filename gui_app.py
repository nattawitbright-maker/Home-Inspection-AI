import streamlit as st
import google.generativeai as genai
import PIL.Image
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. ตั้งค่าหน้าตาเว็บ ---
st.set_page_config(page_title="AI วิศวกรตรวจบ้าน", layout="wide")
st.title("🏗️ AI วิศวกรตรวจบ้าน")

# --- 2. การเชื่อมต่อ API และโมเดล (เลือกอัตโนมัติ) ---
genai.configure(api_key="AIzaSyBuxrrWhc57kC1qeaDkGPE_Htg9cn2QmDE")

def get_working_model():
    # ดึงรายชื่อโมเดลที่ใช้งานได้มาเลือกตัวแรกอัตโนมัติ
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    return genai.GenerativeModel(models[0])

model = get_working_model()
st.sidebar.success(f"เชื่อมต่อโมเดล: {model.model_name}")

# --- 3. ฟังก์ชันดึงเกณฑ์จาก Google Sheets ---
def get_jasper_standard():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        # *** เปลี่ยนชื่อไฟล์ให้ตรงกับ Sheet ของพี่ ***
        sheet = client.open("รายการตรวจบ้าน End Product QA").sheet1
        return str(sheet.get_all_values()[:100]) # ดึง 100 แถวแรกมาเป็นเกณฑ์
    except Exception as e:
        return f"ใช้เกณฑ์มาตรฐานทั่วไป (ดึง Sheet ไม่สำเร็จ: {e})"

# --- 4. ส่วน UX/UI สำหรับอัปโหลดภาพ ---
jasper_standard = get_jasper_standard()

uploaded_files = st.file_uploader("เลือกรูปภาพ Defect (ส่งได้หลายรูปพร้อมกัน)", 
                                  type=['jpg', 'jpeg', 'png'], 
                                  accept_multiple_files=True)

if uploaded_files:
    st.info(f"📸 พบรูปภาพทั้งหมด {len(uploaded_files)} รูป")
    
    if st.button("🚀 เริ่มวิเคราะห์รายงานทั้งหมด"):
        for uploaded_file in uploaded_files:
            # สร้างกล่องแสดงผลแยกแต่ละรูป
            with st.expander(f"ผลการตรวจรูปภาพ: {uploaded_file.name}", expanded=True):
                col1, col2 = st.columns([1, 2])
                
                img = PIL.Image.open(uploaded_file)
                col1.image(img, use_container_width=True)
                
                with col2:
                    with st.spinner("AI กำลังวิเคราะห์ตามมาตรฐาน JASPER..."):
                        try:
                            prompt = f""" คำสั่ง:
                                             1. ระบุว่าพบ Defect ตรงกับหัวข้อใด (เช่น 14.1, 14.2)
                                             2. บอกรายละเอียดตามเกณฑ์มาตรฐานจาก google sheet
                                             3. ระบุความสำคัญ (M = งานระบบ/ความปลอดภัย)
                                             4. แนะนำวิธีแก้ไข
                                             ตอบเป็นภาษาไทย
                                             5. คำตอบแบบกระชับ ตอบภายใน 2 บรรทัด เหมือนแจ้งเพื่อทราบเฉยๆ ไม่ต้องบอกเลขหัวข้อ และให้ตอบตามภาพที่เห็นด้วยว่าคืออะไร
                                             ตอบเป็นภาษาไทย"""
                            
                            response = model.generate_content([prompt, img])
                            st.markdown("### 📋 รายงานการวิเคราะห์")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"ไม่สามารถวิเคราะห์รูปนี้ได้: {e}")
                st.divider()

# --- ส่วน Sidebar แสดงเกณฑ์การตรวจ ---
with st.sidebar:
    st.header("📋 มาตรฐานที่ใช้")
    if st.checkbox("ดูเกณฑ์จาก Google Sheets"):
        st.write(jasper_standard)