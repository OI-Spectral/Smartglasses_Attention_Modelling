import sqlite3
import json
from a_models import Event
from sqlalchemy import create_engine, String, ForeignKey, Float, select, func, desc, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

engine = create_engine("sqlite:///events.db")

class Base(DeclarativeBase):
    pass

class Brand_Table(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    events: Mapped[list["Event_Table"]] = relationship(back_populates = "brand")

class Event_Table(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[str] = mapped_column(index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    confidence: Mapped[float]
    dwell_time: Mapped[float]
    brand: Mapped["Brand_Table"] = relationship(back_populates = "events")

Base.metadata.create_all(engine)

def write_to_database(args):
    with Session(engine) as session:
        with open(args.events_file, "r") as f:
            events = json.load(f)

        session.execute(delete(Event_Table))

        brand_dict = {b.name: b for b in session.scalars(select(Brand_Table))}

        for event in events:
            name = event["brand"]
            brand = brand_dict.get(name)
            if brand is None:
                brand = Brand_Table(name = name)
                session.add(brand)
                brand_dict[name] = brand
            
            session.add(Event_Table(timestamp = event["timestamp"], brand = brand, confidence = event["confidence"], dwell_time = event["dwell_seconds"]))

        session.commit()

def load_database():
    with Session(engine) as session:
        events = session.scalars(select(Event_Table)).all()
        return [Event(e.timestamp, e.brand.name, e.confidence, e.dwell_time) for e in events]

def total_dwell_per_brand():
    with Session(engine) as session:
        stmt = select(
            Brand_Table.name, func.sum(Event_Table.dwell_time)
        ).join(Event_Table.brand).group_by(Brand_Table.name).order_by(func.sum(Event_Table.dwell_time).desc())
        results = session.execute(stmt).all()

        print("Total dwell time per brand:")
        for name, total in results:
            print(f"{name}: {total} seconds")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load events from a JSON file into events.db.")
    parser.add_argument("events_file", help="Path to the events JSON file.")
    args = parser.parse_args()

    write_to_database(args)
    load_database()
    total_dwell_per_brand()
