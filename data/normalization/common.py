"""Get-or-create helpers for reference entities.

Provider payloads identify teams/players/venues/competitions by name (or an
external id); normalization is responsible for mapping those onto stable
internal primary keys, creating the row the first time a name is seen.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.core import Competition, Player, Team, Venue
from database.models.enums import Sport


def get_or_create_team(session: Session, sport: Sport, name: str) -> Team:
    team = session.scalar(select(Team).where(Team.sport == sport, Team.name == name))
    if team is None:
        team = Team(sport=sport, name=name)
        session.add(team)
        session.flush()
    return team


def get_or_create_player(session: Session, sport: Sport, name: str) -> Player:
    player = session.scalar(select(Player).where(Player.sport == sport, Player.full_name == name))
    if player is None:
        player = Player(sport=sport, full_name=name)
        session.add(player)
        session.flush()
    return player


def get_or_create_venue(session: Session, name: str) -> Venue:
    venue = session.scalar(select(Venue).where(Venue.name == name))
    if venue is None:
        venue = Venue(name=name)
        session.add(venue)
        session.flush()
    return venue


def get_or_create_competition(session: Session, sport: Sport, name: str) -> Competition:
    competition = session.scalar(select(Competition).where(Competition.sport == sport, Competition.name == name))
    if competition is None:
        competition = Competition(sport=sport, name=name)
        session.add(competition)
        session.flush()
    return competition
