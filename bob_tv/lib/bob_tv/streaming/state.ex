defmodule BobTv.Streaming.State do
  @moduledoc """
  Manages streaming state using database.
  Provides a consistent API for state management with persistence.
  """
  use GenServer
  require Logger
  import Ecto.Query, except: [update: 2]
  alias BobTv.Repo
  alias BobTv.Streaming.Schemas.{
    StreamingState,
    PlaylistItem,
    RecentlyPlayed,
    DownloadedVideo
  }

  # Client API

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  def get(key) when is_atom(key), do: get(Atom.to_string(key))
  def get(key) when is_binary(key) do
    case Repo.get(StreamingState, key) do
      nil -> {:error, :not_found}
      state -> {:ok, decode_value(state.value, state.value_type)}
    end
  end

  def put(key, value) when is_atom(key), do: put(Atom.to_string(key), value)
  def put(key, value) when is_binary(key) do
    GenServer.call(__MODULE__, {:put, key, value})
  end

  def update(key, fun) when is_atom(key), do: update(Atom.to_string(key), fun)
  def update(key, fun) when is_binary(key) do
    GenServer.call(__MODULE__, {:update, key, fun})
  end

  def get_playlist do
    PlaylistItem
    |> order_by([p], asc: p.position)
    |> where([p], is_nil(p.played_at))
    |> Repo.all()
  end

  def add_to_playlist(item) do
    GenServer.call(__MODULE__, {:add_to_playlist, item})
  end

  def remove_from_playlist(item_id) do
    GenServer.call(__MODULE__, {:remove_from_playlist, item_id})
  end

  def get_recently_played(limit \\ 100) do
    RecentlyPlayed
    |> order_by([r], desc: r.played_at)
    |> limit(^limit)
    |> select([r], r.media_id)
    |> Repo.all()
  end

  def add_to_recently_played(media_id, title \\ nil) do
    GenServer.call(__MODULE__, {:add_recently_played, media_id, title})
  end

  def get_downloaded_videos do
    DownloadedVideo
    |> order_by([d], desc: d.downloaded_at)
    |> Repo.all()
  end

  def add_downloaded_video(attrs) do
    GenServer.call(__MODULE__, {:add_downloaded_video, attrs})
  end

  # Server Callbacks

  @impl true
  def init(_) do
    Logger.info("Streaming state manager initialized with database backend")
    {:ok, %{}}
  end

  @impl true
  def handle_call({:put, key, value}, _from, state) do
    {encoded_value, value_type} = encode_value(value)

    result = case Repo.get(StreamingState, key) do
      nil ->
        %StreamingState{}
        |> StreamingState.changeset(%{
          key: key,
          value: encoded_value,
          value_type: value_type
        })
        |> Repo.insert()

      existing ->
        existing
        |> StreamingState.changeset(%{
          value: encoded_value,
          value_type: value_type
        })
        |> Repo.update()
    end

    case result do
      {:ok, _} -> {:reply, :ok, state}
      {:error, changeset} -> {:reply, {:error, changeset}, state}
    end
  end

  @impl true
  def handle_call({:update, key, fun}, _from, state) do
    case get(key) do
      {:ok, current_value} ->
        new_value = fun.(current_value)
        {encoded_value, value_type} = encode_value(new_value)

        case Repo.get(StreamingState, key) do
          nil -> {:reply, {:error, :not_found}, state}
          existing ->
            case existing
            |> StreamingState.changeset(%{
              value: encoded_value,
              value_type: value_type
            })
            |> Repo.update() do
              {:ok, _} -> {:reply, {:ok, new_value}, state}
              {:error, changeset} -> {:reply, {:error, changeset}, state}
            end
        end

      {:error, _} ->
        {:reply, {:error, :not_found}, state}
    end
  end

  @impl true
  def handle_call({:add_to_playlist, item}, _from, state) do
    # Get next position
    max_position = Repo.one(
      from p in PlaylistItem,
      select: max(p.position)
    ) || 0

    attrs = Map.merge(item, %{position: max_position + 1})

    case %PlaylistItem{}
    |> PlaylistItem.changeset(attrs)
    |> Repo.insert() do
      {:ok, _} -> {:reply, :ok, state}
      {:error, changeset} -> {:reply, {:error, changeset}, state}
    end
  end

  @impl true
  def handle_call({:remove_from_playlist, item_id}, _from, state) do
    case Repo.get(PlaylistItem, item_id) do
      nil -> {:reply, {:error, :not_found}, state}
      item ->
        case Repo.delete(item) do
          {:ok, _} -> {:reply, :ok, state}
          {:error, changeset} -> {:reply, {:error, changeset}, state}
        end
    end
  end

  @impl true
  def handle_call({:add_recently_played, media_id, title}, _from, state) do
    attrs = %{
      media_id: media_id,
      title: title,
      played_at: DateTime.utc_now()
    }

    case %RecentlyPlayed{}
    |> RecentlyPlayed.changeset(attrs)
    |> Repo.insert() do
      {:ok, _} ->
        # Clean up old entries (keep last 100)
        cleanup_old_recently_played()
        {:reply, :ok, state}
      {:error, changeset} ->
        {:reply, {:error, changeset}, state}
    end
  end

  @impl true
  def handle_call({:add_downloaded_video, attrs}, _from, state) do
    attrs = Map.put_new(attrs, :downloaded_at, DateTime.utc_now())

    case %DownloadedVideo{}
    |> DownloadedVideo.changeset(attrs)
    |> Repo.insert(on_conflict: :replace_all, conflict_target: :media_id) do
      {:ok, _} -> {:reply, :ok, state}
      {:error, changeset} -> {:reply, {:error, changeset}, state}
    end
  end

  # Private functions

  defp encode_value(value) when is_binary(value), do: {value, "string"}
  defp encode_value(value) when is_integer(value), do: {to_string(value), "integer"}
  defp encode_value(value) when is_float(value), do: {to_string(value), "float"}
  defp encode_value(value) when is_atom(value), do: {Atom.to_string(value), "atom"}
  defp encode_value(%DateTime{} = value), do: {DateTime.to_iso8601(value), "datetime"}
  defp encode_value(value) when is_list(value) or is_map(value) do
    {Jason.encode!(value), "json"}
  end
  defp encode_value(nil), do: {nil, "nil"}
  defp encode_value(value), do: {inspect(value), "term"}

  defp decode_value(nil, _), do: nil
  defp decode_value(value, "string"), do: value
  defp decode_value(value, "integer"), do: String.to_integer(value)
  defp decode_value(value, "float"), do: String.to_float(value)
  defp decode_value(value, "atom"), do: String.to_atom(value)
  defp decode_value(value, "datetime"), do: DateTime.from_iso8601(value) |> elem(1)
  defp decode_value(value, "json"), do: Jason.decode!(value)
  defp decode_value(_, "nil"), do: nil
  defp decode_value(value, _), do: value

  defp cleanup_old_recently_played do
    # Keep only the last 100 entries
    ids_to_keep = RecentlyPlayed
    |> order_by([r], desc: r.played_at)
    |> limit(100)
    |> select([r], r.id)
    |> Repo.all()

    from(r in RecentlyPlayed, where: r.id not in ^ids_to_keep)
    |> Repo.delete_all()
  end
end