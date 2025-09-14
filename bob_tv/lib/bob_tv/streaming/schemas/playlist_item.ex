defmodule BobTv.Streaming.Schemas.PlaylistItem do
  @moduledoc """
  Schema for playlist items in the streaming queue.
  """
  use Ecto.Schema
  import Ecto.Changeset
  alias BobTv.Catalog.Media

  schema "playlist_items" do
    field :position, :integer
    field :title, :string
    field :creator, :string
    field :year, :integer
    field :scheduled_at, :utc_datetime
    field :played_at, :utc_datetime

    belongs_to :media, Media

    timestamps()
  end

  @doc false
  def changeset(playlist_item, attrs) do
    playlist_item
    |> cast(attrs, [:position, :media_id, :title, :creator, :year, :scheduled_at, :played_at])
    |> validate_required([:position])
  end
end