from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
from fastapi import HTTPException

@dataclass
class LayoutValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    estimated_text_capacity_words: int
    estimated_text_words: int
    overflow_words: int
    def to_dict(self) -> dict[str, Any]: return asdict(self)

class LayoutValidator:
    def __init__(self, *, min_gutter: float = 12.0) -> None: self.min_gutter = min_gutter
    def boxes_overlap(self, a: dict, b: dict, min_gap: float = 0) -> bool:
        return not (a['x']+a['w']+min_gap<=b['x'] or b['x']+b['w']+min_gap<=a['x'] or a['y']+a['h']+min_gap<=b['y'] or b['y']+b['h']+min_gap<=a['y'])
    def estimate_text_capacity(self, element: dict, typography: dict | None) -> int:
        box=element.get('box') or {}; w,h=float(box.get('w',0)),float(box.get('h',0))
        if w<=0 or h<=0: return 0
        fs=float((typography or {}).get('body_size',11)); lh=float((typography or {}).get('line_height',1.5))
        return max(0,int((max(8,int(w/max(4.0,fs*0.52)))*max(1,int(h/max(10.0,fs*lh))))/5.2))
    def validate_layout(self, layout_json: dict, *, page=None, text: str='') -> LayoutValidationResult:
        e=[]; w=[]
        if not isinstance(layout_json,dict): return LayoutValidationResult(False,['layout_json must be an object'],[],0,len(text.split()),0)
        if layout_json.get('schema_version')!=2: e.append('layout_json.schema_version must be 2')
        pd=layout_json.get('page') or {}; safe=pd.get('safe_area') or {'x':0,'y':0,'w':pd.get('width',1),'h':pd.get('height',1)}
        elements=layout_json.get('elements') or []
        if not isinstance(elements,list): e.append('elements must be an array'); elements=[]
        images=[]; texts=[]; ids=set(); used=set()
        for el in elements:
            if not all(k in el for k in ('id','type','box')): e.append('every element must include id, type, box'); continue
            if el['id'] in ids: e.append(f"duplicate element id {el['id']}")
            ids.add(el['id']); b=el['box']
            if any(k not in b for k in ('x','y','w','h')) or b['w']<=0 or b['h']<=0: e.append(f"element {el['id']} has invalid box"); continue
            if not el.get('bleed') and not (b['x']>=safe['x'] and b['y']>=safe['y'] and b['x']+b['w']<=safe['x']+safe['w'] and b['y']+b['h']<=safe['y']+safe['h']): e.append(f"element {el['id']} is outside safe area")
            if el.get('type')=='image':
                if not el.get('image_id'): e.append(f"image element {el['id']} missing image_id")
                elif el['image_id'] in used and not layout_json.get('image_policy',{}).get('allow_duplicate_image_use'): e.append(f"duplicate image_id usage {el['image_id']}")
                used.add(el.get('image_id')); images.append(el)
            if el.get('type') in {'text','caption'}: texts.append(el)
        for t in texts:
            for i in images:
                if self.boxes_overlap(t['box'],i['box'],self.min_gutter): e.append(f"text/caption element {t['id']} overlaps image {i['id']}")
        for i,a in enumerate(texts):
            for b in texts[i+1:]:
                if self.boxes_overlap(a['box'],b['box'],0): e.append(f"text elements {a['id']} and {b['id']} overlap")
        for i,a in enumerate(images):
            for b in images[i+1:]:
                if self.boxes_overlap(a['box'],b['box'],0): e.append(f"image elements {a['id']} and {b['id']} overlap")
        page_images={img.id for img in getattr(page,'images',[])} if page else set()
        if page is not None:
            if page_images and not images and not layout_json.get('image_policy',{}).get('allow_omit_images'): e.append('page has images but layout has no image elements')
            if not page_images and images: e.append('layout contains image elements but page has no images')
            for el in images:
                if el.get('image_id') not in page_images: e.append(f"image_id {el.get('image_id')} does not belong to this page")
        if text.strip() and not any(x.get('type')=='text' for x in elements): e.append('text exists but no text element present')
        cap=sum(self.estimate_text_capacity(el,layout_json.get('typography') or el.get('style')) for el in elements if el.get('type')=='text')
        words=len(text.split()); overflow=max(0,words-cap)
        if overflow>0: w.append('Text may continue to next page.')
        return LayoutValidationResult(not e,e,w,cap,words,overflow)
    def assert_valid_layout(self, layout_json: dict, *, page=None, text: str='') -> LayoutValidationResult:
        r=self.validate_layout(layout_json,page=page,text=text)
        if not r.valid: raise HTTPException(status_code=400,detail={'message':'Invalid layout','errors':r.errors})
        return r
