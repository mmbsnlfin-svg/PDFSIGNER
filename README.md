# Bulk PDF Digital Signature App

Local Streamlit app for signing PDF files in bulk using a USB DSC token such as mToken CryptoID.

## Important
This app must run on the same Windows PC where the USB DSC token is connected and token driver is installed.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## mToken PKCS#11 DLL path

Common paths:

```text
C:\Windows\System32\eps2003csp11.dll
C:\Windows\System32\wdpkcs.dll
C:\Windows\System32\SignatureP11.dll
C:\Windows\System32\CryptoIDA_P11.dll
```

If unsure, search in `C:\Windows\System32` for files containing `p11`, `pkcs`, `cryptoid`, or `eps`.

## Visible signature

The app adds a visible signature box with:
- green right tick symbol
- Digitally Signed by
- signer name
- signing date/time
- reason and location

## Note

The private key is not exported from the token. The token performs the signing after PIN authentication.
