from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import agents.sell_agent as sell_agent
import agents.rebuy_agent as rebuy_agent
import agents.buy_agent as buy_agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run")
def run_all_agents(db: Session = Depends(get_db)):
    """Manually trigger all three agents."""
    snapshot = sell_agent.run(db)
    rebuy_agent.run(db, snapshot)
    buy_agent.run(db)
    return {"status": "ok", "tickers_checked": list(snapshot.keys())}
