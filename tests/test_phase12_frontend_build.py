import os
import pytest


def test_frontend_pages_and_components_exist():
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "frontend", "src")
    
    # 1. Landing Page (page.tsx)
    landing_page = os.path.join(frontend_dir, "app", "page.tsx")
    assert os.path.exists(landing_page)
    with open(landing_page, "r", encoding="utf-8") as f:
        content = f.read()
    assert "What This Platform Does" in content
    assert "/api/config-spec" in content

    # 2. Define Page (/define/page.tsx)
    define_page = os.path.join(frontend_dir, "app", "define", "page.tsx")
    assert os.path.exists(define_page)
    with open(define_page, "r", encoding="utf-8") as f:
        content = f.read()
    assert "/api/llm-status" in content
    assert "/api/parse-machine" in content
    assert "Local AI is reading your description..." in content

    # 3. Configure Page (/configure/page.tsx)
    configure_page = os.path.join(frontend_dir, "app", "configure", "page.tsx")
    assert os.path.exists(configure_page)
    with open(configure_page, "r", encoding="utf-8") as f:
        content = f.read()
    assert "/api/generate" in content
    assert "Proposed Generation Plan" in content

    # 4. Results Page (/results/[runId]/page.tsx)
    results_page = os.path.join(frontend_dir, "app", "results", "[runId]", "page.tsx")
    assert os.path.exists(results_page)
    with open(results_page, "r", encoding="utf-8") as f:
        content = f.read()
    assert "/api/runs/" in content
    assert "Predictive Analytics & Model Performance" in content
    assert "What-If" in content
