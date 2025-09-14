
def test_imports():
    import src.utils.io as io
    import src.core.features as features
    import src.backtest.engine as engine
    assert callable(features.atr)
    assert callable(engine.simulate)
