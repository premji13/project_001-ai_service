from sqlalchemy import create_engine, inspect, text

import app.database as database


def test_init_db_adds_email_owner_to_existing_documents(monkeypatch):
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE documents ("
                "id INTEGER PRIMARY KEY, user_id INTEGER)"
            )
        )
        connection.execute(
            text("INSERT INTO documents (id, user_id) VALUES (1, 42)")
        )

    monkeypatch.setattr(database, "engine", engine)
    try:
        database.init_db()

        with engine.connect() as connection:
            columns = {
                column["name"]
                for column in inspect(connection).get_columns("documents")
            }
            document = connection.execute(
                text("SELECT user_id, user_email FROM documents WHERE id = 1")
            ).one()

        assert "user_email" in columns
        assert document.user_id == 42
        assert document.user_email is None
    finally:
        engine.dispose()
