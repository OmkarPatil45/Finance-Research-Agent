
import argparse
import json

from sqlalchemy.orm import Session

from app.db.models import Base
from app.db.session import engine
from app.services.ingestion_service import ingest_snapshot


def main():
    parser = argparse.ArgumentParser(
        description="Load a finance research data snapshot into PostgreSQL."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to a snapshot directory containing the three JSON files",
    )
    args = parser.parse_args()

    # Create missing tables. Existing tables are not dropped.
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        result = ingest_snapshot(db, args.path)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
