# Shared targets for one slide deck. Each deck's Makefile is just `include ../deck.mk`.
#   make up       install deps and run the dev server on :3030
#   make export   export to <deck>.pdf in this folder (override with OUT=path)
DECK := $(shell basename "$(CURDIR)")
OUT  ?= $(DECK).pdf
PORT ?= 3030
.PHONY: up install export

up: install
	@pid=$$(lsof -tiTCP:$(PORT) -sTCP:LISTEN 2>/dev/null | head -1); \
	if [ -n "$$pid" ]; then \
	  dir=$$(lsof -a -p $$pid -d cwd -Fn 2>/dev/null | sed -n 's/^n//p'); \
	  echo "Port $(PORT) is already in use by pid $$pid ($$dir)"; \
	  echo "Stop it with: kill $$pid"; \
	  exit 1; \
	fi
	pnpm dev

install:
	pnpm install

# --per-slide renders one slide at a time so one slow slide cannot stall the whole print.
# --wait lets the slide transition finish before capture, else the previous slide bleeds through.
# `playwright install` is idempotent: it only downloads the browser build slidev needs if missing.
export: install
	pnpm exec playwright install chromium
	pnpm exec slidev export --output "$(OUT)" --per-slide --timeout 60000 --wait 800
	@echo "Exported to $(OUT)"
