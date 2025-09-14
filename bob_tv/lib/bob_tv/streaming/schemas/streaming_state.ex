defmodule BobTv.Streaming.Schemas.StreamingState do
  @moduledoc """
  Schema for key-value streaming state storage.
  Replaces ETS tables with persistent database storage.
  """
  use Ecto.Schema
  import Ecto.Changeset

  @primary_key {:key, :string, autogenerate: false}
  schema "streaming_state" do
    field :value, :string
    field :value_type, :string

    timestamps()
  end

  @doc false
  def changeset(state, attrs) do
    state
    |> cast(attrs, [:key, :value, :value_type])
    |> validate_required([:key, :value_type])
  end
end