from __future__ import annotations
from app.models.entities import Book, Page

class LayoutEngine:
    PAGE_SIZES={"A4":(595,842),"A5":(420,595),"square":(700,700)}
    def build_layout(self, *, book:Book, page:Page, variant:str|None=None)->dict:
        text=page.final_text or page.generated_text or page.user_text or ""
        ids=[i.id for i in page.images]; width,height=self.PAGE_SIZES.get(book.page_size or 'A4',self.PAGE_SIZES['A4'])
        safe={"x":36,"y":36,"w":width-72,"h":height-72}; variant=variant or self._default_variant(len(ids),len(text.split()))
        return {"schema_version":2,"page":{"width":width,"height":height,"unit":"pt","safe_area":safe},"composition":"text_with_image" if ids else "text_only","variant":variant,"typography":{"body_size":11,"line_height":1.5},"elements":self._build(variant,safe,ids)}
    def _default_variant(self,c,w):
        return 'text_only_classic' if c==0 else ('one_image_top_text_bottom' if c==1 and w<120 else 'one_image_left_text_right' if c==1 else 'two_image_grid_top_text_bottom' if c==2 else 'three_plus_gallery_with_text_block')
    def _img(self,n,i,b,fit='cover',role='illustration'): return {"id":f"image_{n}","type":"image","role":role,"image_id":i,"box":b,"z":10,"fit":fit}
    def _text(self,b): return {"id":"text_main","type":"text","role":"body","box":b,"z":20,"overflow":"continue","text_source":"generated_text"}
    def _build(self,v,s,ids):
        x,y,w,h=s['x'],s['y'],s['w'],s['h']; g=12
        if v=='text_only_classic' or (not ids and v!='text_dominant_with_image_aside'): return [self._text({"x":x,"y":y,"w":w,"h":h})]
        if v=='text_dominant_with_image_aside' and not ids: return [self._text({"x":x,"y":y,"w":w*0.84,"h":h})]
        if v=='one_image_top_text_bottom': return [self._img(1,ids[0],{"x":x,"y":y,"w":w,"h":h*0.42},'cover','hero'),self._text({"x":x,"y":y+h*0.42+g,"w":w,"h":h*0.58-g})]
        if v=='one_image_left_text_right':
            iw=w*0.38; return [self._img(1,ids[0],{"x":x,"y":y,"w":iw,"h":h},'contain'),self._text({"x":x+iw+g,"y":y,"w":w-iw-g,"h":h})]
        if v=='one_image_right_text_left':
            iw=w*0.38; return [self._text({"x":x,"y":y,"w":w-iw-g,"h":h}),self._img(1,ids[0],{"x":x+w-iw,"y":y,"w":iw,"h":h},'contain')]
        if v=='one_image_inline_pullout':
            ih=h*0.34; return [self._text({"x":x,"y":y,"w":w,"h":h-ih-g}),self._img(1,ids[0],{"x":x+w*0.52,"y":y+h-ih,"w":w*0.48,"h":ih},'cover','inline')]
        if v=='two_image_grid_top_text_bottom':
            iw=(w-g)/2; return [self._img(1,ids[0],{"x":x,"y":y,"w":iw,"h":h*0.34}),self._img(2,ids[min(1,len(ids)-1)],{"x":x+iw+g,"y":y,"w":iw,"h":h*0.34}),self._text({"x":x,"y":y+h*0.34+g,"w":w,"h":h*0.66-g})]
        if v=='two_image_stack_left_text_right':
            iw=w*0.34; ih=(h-g)/2; return [self._img(1,ids[0],{"x":x,"y":y,"w":iw,"h":ih}),self._img(2,ids[min(1,len(ids)-1)],{"x":x,"y":y+ih+g,"w":iw,"h":ih}),self._text({"x":x+iw+g,"y":y,"w":w-iw-g,"h":h})]
        if v=='image_dominant_caption_page':
            return [self._img(1,ids[0],{"x":x,"y":y,"w":w,"h":h*0.72},'cover','hero'),{"id":"caption_1","type":"caption","box":{"x":x,"y":y+h*0.72+g,"w":w,"h":h*0.28-g},"z":20,"text":""}]
        if v=='text_dominant_with_image_aside':
            iw=w*0.28; return [self._text({"x":x,"y":y,"w":w-iw-g,"h":h}),self._img(1,ids[0],{"x":x+w-iw,"y":y+h*0.2,"w":iw,"h":h*0.4},'contain','aside')]
        # three_plus_gallery_with_text_block
        out=[]; iw=(w-g)/2; ih=(h*0.45-g)/2
        for n,i in enumerate(ids[:3],start=1):
            cx=0 if n in (1,3) else 1; cy=0 if n<3 else 1
            out.append(self._img(n,i,{"x":x+cx*(iw+g),"y":y+cy*(ih+g),"w":iw,"h":ih}))
        out.append(self._text({"x":x,"y":y+h*0.48,"w":w,"h":h*0.52}))
        return out
    def estimate_target_words(self, *, book:Book, page:Page, composition:str|None=None)->tuple[int,str]: return (260 if page.images else 420,'deterministic template-based capacity estimate')
