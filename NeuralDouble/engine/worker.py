from core.event_bus import event_bus
from engine.strategy_engine import StrategyEngine

engine = StrategyEngine()

def start_worker():

    print("Worker ativo")

    while True:

        result = event_bus.get()

        engine.process(result)