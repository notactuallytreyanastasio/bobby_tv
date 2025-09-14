defmodule BobTv.Streaming.VideoManager do
  @moduledoc """
  Manages video downloads from Archive.org and local storage.
  Maintains exactly 2 videos (current + next) to minimize disk usage.
  """
  use GenServer
  require Logger
  alias BobTv.Catalog
  alias BobTv.Streaming.State

  @videos_dir "streaming_videos"
  @max_storage_gb 40
  @max_video_size_gb 10
  @videos_to_maintain 2

  # Client API

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @doc """
  Download the next video in the queue
  """
  def download_next_video do
    GenServer.cast(__MODULE__, :download_next)
  end

  @doc """
  Get a random video that hasn't been played recently
  """
  def get_next_video do
    GenServer.call(__MODULE__, :get_next_video)
  end

  @doc """
  Clean up old videos to maintain storage limits
  """
  def cleanup_videos do
    GenServer.cast(__MODULE__, :cleanup)
  end

  @doc """
  Get current storage usage
  """
  def get_storage_info do
    GenServer.call(__MODULE__, :storage_info)
  end

  # Server Callbacks

  @impl true
  def init(_) do
    # Ensure videos directory exists
    File.mkdir_p!(@videos_dir)

    state = %{
      downloading: false,
      current_download: nil,
      download_queue: []
    }

    Logger.info("Video manager initialized")

    # Schedule periodic cleanup
    Process.send_after(self(), :cleanup, :timer.minutes(5))

    {:ok, state}
  end

  @impl true
  def handle_cast(:download_next, state) do
    if not state.downloading do
      case select_next_video() do
        {:ok, media} ->
          Logger.info("Starting download for: #{media.title}")
          Task.start(fn -> download_video(media) end)
          {:noreply, %{state | downloading: true, current_download: media}}

        {:error, reason} ->
          Logger.warn("Could not select next video: #{reason}")
          {:noreply, state}
      end
    else
      Logger.debug("Download already in progress")
      {:noreply, state}
    end
  end

  @impl true
  def handle_cast(:cleanup, state) do
    Task.start(fn -> cleanup_old_videos() end)
    {:noreply, state}
  end

  @impl true
  def handle_call(:get_next_video, _from, state) do
    video = select_next_video()
    {:reply, video, state}
  end

  @impl true
  def handle_call(:storage_info, _from, state) do
    info = calculate_storage_info()
    {:reply, info, state}
  end

  @impl true
  def handle_info({:download_complete, media, path}, state) do
    Logger.info("Download complete: #{media.title} -> #{path}")

    # Update state
    State.update(:downloaded_videos, fn videos ->
      [%{id: media.id, path: path, title: media.title} | videos]
      |> Enum.take(@videos_to_maintain)
    end)

    {:noreply, %{state | downloading: false, current_download: nil}}
  end

  @impl true
  def handle_info({:download_failed, media, reason}, state) do
    Logger.error("Download failed for #{media.title}: #{inspect(reason)}")
    {:noreply, %{state | downloading: false, current_download: nil}}
  end

  @impl true
  def handle_info(:cleanup, state) do
    cleanup_old_videos()
    # Schedule next cleanup
    Process.send_after(self(), :cleanup, :timer.minutes(5))
    {:noreply, state}
  end

  # Private functions

  defp select_next_video do
    recently_played = State.get_recently_played(100)

    # Query for videos not recently played
    videos = Catalog.list_media(%{
      "sort" => "random",
      "page" => 1
    })

    # Filter out recently played
    available = Enum.reject(videos, fn video ->
      video.id in recently_played
    end)

    case available do
      [video | _] -> {:ok, video}
      [] ->
        # If all videos have been played, just get a random one
        case videos do
          [video | _] -> {:ok, video}
          [] -> {:error, :no_videos_available}
        end
    end
  end

  defp download_video(media) do
    # Build download URL from Archive.org
    download_url = build_download_url(media)
    output_path = Path.join(@videos_dir, "video_#{media.id}.mp4")

    Logger.info("Downloading from: #{download_url}")

    case download_file(download_url, output_path) do
      :ok ->
        send(self(), {:download_complete, media, output_path})
      {:error, reason} ->
        send(self(), {:download_failed, media, reason})
    end
  end

  defp build_download_url(media) do
    # Archive.org download URL pattern
    # First, try to get the video file directly
    base_url = "https://archive.org/download/#{media.identifier}"

    # Try common video formats
    # In production, you'd want to query the Archive.org API for actual files
    "#{base_url}/#{media.identifier}.mp4"
  end

  defp download_file(url, output_path) do
    # Use Req to download the file
    case Req.get(url, decode_body: false, into: File.stream!(output_path)) do
      {:ok, %{status: 200}} ->
        Logger.info("Downloaded successfully to #{output_path}")
        :ok

      {:ok, %{status: status}} ->
        Logger.error("Download failed with status #{status}")
        File.rm(output_path)
        {:error, {:http_status, status}}

      {:error, reason} ->
        Logger.error("Download error: #{inspect(reason)}")
        File.rm(output_path)
        {:error, reason}
    end
  rescue
    e ->
      Logger.error("Download exception: #{inspect(e)}")
      {:error, e}
  end

  defp cleanup_old_videos do
    # Get list of downloaded videos from state
    {:ok, downloaded} = State.get(:downloaded_videos)

    # Get all video files in directory
    all_files = File.ls!(@videos_dir)
    |> Enum.filter(&String.ends_with?(&1, ".mp4"))
    |> Enum.map(&Path.join(@videos_dir, &1))

    # Keep only the videos we're supposed to maintain
    keep_paths = downloaded
    |> Enum.take(@videos_to_maintain)
    |> Enum.map(& &1.path)
    |> MapSet.new()

    # Delete files not in our keep list
    Enum.each(all_files, fn file ->
      if not MapSet.member?(keep_paths, file) do
        Logger.info("Cleaning up old video: #{file}")
        File.rm(file)
      end
    end)

    # Check storage limits
    check_storage_limits()
  end

  defp check_storage_limits do
    info = calculate_storage_info()

    if info.total_gb > @max_storage_gb do
      Logger.warn("Storage limit exceeded: #{info.total_gb}GB / #{@max_storage_gb}GB")
      # Remove oldest videos until under limit
      cleanup_to_limit()
    end
  end

  defp cleanup_to_limit do
    files = File.ls!(@videos_dir)
    |> Enum.filter(&String.ends_with?(&1, ".mp4"))
    |> Enum.map(fn file ->
      path = Path.join(@videos_dir, file)
      stat = File.stat!(path)
      {path, stat.size, stat.mtime}
    end)
    |> Enum.sort_by(fn {_path, _size, mtime} -> mtime end)

    total_size = Enum.reduce(files, 0, fn {_path, size, _mtime}, acc -> acc + size end)
    total_gb = total_size / (1024 * 1024 * 1024)

    if total_gb > @max_storage_gb do
      # Remove oldest file
      case files do
        [{path, _size, _mtime} | _rest] ->
          Logger.info("Removing oldest video to free space: #{path}")
          File.rm(path)
          cleanup_to_limit()
        [] ->
          :ok
      end
    end
  end

  defp calculate_storage_info do
    files = File.ls!(@videos_dir)
    |> Enum.filter(&String.ends_with?(&1, ".mp4"))
    |> Enum.map(fn file ->
      path = Path.join(@videos_dir, file)
      %{path: path, size: File.stat!(path).size}
    end)

    total_size = Enum.reduce(files, 0, fn %{size: size}, acc -> acc + size end)

    %{
      total_bytes: total_size,
      total_gb: total_size / (1024 * 1024 * 1024),
      file_count: length(files),
      max_gb: @max_storage_gb,
      files: files
    }
  end
end