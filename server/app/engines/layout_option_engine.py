from __future__ import annotations
from dataclasses import dataclass
from fastapi import HTTPException
from app.engines.layout_engine import LayoutEngine
from app.engines.layout_validator import LayoutValidator
from app.models.entities import Book, Page

@dataclass
class LayoutOptionInput:
    book: Book
    page: Page
    text: str
    image_count: int
    page_capacity_hint: dict | None = None
    instructions: str | None = None

class LayoutOptionEngine:
    def __init__(self) -> None:
        self.layout_engine=LayoutEngine(); self.validator=LayoutValidator()
    async def generate_options(self,payload:LayoutOptionInput)->list[dict]:
        candidates=self._variants(payload.image_count)
        valid=[]; errors=[]
        for v in candidates:
            layout=self.layout_engine.build_layout(book=payload.book,page=payload.page,variant=v)
            res=self.validator.validate_layout(layout,page=payload.page,text=payload.text)
            if res.valid:
                layout['validation']=res.to_dict(); valid.append((v,layout,res))
            else:
                errors.append({"variant":v,"errors":res.errors})
            if len(valid)==2: break
        if len(valid)<2:
            raise HTTPException(status_code=400, detail={"message":"Could not generate two valid layout options","errors":errors})
        out=[]
        for idx,(v,layout,res) in enumerate(valid,start=1):
            out.append({"option_index":idx,"label":"Option A" if idx==1 else "Option B","layout_json":layout,"preview_metadata":{"variant":v,"validation":res.to_dict()},"rationale":f"{v} keeps text and images non-overlapping."})
        return out
    def _variants(self,c:int)->list[str]:
        if c<=0: return ['text_only_classic','text_dominant_with_image_aside']
        if c==1: return ['one_image_top_text_bottom','one_image_right_text_left','text_dominant_with_image_aside','one_image_left_text_right','one_image_inline_pullout']
        if c==2: return ['two_image_grid_top_text_bottom','two_image_stack_left_text_right','text_dominant_with_image_aside']
        return ['three_plus_gallery_with_text_block','image_dominant_caption_page','two_image_grid_top_text_bottom']
