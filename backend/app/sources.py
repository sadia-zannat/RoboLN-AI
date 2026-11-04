"""Bounded local extraction and lexical RAG. No network fetches or executable content."""
import io, re, math, hashlib
from collections import Counter
from pathlib import PurePosixPath
from fastapi import HTTPException
from pypdf import PdfReader, overwrite_configuration
# Limit decompressed streams in the current extraction context.
overwrite_configuration(zlib_maximum_output_length=4_000_000,lzw_maximum_output_length=4_000_000,run_length_maximum_output_length=4_000_000,zlib_maximum_recovery_input_length=1_000_000,maximum_declared_stream_length=4_000_000)
from PIL import Image, UnidentifiedImageError

MAX_FILE = 4 * 1024 * 1024

def extract(filename: str, content: bytes):
    filename = PurePosixPath(filename.replace('\\','/')).name
    if not filename or len(filename)>180 or any(ord(c)<32 for c in filename):
        raise HTTPException(422,'Invalid filename')
    if not content or len(content)>MAX_FILE:
        raise HTTPException(413,'Source must contain 1 byte to 4 MiB')
    suffix=PurePosixPath(filename).suffix.lower()
    if suffix=='.pdf':
        try:
            pdf=PdfReader(io.BytesIO(content), strict=True)
            if pdf.is_encrypted: raise ValueError('Encrypted')
            if len(pdf.pages)>100: raise ValueError('Too many pages')
            pages=[]
            total=0
            for i,p in enumerate(pdf.pages):
                text=p.extract_text() or ''
                total+=len(text)
                if total>500_000: raise ValueError('Text limit')
                pages.append((i+1,text))
        except Exception:
            raise HTTPException(422,'Unreadable/encrypted PDF or extraction limit exceeded (100 pages / 500k characters). Scanned PDFs require external OCR.')
        media='application/pdf'
    elif suffix in ('.txt','.md','.csv','.json'):
        try: text=content.decode('utf-8-sig')
        except UnicodeDecodeError: raise HTTPException(422,'Text sources must be UTF-8')
        if '\x00' in text or len(text)>500_000: raise HTTPException(422,'Invalid or oversized text')
        pages=[(None,text)];media='text/plain'
    else: raise HTTPException(415,'Supported sources: UTF-8 TXT, MD, CSV, JSON, and text PDF')
    chunks=[]
    for page,text in pages:
        text=text.strip()
        for offset in range(0,len(text),900):
            piece=text[offset:offset+1000]
            if piece.strip(): chunks.append({'index':len(chunks)+1,'page':page,'offset':offset,'text':piece})
    if not chunks: raise HTTPException(422,'No extractable text. OCR is not included.')
    return filename,media,chunks

def retrieve(documents, query: str, limit=6):
    terms=Counter(re.findall(r'[^\W_]+',query.lower()))
    matches=[]
    for doc in documents:
        for chunk in doc.chunks:
            tokens=Counter(re.findall(r'[^\W_]+',chunk['text'].lower()))
            score=sum(min(tokens[t],3)*(1+math.log(1+n)) for t,n in terms.items() if len(t)>1)
            if score:
                matches.append({'source_id':doc.id,'filename':doc.filename,'version':doc.version,
                    **chunk,'citation':f'S:{doc.id}:C:{chunk["index"]}', 'score':round(score,4),
                    'sha256':doc.sha256})
    return sorted(matches,key=lambda x:(-x['score'],x['source_id'],x['index']))[:limit]

def image_bytes(data_url: str) -> bytes:
    import base64, binascii
    if len(data_url)>4_300_000 or not re.match(r'^data:image/(png|jpeg|webp);base64,',data_url):
        raise HTTPException(422,'Image must be a PNG, JPEG or WebP data URL (3 MiB max)')
    try:
        raw=base64.b64decode(data_url.split(',',1)[1],validate=True)
        if len(raw)>3*1024*1024: raise ValueError()
        with Image.open(io.BytesIO(raw)) as img:
            if img.width*img.height>8_000_000 or getattr(img,'n_frames',1)!=1: raise ValueError()
            img.load(); img=img.convert('RGB');img.thumbnail((1600,1600))
            out=io.BytesIO();img.save(out,format='JPEG',quality=85)
            return out.getvalue()  # fresh JPEG strips EXIF/location metadata
    except (ValueError,binascii.Error,UnidentifiedImageError,OSError,Image.DecompressionBombError):
        raise HTTPException(422,'Invalid image or decoded image exceeds safe limits')
