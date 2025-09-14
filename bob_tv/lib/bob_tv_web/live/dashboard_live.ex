defmodule BobTvWeb.DashboardLive do
  @moduledoc """
  LiveView dashboard for monitoring the streaming system.
  Shows real-time status of all streaming components.
  """
  use BobTvWeb, :live_view
  alias BobTv.Streaming.{StreamCoordinator, VideoManager, OverlayGenerator, State}
  alias BobTv.Catalog

  @refresh_interval :timer.seconds(1)

  @impl true
  def mount(_params, _session, socket) do
    if connected?(socket) do
      # Subscribe to updates
      :timer.send_interval(@refresh_interval, self(), :refresh)
    end

    socket = socket
    |> assign(:page_title, "Streaming Dashboard")
    |> load_status()

    {:ok, socket}
  end

  @impl true
  def handle_info(:refresh, socket) do
    {:noreply, load_status(socket)}
  end

  @impl true
  def handle_event("start_streaming", _params, socket) do
    case StreamCoordinator.start_streaming() do
      :ok ->
        socket = socket
        |> put_flash(:info, "Streaming started")
        |> load_status()
        {:noreply, socket}
      {:error, reason} ->
        socket = put_flash(socket, :error, "Failed to start: #{inspect(reason)}")
        {:noreply, socket}
    end
  end

  @impl true
  def handle_event("stop_streaming", _params, socket) do
    StreamCoordinator.stop_streaming()
    socket = socket
    |> put_flash(:info, "Streaming stopped")
    |> load_status()
    {:noreply, socket}
  end

  @impl true
  def handle_event("swap_videos", _params, socket) do
    StreamCoordinator.swap_videos()
    socket = socket
    |> put_flash(:info, "Video swap triggered")
    |> load_status()
    {:noreply, socket}
  end

  @impl true
  def handle_event("download_next", _params, socket) do
    VideoManager.download_next_video()
    socket = put_flash(socket, :info, "Download started")
    {:noreply, socket}
  end

  @impl true
  def handle_event("cleanup_videos", _params, socket) do
    VideoManager.cleanup_videos()
    socket = put_flash(socket, :info, "Cleanup initiated")
    {:noreply, socket}
  end

  @impl true
  def handle_event("update_overlays", _params, socket) do
    OverlayGenerator.update_overlays()
    socket = put_flash(socket, :info, "Overlays updated")
    {:noreply, socket}
  end

  defp load_status(socket) do
    # Get streaming coordinator status
    coordinator_status = StreamCoordinator.get_status()
    
    # Get storage info
    storage_info = VideoManager.get_storage_info()
    
    # Get overlay status
    overlay_status = OverlayGenerator.get_status()
    
    # Get state info
    total_played = case State.get(:total_videos_played) do
      {:ok, count} -> count
      _ -> 0
    end
    
    recently_played = State.get_recently_played(10)
    
    # Get playlist
    playlist = State.get_playlist()
    
    # Calculate uptime
    uptime = calculate_uptime(coordinator_status)
    
    socket
    |> assign(:coordinator_status, coordinator_status)
    |> assign(:storage_info, storage_info)
    |> assign(:overlay_status, overlay_status)
    |> assign(:total_played, total_played)
    |> assign(:recently_played, recently_played)
    |> assign(:playlist, playlist)
    |> assign(:uptime, uptime)
    |> assign(:streaming, coordinator_status[:streaming] || false)
  end

  defp calculate_uptime(%{streaming: true, playback_start: start} = status) when not is_nil(start) do
    seconds = System.monotonic_time(:second) - start
    format_duration(seconds)
  end
  defp calculate_uptime(_), do: "--:--:--"

  defp format_duration(seconds) when seconds < 0, do: "00:00:00"
  defp format_duration(seconds) do
    hours = div(seconds, 3600)
    minutes = div(rem(seconds, 3600), 60)
    secs = rem(seconds, 60)
    :io_lib.format("~2..0B:~2..0B:~2..0B", [hours, minutes, secs])
    |> IO.iodata_to_binary()
  end

  defp format_gb(bytes) when is_number(bytes) do
    gb = bytes / (1024 * 1024 * 1024)
    :io_lib.format("~.2f GB", [gb])
    |> IO.iodata_to_binary()
  end
  defp format_gb(_), do: "0.00 GB"

  defp format_percentage(nil), do: "0%"
  defp format_percentage(percent) when is_number(percent) do
    "#{round(percent)}%"
  end
  defp format_percentage(_), do: "0%"

  defp truncate(nil, _), do: "Unknown"
  defp truncate(text, max_length) when is_binary(text) do
    if String.length(text) > max_length do
      String.slice(text, 0, max_length - 3) <> "..."
    else
      text
    end
  end
  defp truncate(text, max_length), do: truncate(to_string(text), max_length)
end