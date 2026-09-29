.PHONY: all data build eval verify test serve live
all: build eval verify test
data:   ; python generator/generate.py
build:  ; python -m pipeline.build
eval:   ; python -m pipeline.eval
verify: ; python -m pipeline.verify_preread
test:   ; python -m pytest -q
serve:  ; python -m http.server 8000 -d docs
live:   ; python -m pipeline.build --backend claude && $(MAKE) eval verify
