UV ?= uv

all: generate

install_deps:
	$(UV) sync

extract: install_deps
	$(UV) run aoe2civgen extract

extract_en: install_deps
	$(UV) run aoe2civgen extract --locale en

check_config: install_deps
	$(UV) run aoe2civgen init-config

generate: check_config extract
	$(UV) run aoe2civgen generate

generate_en: check_config extract_en
	$(UV) run aoe2civgen generate --locale en
