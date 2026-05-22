from app import make_tick_signature_appearance

with open("signature_tick_preview.png", "wb") as f:
    f.write(make_tick_signature_appearance("KISHOR HARI GAJARE", "Document digitally signed", "India"))

print("Created signature_tick_preview.png")
