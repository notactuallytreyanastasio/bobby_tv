defmodule BobTv.Streaming.Schemas.DownloadedVideo do
  @moduledoc """
  Schema for tracking downloaded video files.
  """
  use Ecto.Schema
  import Ecto.Changeset
  alias BobTv.Catalog.Media

  schema "downloaded_videos" do
    field :identifier, :string
    field :title, :string
    field :file_path, :string
    field :file_size, :integer
    field :duration_seconds, :float
    field :downloaded_at, :utc_datetime
    field :last_played_at, :utc_datetime

    belongs_to :media, Media

    timestamps()
  end

  @doc false
  def changeset(downloaded_video, attrs) do
    downloaded_video
    |> cast(attrs, [:media_id, :identifier, :title, :file_path, :file_size,
                    :duration_seconds, :downloaded_at, :last_played_at])
    |> validate_required([:file_path, :downloaded_at])
  end
end