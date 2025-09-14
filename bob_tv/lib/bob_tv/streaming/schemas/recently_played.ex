defmodule BobTv.Streaming.Schemas.RecentlyPlayed do
  @moduledoc """
  Schema for tracking recently played videos.
  """
  use Ecto.Schema
  import Ecto.Changeset
  alias BobTv.Catalog.Media

  schema "recently_played" do
    field :identifier, :string
    field :title, :string
    field :played_at, :utc_datetime

    belongs_to :media, Media

    timestamps()
  end

  @doc false
  def changeset(recently_played, attrs) do
    recently_played
    |> cast(attrs, [:media_id, :identifier, :title, :played_at])
    |> validate_required([:played_at])
  end
end