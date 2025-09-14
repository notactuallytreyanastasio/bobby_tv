defmodule BobTv.Repo.Migrations.CreateStreamingState do
  use Ecto.Migration

  def change do
    # Create streaming_state table for key-value state storage
    create table(:streaming_state, primary_key: false) do
      add :key, :string, primary_key: true
      add :value, :text
      add :value_type, :string  # "string", "integer", "json", etc.

      timestamps()
    end

    # Create playlist_items table
    create table(:playlist_items) do
      add :position, :integer, null: false
      add :media_id, references(:media, on_delete: :delete_all)
      add :title, :string
      add :creator, :string
      add :year, :integer
      add :scheduled_at, :utc_datetime
      add :played_at, :utc_datetime

      timestamps()
    end

    create index(:playlist_items, [:position])
    create index(:playlist_items, [:scheduled_at])
    create index(:playlist_items, [:played_at])

    # Create recently_played table
    create table(:recently_played) do
      add :media_id, references(:media, on_delete: :delete_all)
      add :identifier, :string
      add :title, :string
      add :played_at, :utc_datetime, null: false

      timestamps()
    end

    create index(:recently_played, [:played_at])
    create index(:recently_played, [:media_id])

    # Create downloaded_videos table to track local files
    create table(:downloaded_videos) do
      add :media_id, references(:media, on_delete: :delete_all)
      add :identifier, :string
      add :title, :string
      add :file_path, :string, null: false
      add :file_size, :bigint
      add :duration_seconds, :float
      add :downloaded_at, :utc_datetime, null: false
      add :last_played_at, :utc_datetime

      timestamps()
    end

    create index(:downloaded_videos, [:downloaded_at])
    create index(:downloaded_videos, [:file_path])
    create unique_index(:downloaded_videos, [:media_id])

    # Initialize default streaming state values
    execute """
      INSERT INTO streaming_state (key, value, value_type, inserted_at, updated_at) VALUES
      ('streaming_status', 'idle', 'string', datetime('now'), datetime('now')),
      ('current_video_id', NULL, 'integer', datetime('now'), datetime('now')),
      ('next_video_id', NULL, 'integer', datetime('now'), datetime('now')),
      ('playback_start_time', NULL, 'datetime', datetime('now'), datetime('now')),
      ('total_videos_played', '0', 'integer', datetime('now'), datetime('now')),
      ('stream_start_time', NULL, 'datetime', datetime('now'), datetime('now'))
    """, ""
  end
end