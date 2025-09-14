defmodule BobTv.Catalog.Media do
  use Ecto.Schema
  import Ecto.Changeset

  schema "media" do
    field :title, :string
    field :description, :string
    field :creator, :string
    field :date, :string
    field :year, :integer
    field :mediatype, :string
    field :collection, :string
    field :downloads, :integer
    field :item_size, :integer
    field :item_url, :string
    field :thumbnail_url, :string
  end

  @doc false
  def changeset(media, attrs) do
    media
    |> cast(attrs, [:title, :description, :creator, :date, :year,
                    :mediatype, :collection, :downloads, :item_size, :item_url,
                    :thumbnail_url])
    |> validate_required([:title])
  end
end