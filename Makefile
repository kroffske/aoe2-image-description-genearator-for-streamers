all: generate

install_deps:
	python -m venv .venv
	$(source .venv/bin/activate)
	python -m pip install -r requirements.txt
	
extract: install_deps
	python extract_data.py

check_config:
	if ! [ -e "config.yaml" ]; then cp config.example.yaml config.yaml; fi

generate: check_config extract
	python generate_images.py
