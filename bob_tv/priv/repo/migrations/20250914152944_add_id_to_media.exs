defmodule BobTv.Repo.Migrations.AddIdToMedia do
  use Ecto.Migration

  def change do
    # SQLite doesn't support ALTER TABLE to add PRIMARY KEY
    # So we need to recreate the table with proper structure
    execute(
      "CREATE TABLE media_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT UNIQUE NOT NULL,
        title TEXT,
        description TEXT,
        creator TEXT,
        date TEXT,
        year INTEGER,
        mediatype TEXT,
        collection TEXT,
        downloads INTEGER,
        item_size INTEGER,
        item_url TEXT,
        thumbnail_url TEXT,
        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )",
      "DROP TABLE media_new"
    )

    # Copy existing data
    execute(
      "INSERT INTO media_new (identifier, title, description, creator, date, year, mediatype, collection, downloads, item_size, item_url, thumbnail_url, crawled_at)
       SELECT identifier, title, description, creator, date, year, mediatype, collection, downloads, item_size, item_url, thumbnail_url, crawled_at
       FROM media",
      ""
    )

    # Replace old table with new one
    execute("DROP TABLE media", "")
    execute("ALTER TABLE media_new RENAME TO media", "")

    # Recreate indexes
    create_if_not_exists index(:media, [:identifier], unique: true)
    create_if_not_exists index(:media, [:mediatype])
    create_if_not_exists index(:media, [:year])
    create_if_not_exists index(:media, [:downloads])
    create_if_not_exists index(:media, [:creator])
  end
end