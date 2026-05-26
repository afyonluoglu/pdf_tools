# Geriye dönük uyumluluk shim'i
# Bu dosya artik yalnizca eski importlari yonlendirmek icin mevcuttur.
# Yeni kodda dogrudan su modulleri kullanin:
#   from pdf_view_ann_core import AnnotationManager
#   from pdf_view_ann_highlight import HighlightTool

from pdf_view_ann_core import AnnotationManager
from pdf_view_ann_highlight import HighlightTool

# Eski isimlerle uyumluluk takma adlari
FixedAnnotationManager = AnnotationManager
FixedHighlightTool = HighlightTool
