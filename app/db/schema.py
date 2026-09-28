"""DDL-операторы: таблицы, индексы, триггеры.
"""

DDL_STATEMENTS: tuple[str, ...] = (
    # ------------------------- tables -------------------------
    """
    CREATE TABLE IF NOT EXISTS log_entries (
        id           BIGSERIAL    PRIMARY KEY,
        application  VARCHAR(255) NOT NULL,
        event_time   TIMESTAMPTZ  NOT NULL,
        message      TEXT         NOT NULL,
        received_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_log_entries_app_time
        ON log_entries (application, event_time DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_log_entries_time
        ON log_entries (event_time)
    """,
    """
    CREATE TABLE IF NOT EXISTS application_counters (
        application   VARCHAR(255) PRIMARY KEY,
        entries_count BIGINT       NOT NULL DEFAULT 0
                      CHECK (entries_count >= 0),
        updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
    )
    """,

    # -------------------- INSERT trigger ----------------------
    """
    CREATE OR REPLACE FUNCTION trg_log_entries_ins() RETURNS trigger AS $$
    BEGIN
        INSERT INTO application_counters (application, entries_count, updated_at)
        SELECT application, COUNT(*), now()
        FROM new_table
        GROUP BY application
        ON CONFLICT (application) DO UPDATE
            SET entries_count = application_counters.entries_count + EXCLUDED.entries_count,
                updated_at    = now();
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql
    """,
    "DROP TRIGGER IF EXISTS trg_log_entries_ai ON log_entries",
    """
    CREATE TRIGGER trg_log_entries_ai
    AFTER INSERT ON log_entries
    REFERENCING NEW TABLE AS new_table
    FOR EACH STATEMENT
    EXECUTE FUNCTION trg_log_entries_ins()
    """,

    # -------------------- DELETE trigger ----------------------
    """
    CREATE OR REPLACE FUNCTION trg_log_entries_del() RETURNS trigger AS $$
    BEGIN
        UPDATE application_counters c
           SET entries_count = GREATEST(c.entries_count - d.cnt, 0),
               updated_at    = now()
          FROM (
              SELECT application, COUNT(*) AS cnt
              FROM old_table
              GROUP BY application
          ) d
         WHERE c.application = d.application;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql
    """,
    "DROP TRIGGER IF EXISTS trg_log_entries_ad ON log_entries",
    """
    CREATE TRIGGER trg_log_entries_ad
    AFTER DELETE ON log_entries
    REFERENCING OLD TABLE AS old_table
    FOR EACH STATEMENT
    EXECUTE FUNCTION trg_log_entries_del()
    """,

    # ------------------- TRUNCATE trigger ---------------------
    """
    CREATE OR REPLACE FUNCTION trg_log_entries_trunc() RETURNS trigger AS $$
    BEGIN
        TRUNCATE application_counters;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql
    """,
    "DROP TRIGGER IF EXISTS trg_log_entries_at ON log_entries",
    """
    CREATE TRIGGER trg_log_entries_at
    AFTER TRUNCATE ON log_entries
    FOR EACH STATEMENT
    EXECUTE FUNCTION trg_log_entries_trunc()
    """,
)