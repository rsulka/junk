.PHONY: install install-dev test test-cov lint format typecheck clean \
        e2e-build e2e-start e2e-stop e2e-clean e2e-status e2e-test e2e-ssh

# ============================================================================
# Instalacja
# ============================================================================

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# ============================================================================
# Testy i jakość kodu
# ============================================================================

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=dsmonitor --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

# ============================================================================
# Kontenery E2E
# ============================================================================

E2E_DIR := tests/e2e
E2E_IMAGE := dsmonitor-test:latest
E2E_CONTAINER1 := dsmonitor-test1
E2E_CONTAINER2 := dsmonitor-test2
E2E_PORT1 := 2221
E2E_PORT2 := 2222
E2E_KEY := $(E2E_DIR)/id_rsa

$(E2E_KEY):
	ssh-keygen -t rsa -b 2048 -N "" -f $(E2E_KEY) -C "dsmonitor-test"

e2e-build: $(E2E_KEY)
	podman build -t $(E2E_IMAGE) $(E2E_DIR)

e2e-start:
	@if podman ps -a --format "{{.Names}}" | grep -q "^$(E2E_CONTAINER1)$$"; then \
		podman start $(E2E_CONTAINER1) 2>/dev/null || true; \
	else \
		podman run -d --name $(E2E_CONTAINER1) -p $(E2E_PORT1):22 $(E2E_IMAGE); \
	fi
	@if podman ps -a --format "{{.Names}}" | grep -q "^$(E2E_CONTAINER2)$$"; then \
		podman start $(E2E_CONTAINER2) 2>/dev/null || true; \
	else \
		podman run -d --name $(E2E_CONTAINER2) -p $(E2E_PORT2):22 $(E2E_IMAGE); \
	fi
	@echo "Kontenery uruchomione na portach $(E2E_PORT1) i $(E2E_PORT2)"

e2e-stop:
	podman stop $(E2E_CONTAINER1) $(E2E_CONTAINER2) 2>/dev/null || true
	@echo "Kontenery zatrzymane"

e2e-clean:
	podman rm -f $(E2E_CONTAINER1) $(E2E_CONTAINER2) 2>/dev/null || true
	@echo "Kontenery usunięte"

e2e-status:
	@echo "Status kontenerów E2E:"
	@podman ps -a --filter "name=dsmonitor-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

e2e-ssh:
	@echo "Test SSH do kontenera 1 (port $(E2E_PORT1)):"
	@ssh -i $(E2E_KEY) -o StrictHostKeyChecking=accept-new -p $(E2E_PORT1) testuser@localhost "echo 'SSH OK'" || true
	@echo ""
	@echo "Test SSH do kontenera 2 (port $(E2E_PORT2)):"
	@ssh -i $(E2E_KEY) -o StrictHostKeyChecking=accept-new -p $(E2E_PORT2) testuser@localhost "echo 'SSH OK'" || true

e2e-test: e2e-start
	@echo "Uruchamianie dsmonitor na kontenerach E2E..."
	dsmonitor --config $(E2E_DIR)/config_e2e.yaml

# ============================================================================
# Czyszczenie
# ============================================================================

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean e2e-clean
	rm -f $(E2E_KEY) $(E2E_KEY).pub

# ============================================================================
# Pomoc
# ============================================================================

help:
	@echo "Dostępne komendy:"
	@echo ""
	@echo "  Instalacja:"
	@echo "    make install      - Instalacja pakietu"
	@echo "    make install-dev  - Instalacja z zależnościami dev"
	@echo ""
	@echo "  Testy i jakość:"
	@echo "    make test         - Uruchomienie testów"
	@echo "    make test-cov     - Testy z coverage"
	@echo "    make lint         - Sprawdzenie ruff"
	@echo "    make format       - Formatowanie kodu"
	@echo "    make typecheck    - Sprawdzenie mypy"
	@echo ""
	@echo "  Kontenery E2E:"
	@echo "    make e2e-build    - Budowanie obrazu kontenera"
	@echo "    make e2e-start    - Uruchomienie kontenerów"
	@echo "    make e2e-stop     - Zatrzymanie kontenerów"
	@echo "    make e2e-clean    - Usunięcie kontenerów"
	@echo "    make e2e-status   - Status kontenerów"
	@echo "    make e2e-ssh      - Test połączenia SSH"
	@echo "    make e2e-test     - Uruchomienie dsmonitor na kontenerach"
	@echo ""
	@echo "  Czyszczenie:"
	@echo "    make clean        - Czyszczenie artefaktów build"
	@echo "    make clean-all    - Czyszczenie + usunięcie kontenerów i kluczy"
