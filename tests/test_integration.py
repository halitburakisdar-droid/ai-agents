"""
Integration Tests — Level 2 otomatik test çalıştırır
"""

import sys
sys.path.insert(0, "/Users/burak/ai-agents")


def test_price_monitor():
    from agents.price_monitor import PriceMonitorAgent
    result = PriceMonitorAgent().run()
    assert "prices" in result
    assert "gold" in result["prices"]
    assert result["prices"]["gold"] > 0


def test_market_data():
    from agents.instagram.market_data import MarketDataAgent
    result = MarketDataAgent().run()
    assert "data" in result
    assert "ALTIN" in result["data"]


def test_learning_db():
    from memory.learning_db import init_learning_tables, save_level1_report, get_level1_reports
    init_learning_tables()
    rid = save_level1_report(cycle_num=9999, avg_score=7.5,
                             engagement="yüksek", errors=[], issues=[])
    assert rid > 0
    reports = get_level1_reports(hours=1)
    assert any(r["cycle_num"] == 9999 for r in reports)


def test_skill_tree():
    from memory.learning_db import update_skill_score, init_learning_tables
    init_learning_tables()
    result = update_skill_score("Test Agent", "hook_writing", 7.5)
    assert "leveled_up" in result


if __name__ == "__main__":
    tests = [test_price_monitor, test_market_data, test_learning_db, test_skill_tree]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
    print(f"\n  {passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
