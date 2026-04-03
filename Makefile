.PHONY: test lint typecheck install install-all clean

test:  ## Run all tests
	python -m pytest tests/ -q

test-quick:  ## Run tests (minimal output)
	python -m pytest tests/ -q --tb=no

test-verbose:  ## Run tests with verbose output
	python -m pytest tests/ -v

lint:  ## Run ruff linter
	ruff check src/ tests/

typecheck:  ## Run mypy type checking
	mypy --strict src/open_web_retrieval/

install:  ## Install in editable mode (base only)
	pip install -e .

install-extract:  ## Install with trafilatura for extraction
	pip install -e ".[extract]"

install-all:  ## Install with all optional deps
	pip install -e ".[all]"

clean:  ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

# >>> META-PROCESS WORKTREE TARGETS >>>
WORKTREE_CREATE_SCRIPT := scripts/meta/worktree-coordination/create_worktree.py
WORKTREE_REMOVE_SCRIPT := scripts/meta/worktree-coordination/safe_worktree_remove.py
WORKTREE_CLAIMS_SCRIPT := scripts/meta/worktree-coordination/check_claims.py
WORKTREE_DIR ?= $(shell python "$(WORKTREE_CREATE_SCRIPT)" --repo-root . --print-default-worktree-dir)
WORKTREE_START_POINT ?= HEAD

.PHONY: worktree worktree-list worktree-remove

worktree:  ## Create claimed worktree (BRANCH=name TASK="..." [PLAN=N])
ifndef BRANCH
	$(error BRANCH is required. Usage: make worktree BRANCH=plan-42-feature TASK="Describe the task")
endif
ifndef TASK
	$(error TASK is required. Usage: make worktree BRANCH=plan-42-feature TASK="Describe the task")
endif
	@if [ ! -f "$(WORKTREE_CREATE_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CREATE_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree."; \
		exit 1; \
	fi
	@if [ ! -f "$(WORKTREE_CLAIMS_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CLAIMS_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree."; \
		exit 1; \
	fi
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --claim --id "$(BRANCH)" --task "$(TASK)" $(if $(PLAN),--plan $(PLAN),)
	@mkdir -p "$(WORKTREE_DIR)"
	@if ! python "$(WORKTREE_CREATE_SCRIPT)" --repo-root . --path "$(WORKTREE_DIR)/$(BRANCH)" --branch "$(BRANCH)" --start-point "$(WORKTREE_START_POINT)"; then \
		python "$(WORKTREE_CLAIMS_SCRIPT)" --release --id "$(BRANCH)" --force >/dev/null 2>&1 || true; \
		exit 1; \
	fi
	@echo ""
	@echo "Worktree created at $(WORKTREE_DIR)/$(BRANCH)"
	@echo "Claim created for branch $(BRANCH)"

worktree-list:  ## Show claimed worktree coordination status
	@if [ ! -f "$(WORKTREE_CLAIMS_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CLAIMS_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree-list."; \
		exit 1; \
	fi
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --list

worktree-remove:  ## Safely remove worktree for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make worktree-remove BRANCH=plan-42-feature)
endif
	@if [ ! -f "$(WORKTREE_REMOVE_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_REMOVE_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree-remove."; \
		exit 1; \
	fi
	@python "$(WORKTREE_REMOVE_SCRIPT)" "$(WORKTREE_DIR)/$(BRANCH)"
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --release --id "$(BRANCH)" --force >/dev/null 2>&1 || true
# <<< META-PROCESS WORKTREE TARGETS <<<
