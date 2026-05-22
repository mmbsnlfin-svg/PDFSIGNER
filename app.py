import io
import os
import zipfile
import tempfile
from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers, fields
from pyhanko.sign.pkcs11 import PKCS11Signer
from pyhanko_certvalidator import ValidationContext


st.set_page_config(page_title="Bulk PDF Digital Signature", page_icon="✅", layout="wide")

st.title("✅ Bulk PDF Digital Signature")
st.caption("Local DSC token based PDF signer for mToken / USB digital signature certificate")


def make_tick_signature_appearance(signer_name: str, reason: str, location: str) -> bytes:
    """Create visible signature image with right tick symbol."""
    width, height = 900, 260
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("arialbd.ttf", 44)
        font_medium = ImageFont.truetype("arialbd.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 27)
    except Exception:
        font_big = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # border
    draw.rounded_rectangle([8, 8, width - 8, height - 8], radius=22, outline=(40, 40, 40), width=3)

    # green tick circle
    circle = [35, 45, 175, 185]
    draw.ellipse(circle, fill=(18, 150, 75), outline=(18, 120, 60), width=4)

    # right tick symbol
    draw.line([(72, 115), (103, 145), (143, 82)], fill="white", width=14, joint="curve")

    x = 205
    y = 38
    draw.text((x, y), "Digitally Signed", fill=(18, 120, 60), font=font_big)
    y += 58
    draw.text((x, y), f"by: {signer_name or 'DSC Certificate Holder'}", fill=(0, 0, 0), font=font_medium)
    y += 44
    draw.text((x, y), f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", fill=(0, 0, 0), font=font_small)
    y += 36
    draw.text((x, y), f"Reason: {reason}", fill=(0, 0, 0), font=font_small)
    y += 36
    draw.text((x, y), f"Location: {location}", fill=(0, 0, 0), font=font_small)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def sign_pdf_with_token(
    pdf_bytes: bytes,
    pkcs11_dll: str,
    token_label: str | None,
    cert_label: str | None,
    pin: str,
    signer_name: str,
    reason: str,
    location: str,
    page_index: int,
    box: tuple[int, int, int, int],
) -> bytes:
    """Sign one PDF using PKCS#11 token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        in_pdf = os.path.join(tmpdir, "input.pdf")
        out_pdf = os.path.join(tmpdir, "signed.pdf")
        stamp_img = os.path.join(tmpdir, "signature_tick.png")

        with open(in_pdf, "wb") as f:
            f.write(pdf_bytes)

        with open(stamp_img, "wb") as f:
            f.write(make_tick_signature_appearance(signer_name, reason, location))

        signer = PKCS11Signer(
            pkcs11_module=pkcs11_dll,
            token_label=token_label or None,
            cert_label=cert_label or None,
            user_pin=pin,
        )

        meta = signers.PdfSignatureMetadata(
            field_name="Signature1",
            reason=reason,
            location=location,
            validation_context=ValidationContext(allow_fetching=False),
        )

        with open(in_pdf, "rb") as inf:
            writer = IncrementalPdfFileWriter(inf)

            fields.append_signature_field(
                writer,
                sig_field_spec=fields.SigFieldSpec(
                    sig_field_name="Signature1",
                    box=box,
                    on_page=page_index,
                ),
            )

            pdf_signer = signers.PdfSigner(
                meta,
                signer=signer,
                stamp_style=signers.PdfSignatureAppearance(
                    background=stamp_img,
                    background_opacity=1,
                ),
            )

            with open(out_pdf, "wb") as outf:
                pdf_signer.sign_pdf(writer, output=outf)

        with open(out_pdf, "rb") as f:
            return f.read()


with st.sidebar:
    st.header("Token Settings")
    pkcs11_dll = st.text_input(
        "PKCS#11 DLL path",
        value=r"C:\Windows\System32\eps2003csp11.dll",
        help="Change as per your mToken driver DLL.",
    )
    token_label = st.text_input("Token label / name optional", value="")
    cert_label = st.text_input("Certificate label optional", value="")
    pin = st.text_input("USB Token PIN", type="password")

    st.header("Signature Text")
    signer_name = st.text_input("Signer name", value="KISHOR HARI GAJARE")
    reason = st.text_input("Reason", value="Document digitally signed")
    location = st.text_input("Location", value="India")

    st.header("Signature Position")
    page_choice = st.selectbox("Page", ["Last page", "First page"], index=0)
    x1 = st.number_input("X1 left", value=50)
    y1 = st.number_input("Y1 bottom", value=50)
    x2 = st.number_input("X2 right", value=300)
    y2 = st.number_input("Y2 top", value=130)

uploaded = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

st.info(
    "Right tick symbol will appear in the visible signature box. "
    "Signing will work only on a local Windows PC with the DSC token connected and driver installed."
)

if st.button("✅ Sign PDFs", type="primary"):
    if not uploaded:
        st.error("Please upload at least one PDF.")
    elif not pin:
        st.error("Please enter USB token PIN.")
    elif not pkcs11_dll:
        st.error("Please enter PKCS#11 DLL path.")
    else:
        signed_files = []
        errors = []

        progress = st.progress(0)
        for i, file in enumerate(uploaded, start=1):
            try:
                pdf_data = file.read()
                page_index = -1 if page_choice == "Last page" else 0

                signed_pdf = sign_pdf_with_token(
                    pdf_bytes=pdf_data,
                    pkcs11_dll=pkcs11_dll,
                    token_label=token_label,
                    cert_label=cert_label,
                    pin=pin,
                    signer_name=signer_name,
                    reason=reason,
                    location=location,
                    page_index=page_index,
                    box=(int(x1), int(y1), int(x2), int(y2)),
                )

                name = file.name.replace(".pdf", "_signed.pdf")
                signed_files.append((name, signed_pdf))
                st.success(f"Signed: {file.name}")

            except Exception as e:
                errors.append((file.name, str(e)))
                st.error(f"Failed: {file.name} — {e}")

            progress.progress(i / len(uploaded))

        if signed_files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                for name, data in signed_files:
                    z.writestr(name, data)

            st.download_button(
                "⬇️ Download Signed ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"signed_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
            )

        if errors:
            st.subheader("Errors")
            for name, err in errors:
                st.write(f"**{name}**: {err}")
