from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Game


def reset_ranking(session: Session) -> int:
    """Borra todas las partidas completadas, dejando el marcador a cero."""
    deleted = (
        session.query(Game)
        .filter(Game.status == "completed")
        .delete(synchronize_session=False)
    )
    session.commit()
    return deleted


def prune_ranking(session: Session, keep: int = 10) -> int:
    """Borra las partidas completadas que no están entre las `keep` mejores."""
    top_ids = [
        row[0]
        for row in session.query(Game.id)
        .filter(Game.status == "completed")
        .order_by(Game.score.desc(), Game.finished_at.asc(), Game.id.asc())
        .limit(keep)
        .all()
    ]
    if not top_ids:
        return 0
    deleted = (
        session.query(Game)
        .filter(Game.status == "completed", Game.id.notin_(top_ids))
        .delete(synchronize_session=False)
    )
    session.commit()
    return deleted
