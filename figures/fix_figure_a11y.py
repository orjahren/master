#!/usr/bin/env python3
import argparse
from pikepdf import Pdf, Name

def set_interpolate_false(img_ref):
    try:
        img = img_ref.get_object()
    except Exception:
        return
    if img.get('/Subtype') == Name('/Image'):
        img['/Interpolate'] = False
        if '/SMask' in img:
            try:
                sm = img['/SMask'].get_object()
                if sm.get('/Subtype') == Name('/Image'):
                    sm['/Interpolate'] = False
            except Exception:
                pass

def process_xobjects(xobjs):
    for name, ref in list(xobjs.items()):
        try:
            obj = ref.get_object()
        except Exception:
            continue
        if obj.get('/Subtype') == Name('/Image'):
            set_interpolate_false(ref)
        elif obj.get('/Subtype') == Name('/Form'):
            resources = obj.get('/Resources')
            if resources and '/XObject' in resources:
                process_xobjects(resources['/XObject'])

def main():
    ap = argparse.ArgumentParser(description="Set /Interpolate false for images in a PDF")
    ap.add_argument('input', help="input PDF")
    ap.add_argument('output', nargs='?', help="output PDF (if omitted writes input.fixed.pdf)")
    args = ap.parse_args()

    out_path = args.output or args.input + ".fixed.pdf"
    with Pdf.open(args.input, allow_overwriting_input=True) as pdf:
        for page in pdf.pages:
            resources = page.get('/Resources')
            if resources and '/XObject' in resources:
                process_xobjects(resources['/XObject'])
        # extra sweep over all objects
        for obj in pdf.objects:
            try:
                if getattr(obj, 'get', None) and obj.get('/Subtype') == Name('/Image'):
                    obj['/Interpolate'] = False
                    if '/SMask' in obj:
                        try:
                            sm = obj['/SMask'].get_object()
                            if sm.get('/Subtype') == Name('/Image'):
                                sm['/Interpolate'] = False
                        except Exception:
                            pass
            except Exception:
                continue

        pdf.save(out_path)
        print(f"Saved fixed PDF to: {out_path}")

if __name__ == "__main__":
    main()
